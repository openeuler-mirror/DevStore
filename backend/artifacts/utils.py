#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# oeDeploy is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2025-07-30
# ======================================================================================================================

import os
import subprocess
import yaml
import operator
from functools import reduce
from django.db import connection
from django.db.models import Q, Case, When, Value, IntegerField,FloatField,F
from django.db.models.functions import Length
from tasks.models import Task
from artifacts.models import MCPServer
from artifacts.serializers import PluginItemSerializer
from constants.paths import PLUGIN_CACHE_DIR, LOG_DIR
from utils.common import is_process_running
from utils.cmd_executor import CommandExecutor
from utils.logger import init_log
logger = init_log('run.log')


# 权重配置
SEARCH_WEIGHTS = {
    'exact_match': 10.0,
    'phrase_match': 5.0,
    'name_field': 3.0,
    'position_bonus': 3.0,
    'length_factor': 2.0,
    'coverage': 1.5
}



def clear_table(table_name):
    """清空指定数据库表并重置自增主键"""
    logger.info(f"Start to clear table '{table_name}'")
    with connection.cursor() as cursor:
        cursor.execute(f"TRUNCATE TABLE {table_name}")


def set_plugin_action_status(action_list, action_name, status):
    """设置插件action状态"""
    for action in action_list:
        if action["name"] == action_name:
            action["status"] = status
            return


def update_plugin_action_list(plugin, action_list):
    """更新插件action列表"""
    try:
        update_data = {'action_list': action_list}
        serializer = PluginItemSerializer(plugin, data=update_data, partial=True)
        if serializer.is_valid():
            serializer.save()
        else:
            logger.error(f"Failed to update plugin [{plugin.name}] action_list: {serializer.errors}")
            return False
    except Exception as e:
        logger.error(f"Failed to update plugin [{plugin.name}] action_list: {str(e)}")
        return False
    return True


def get_plugin_action_list(plugin):
    """获取插件action列表"""
    target_project = os.path.join(PLUGIN_CACHE_DIR, plugin.key)
    main_file = os.path.join(target_project, "main.yaml")
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            main = yaml.safe_load(f)
        
        if not main or 'action' not in main:
            return []
        
        action_list = []
        for action_name, action_data in main['action'].items():
            status = Task.Status.NOT_YET
            if is_process_running(f"oedp run -p {target_project} -lt {action_name}", timeout=3600):
                status = Task.Status.IN_PROCESS
            action_info = {
                "name": action_name,
                "title": action_data.get('title', action_name),
                "description": action_data.get('description', ''),
                "status": status
            }
            action_list.append(action_info)
        
        return action_list
    except Exception as e:
        logger.error(f"Failed to parse main.yaml for plugin {plugin.name}: {str(e)}")
        return []


def update_plugin_status(plugin, status):
    """更新插件下载状态"""
    try:
        update_data = {'download_status': status}
        serializer = PluginItemSerializer(plugin, data=update_data, partial=True)
        if serializer.is_valid():
            serializer.save()
        else:
            logger.error(f"Failed to update plugin [{plugin.name}] status: {serializer.errors}")
            return False
    except Exception as e:
        logger.error(f"Failed to update plugin [{plugin.name}] status: {str(e)}")
        return False
    return True

def get_devstore_log():
    """获取 DevStore 日志
    
    如果日志文件超过100KB，则只返回最后100KB的内容
    """
    log_file = os.path.join(LOG_DIR, "run.log")
    if not os.path.exists(log_file):
        return ""
    
    try:
        max_size = 100 * 1024  # 定义100KB的大小限制
        file_size = os.path.getsize(log_file)
        with open(log_file, 'r', encoding='utf-8') as f:
            if file_size <= max_size:
                return f.read()
            else:
                # 文件大于100KB，读取最后100KB
                f.seek(file_size - max_size)
                content = f.read()
                # 由于可能从字符中间开始读取，找到第一个完整的行
                lines = content.split('\n')
                if len(lines) > 1:
                    # 去掉第一行（可能不完整），从第二行开始
                    return '\n'.join(lines[1:])
                else:
                    return content
                    
    except (OSError, IOError, UnicodeDecodeError) as e:
        logger.error(f"Failed to read log file {log_file}: {str(e)}")
        return f"读取日志文件时发生错误: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error while reading log file {log_file}: {str(e)}")
        return f"读取日志文件时发生未知错误: {str(e)}"

def check_system_rpm_installed(package_name: str) -> bool:
    """检查RPM包是否已在系统中安装"""
    try:
        cmd = ['rpm', '-q', package_name]
        cmd_executor = CommandExecutor(cmd, timeout=30)
        _, _, code = cmd_executor.run()
        if code == 0:
            return True
        else:
            return False
    except Exception:
        return False

def calculate_weighted_relevance(queryset, search_value, weights=None):
    """基于权重的相关性算法"""
    if not search_value:
        return queryset.annotate(relevance_score=Value(0.0, output_field=FloatField()))
    
    weights = weights or SEARCH_WEIGHTS
    search_terms = [term.strip() for term in search_value.lower().split() if term.strip()]
    full_search = search_value.lower().strip()
    
    annotations = {}
    annotations.update(_build_basic_factors(full_search))
    annotations.update(_build_position_factor(full_search, search_terms))
    annotations.update(_build_complex_factors(search_terms)) 
    annotations['relevance_score'] = _build_relevance_score(weights)
    
    return queryset.annotate(**annotations)

def _build_basic_factors(full_search):
    """构建基础匹配因子"""
    return {
        'exact_match_factor': Case(
            When(name__iexact=full_search, then=Value(1.0)),
            default=Value(0.0), output_field=FloatField()
        ),
        'phrase_match_factor': Case(
            When(name__icontains=full_search, then=Value(1.0)),
            When(description__icontains=full_search, then=Value(0.7)),
            default=Value(0.0), output_field=FloatField()
        ),
        'length_factor': Case(
            When(name__icontains=full_search, 
                 then=Value(1.0) / (Length('name') / len(full_search))),
            default=Value(0.0), output_field=FloatField()
        )
    }

def _build_position_factor(full_search, search_terms):
    """构建位置匹配因子 """
    position_kwargs = {
        f'name_startswith_{i}': Case(
            When(name__istartswith=term, then=Value(0.8 / (i + 1))),
            default=Value(0.0), output_field=FloatField()
        ) for i, term in enumerate(search_terms)
    }
    
    position_factor = Case(
        When(name__istartswith=full_search, then=Value(1.0)),
        When(name__icontains=full_search, then=Value(0.6)),
        **position_kwargs,
        default=Value(0.0), output_field=FloatField()
    )
    
    return {'position_factor': position_factor}

def _build_complex_factors(search_terms):
    """构建复杂匹配因子"""
    if not search_terms:
        return {
            'word_match_factor': Value(0.0, output_field=FloatField()),
            'coverage_factor': Value(0.0, output_field=FloatField())
        }
    
    # 构建单词匹配的Case列表
    word_cases = _build_word_cases(search_terms)

    total_score = sum(word_cases)
    max_possible_score = len(search_terms) * 1.0
    word_match_factor = total_score / max_possible_score if max_possible_score > 0 else Value(0.0)

    coverage_cases = _build_coverage_cases(search_terms)
    coverage_factor = sum(coverage_cases) / len(search_terms)
    
    return {
        'word_match_factor': word_match_factor,
        'coverage_factor': coverage_factor
    }

def _build_word_cases(search_terms):
    """构建单词匹配案例"""
    word_cases = []
    for term in search_terms:
        case = Case(
            When(name__icontains=term, then=Value(1.0)),
            When(description__icontains=term, then=Value(0.5)),
            default=Value(0.0), output_field=FloatField()
        )
        word_cases.append(case)
    return word_cases

def _build_coverage_cases(search_terms):
    """构建覆盖率案例"""
    coverage_cases = []
    for term in search_terms:
        case = Case(
            When(Q(name__icontains=term) | Q(description__icontains=term), 
                 then=Value(1.0)),
            default=Value(0.0), output_field=FloatField()
        )
        coverage_cases.append(case)
    return coverage_cases

def _build_relevance_score(weights):
    """构建最终相关性得分"""
    return (
        F('exact_match_factor') * weights['exact_match'] +
        F('phrase_match_factor') * weights['phrase_match'] +
        F('position_factor') * weights['position_bonus'] +  
        F('word_match_factor') * weights['name_field'] +
        F('coverage_factor') * weights['coverage'] +
        F('length_factor') * weights['length_factor']
    )

def process_search_with_relevance(queryset, search_value, sort='rec'):
    """处理多关键词搜索"""
    
    if search_value:
        # 构建搜索条件：任意词匹配名称或描述
        search_terms = [term.strip() for term in search_value.split() if term.strip()]
        conditions = []
        
        for term in search_terms:
            conditions.append(Q(name__icontains=term) | Q(description__icontains=term))
        
        # 使用OR连接所有条件
        if conditions:
            search_filter = reduce(operator.or_, conditions)
            queryset = queryset.filter(search_filter)
        
        # 计算相关性
        queryset = calculate_weighted_relevance(queryset, search_value)
    else:
        queryset = queryset.annotate(relevance_score=Value(0.0, output_field=FloatField()))
    
    # 排序
    if sort == 'new':
        return queryset.order_by('-relevance_score', '-updated_at') if search_value else queryset.order_by('-updated_at')
    else:
        return queryset.order_by('-relevance_score', 'name') if search_value else queryset.order_by('name')