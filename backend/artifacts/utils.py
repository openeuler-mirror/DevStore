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
from django.db import connection
from tasks.models import Task
from artifacts.models import MCPServer
from artifacts.serializers import PluginItemSerializer
from constants.paths import PLUGIN_CACHE_DIR, LOG_DIR
from utils.common import is_process_running
from utils.cmd_executor import CommandExecutor
from utils.logger import init_log
logger = init_log('run.log')


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

