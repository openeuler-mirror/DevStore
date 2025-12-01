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

import base64
import os
import shutil
import yaml

from pathlib import Path
from rest_framework import status

from artifacts.models import OEDPPlugin
from artifacts.serializers import PluginBulkCreateSerializer
from artifacts.tasks.plugin_action_task import PluginActionTask
from artifacts.tasks.plugin_download_task import PluginDownloadTask
from artifacts.utils import (
    clear_table,
    set_plugin_action_status,
    update_plugin_action_list,
    get_plugin_action_list,
    update_plugin_status
)
from constants.paths import PLUGIN_REPO_DIR, REPO_DETAILS_DIR, PLUGIN_CACHE_DIR
from tasks.models import Task
from tasks.scheduler import scheduler
from utils.cmd_executor import CommandExecutor
from utils.common import is_process_running
from utils.file_handler.base_handler import FileError
from utils.file_handler.yaml_handler import YAMLHandler
from utils.logger import init_log

logger = init_log('run.log')


class PluginMethods:

    @staticmethod
    def sync_plugins():
        """同步插件信息到数据库"""
        try:
            update_result, msg = PluginMethods._update_plugin_info()
            if not update_result:
                # 更新失败时清空数据库
                clear_table(OEDPPlugin._meta.db_table)
                return {'is_success': False, 'message': msg}
            
            plugin_data, msg = PluginMethods._read_plugin_info()
            if not plugin_data:
                # 读取失败时清空数据库
                clear_table(OEDPPlugin._meta.db_table)
                return {'is_success': False, 'message': msg}

            # 插件解析过程可能耗时，因此数据库清理在插件解析之后，避免出现较长空窗期
            clear_table(OEDPPlugin._meta.db_table)
            
            # 数据序列化并验证
            serializer = PluginBulkCreateSerializer(data=plugin_data, many=True)
            if not serializer.is_valid():
                logger.error(f"Failed to validate plugin data, errors: {serializer.errors}")
                return {'is_success': False, 'message': serializer.errors}
            
            # 写入新数据
            plugins = serializer.save()
            logger.info("Store plugin data to database successfully.")
            return {'is_success': True, 'message': "Sync plugin data successfully."}
            
        except Exception as e:
            logger.error(f"Sync plugins failed: {str(e)}")
            # 发生异常时清空数据库
            clear_table(OEDPPlugin._meta.db_table)
            return {'is_success': False, 'message': f'Sync failed: {str(e)}'}

    @staticmethod
    def download_plugin(key: str):
        """下载指定插件
        Args:
            key: 插件唯一标识符
        """
        logger.info("Start query plugin package information by key.")
        try:
            plugin = OEDPPlugin.objects.get(key=key)
        except OEDPPlugin.DoesNotExist:
            msg = f"The plugin with key [{key}] does not exist."
            logger.error(msg)
            return {'is_success': False, 'message': msg}
        logger.info("Query plugin package information successfully.")

        # 检查是否已经在下载中
        target_project = os.path.join(PLUGIN_CACHE_DIR, key)
        if is_process_running(f'oedp init {plugin.name} -p {target_project} -f', timeout=600):
            # 更新插件下载状态 in process
            if not update_plugin_status(plugin, Task.Status.IN_PROCESS):
                msg = f"Plugin [{key}] failed to update status [{Task.Status.IN_PROCESS}]."
                logger.error(msg)
                return {'is_success': False, 'message': msg}
            msg = f"Plugin [{key}] download already in process."
            logger.info(msg)
            return {'is_success': True, 'message': msg}
        
        # 检查本地插件是否已经存在
        logger.info(f"Start to check whether plugin [{key}] already exists.")
        if PluginMethods._check_plugin_file_exist(key):
            # 更新插件下载状态 success
            if not update_plugin_status(plugin, Task.Status.SUCCESS):
                msg = f"Plugin [{key}] failed to update status [{Task.Status.SUCCESS}]."
                logger.error(msg)
                return {'is_success': False, 'message': msg}

            # 更新action列表
            action_list = get_plugin_action_list(plugin)
            if not update_plugin_action_list(plugin, action_list):
                msg = f"Failed to update plugin [{key}] action_list"
                logger.error(msg)
                return {'is_success': False, 'message': msg}
            
            msg = f"Plugin [{key}] already exists."
            logger.info(msg)
            return {'is_success': True, 'message': msg}

        logger.info(f"Start to download plugin [{key}].")
        # 更新插件下载状态 in process
        if not update_plugin_status(plugin, Task.Status.IN_PROCESS):
            msg = f"Plugin [{key}] failed to update status [{Task.Status.IN_PROCESS}]."
            logger.error(msg)
            return {'is_success': False, 'message': msg}

        download_plugin_task = PluginDownloadTask(plugin, name=f"plugin_download_{key}_task")
        scheduler.add_task(download_plugin_task)
        
        msg = f"Plugin [{key}] begin downloading."
        logger.info(msg)
        return {'is_success': True, 'message': msg, 'task_name': download_plugin_task.name}
    
    @staticmethod
    def delete_plugin(key: str):
        """删除指定插件
        Args:
            key: 插件唯一标识符
        """
        logger.info("Start query plugin package information by key.")
        try:
            plugin = OEDPPlugin.objects.get(key=key)
        except OEDPPlugin.DoesNotExist:
            msg = f"The plugin with key [{key}] does not exist."
            logger.error(msg)
            return {'is_success': False, 'message': msg}
        logger.info("Query plugin package information successfully.")

        # 检查是否在下载中
        if plugin.download_status == Task.Status.IN_PROCESS:
            msg = f"Plugin [{plugin.name}] downlaod in process, please wait."
            logger.info(msg)
            return {'is_success': False, "message": msg}
        
        target_project = os.path.join(PLUGIN_CACHE_DIR, plugin.key)
        if not os.path.exists(target_project):
            if not update_plugin_status(plugin, Task.Status.NOT_YET):
                msg = f"Plugin [{plugin.name}] failed to update status [{Task.Status.NOT_YET}]."
                logger.error(msg)
                return {'is_success': False, "message": msg}
            msg = f"Plugin [{plugin.name}] is already deleted."
            logger.info(msg)
            return {'is_success': True, 'message': msg}
        
        try:
            shutil.rmtree(target_project)
            logger.info(f"Cleaned up failed download directory: {target_project}")
        except Exception as e:
            logger.error(f"Failed to clean up directory {target_project}: {e}")
            msg = f"Failed to delete plugin [{plugin.name}]."
            logger.error(msg)
            return {'is_success': False, "message": msg}
        
        if not update_plugin_status(plugin, Task.Status.NOT_YET):
            msg = f"Plugin [{plugin.name}] failed to update status [{Task.Status.NOT_YET}]."
            logger.error(msg)
            return {'is_success': False, "message": msg}
        
        # 清空action列表(非必须)
        update_plugin_action_list(plugin, [])

        msg = f"Plugin [{plugin.name}] is deleted."
        logger.info(msg)
        return {'is_success': True, 'message': msg}

    @staticmethod
    def run_plugin_action(key: str, action_name: str):
        """执行插件action
        Args:
            key: 插件唯一标识符
            action_name: 要执行的action名称
        """
        logger.info("Start query plugin package information by key.")
        try:
            plugin = OEDPPlugin.objects.get(key=key)
        except OEDPPlugin.DoesNotExist:
            msg = f"The plugin with key [{key}] does not exist."
            logger.error(msg)
            return {'is_success': False, 'message': msg}
        logger.info("Query plugin package information successfully.")

        # 检查是否已经下载插件
        if plugin.download_status != Task.Status.SUCCESS or not PluginMethods._check_plugin_file_exist(key):
            msg = f"Plugin [{plugin.name}] is not downloaded or files missing."
            logger.error(msg)
            return {'is_success': False, "message": msg}
        
        # 检查action合法性
        action_list = plugin.action_list
        action_object = PluginMethods._get_plugin_action_from_list(action_list, action_name)
        if not action_object:
            msg = f"Plugin [{plugin.name}] has no action [{action_name}]."
            logger.error(msg)
            return {'is_success': False, "message": msg}
        
        # 检查是否已经在执行中
        target_project = os.path.join(PLUGIN_CACHE_DIR, key)
        if is_process_running(f"oedp run -p {target_project} -lt {action_name}", timeout=3600):
            msg = f"Plugin [{plugin.name}] action [{action_name}] is in process."
            logger.error(msg)
            return {'is_success': False, "message": msg}
        
        # 每个插件同时只允许触发一个action
        if is_process_running(f"oedp run -p {target_project} -lt", timeout=3600):
            msg = f"Plugin [{plugin.name}]'s another action is in process, only one action can be run at a time."
            logger.error(msg)
            return {'is_success': False, "message": msg}

        # 更新部署操作状态 in process
        set_plugin_action_status(action_list, action_name, Task.Status.IN_PROCESS)
        if not update_plugin_action_list(plugin, action_list):
            msg = f"Failed to update plugin [{plugin.name}] action_list"
            logger.error(msg)
            return {'is_success': False, "message": msg}
        
        # 开始执行部署操作
        logger.info(f"Start to run plugin [{plugin.name}] action [{action_name}].")
        plugin_action_task = PluginActionTask(plugin, action_name, name=f"plugin_action_{key}_task")
        scheduler.add_task(plugin_action_task)
        
        msg = f"Plugin [{plugin.name}] action [{action_name}] is begin running."
        logger.info(msg)
        return {'is_success': True, 'message': msg, 'task_name': plugin_action_task.name}
    
    @staticmethod
    def get_plugin_config(key: str):
        if not PluginMethods._check_plugin_file_exist(key):
            msg = f"Plugin [{key}] is not downloaded or files missing."
            logger.error(msg)
            return status.HTTP_400_BAD_REQUEST ,{'is_success': False, "message": msg, "config_text": ""}
        target_project = os.path.join(PLUGIN_CACHE_DIR, key)
        config_path = os.path.join(target_project, "config.yaml")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_text = f.read()
            msg = f"Get plugin [{key}] config successfully."
            return status.HTTP_200_OK, {'is_success': True, "message": msg, "config_text": config_text}
        except Exception as e:
            msg = f"Failed to read plugin [{key}] config file: {str(e)}"
            logger.error(msg)
            return status.HTTP_500_INTERNAL_SERVER_ERROR, {'is_success': False, "message": msg, "config_text": ""}

    @staticmethod
    def set_plugin_config(key: str, config_text: str):
        if not PluginMethods._check_plugin_file_exist(key):
            msg = f"Plugin [{key}] is not downloaded or files missing."
            logger.error(msg)
            return status.HTTP_400_BAD_REQUEST ,{'is_success': False, "message": msg, "config_text": ""}
        target_project = os.path.join(PLUGIN_CACHE_DIR, key)
        config_path = os.path.join(target_project, "config.yaml")
        config_bak_path = os.path.join(target_project, "config.yaml.bak")
        
        try:
            # 如果备份文件不存在，创建备份
            if not os.path.exists(config_bak_path) and os.path.exists(config_path):
                shutil.copy2(config_path, config_bak_path)
            # 写入新配置
            fd = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(config_text)
            msg = f"Set plugin [{key}] config successfully."
            return status.HTTP_200_OK, {'is_success': True, "message": msg, "config_text": ""}
        except Exception as e:
            msg = f"Failed to set plugin [{key}] config: {str(e)}"
            logger.error(msg)
            return status.HTTP_500_INTERNAL_SERVER_ERROR, {'is_success': False, "message": msg, "config_text": ""}

    @staticmethod
    def reset_plugin_config(key: str):
        if not PluginMethods._check_plugin_file_exist(key):
            msg = f"Plugin [{key}] is not downloaded or files missing."
            logger.error(msg)
            return status.HTTP_400_BAD_REQUEST ,{'is_success': False, "message": msg, "config_text": ""}
        target_project = os.path.join(PLUGIN_CACHE_DIR, key)
        config_path = os.path.join(target_project, "config.yaml")
        config_bak_path = os.path.join(target_project, "config.yaml.bak")
        
        try:
            if os.path.exists(config_bak_path):
                if os.path.exists(config_path):
                    os.remove(config_path)
                shutil.copy2(config_bak_path, config_path)
            with open(config_path, 'r', encoding='utf-8') as f:
                config_text = f.read()
            msg = f"Reset plugin [{key}] config successfully."
            return status.HTTP_200_OK, {'is_success': True, "message": msg, "config_text": config_text}
            
        except Exception as e:
            msg = f"Failed to reset plugin [{key}] config: {str(e)}"
            logger.error(msg)
            return status.HTTP_500_INTERNAL_SERVER_ERROR, {'is_success': False, "message": msg, "config_text": ""}
    
    @staticmethod
    def get_plugin_log(key: str):
        if not PluginMethods._check_plugin_file_exist(key):
            msg = f"Plugin [{key}] is not downloaded or files missing."
            logger.error(msg)
            return status.HTTP_400_BAD_REQUEST ,{'is_success': False, "message": msg, "log": ""}
        target_project = os.path.join(PLUGIN_CACHE_DIR, key)
        log_file = os.path.join(target_project, "run.log")
        if not os.path.exists(log_file):
            msg = f"Plugin [{key}] has no log file."
            return status.HTTP_200_OK, {'is_success': True, "message": msg, "log": ""}
        
        try:
            file_size = os.path.getsize(log_file)
            if file_size > 100 * 1024:  # 超过100KB
                with open(log_file, 'rb') as f:
                    f.seek(-100 * 1024, os.SEEK_END)
                    log_text = f.read().decode('utf-8', errors='ignore')
            else:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_text = f.read()
            msg = f"Get log successfully."
            return status.HTTP_200_OK, {'is_success': True, "message": msg, "log": log_text}
        except Exception as e:
            msg = f"Failed to read log file {log_file}: {str(e)}"
            logger.error(msg)
            return status.HTTP_500_INTERNAL_SERVER_ERROR, {'is_success': False, "message": msg, "log": ""}
    
    @staticmethod
    def _update_plugin_info():
        """更新插件仓库信息"""
        # 检查 oedp 命令是否可用
        logger.info("Start to check if the oedp is installed.")
        cmd_executor = CommandExecutor(['rpm', '-q', 'oedp'])
        _, _, return_code = cmd_executor.run()
        if return_code != 0:
            msg = "The oedp is not installed."
            logger.error(msg)
            return False, msg
        logger.info("The oedp has already been installed.")

        # 执行 oedp repo update
        cmd = ['oedp', 'repo', 'update']
        logger.info(f'Start to execute command [{" ".join(cmd)}].')
        cmd_executor = CommandExecutor(cmd)
        _, stderr, return_code = cmd_executor.run()
        if return_code != 0:
            msg = f"Failed to execute command: [{' '.join(cmd)}]. Error: {stderr}"
            logger.error(msg)
            return False, msg
        
        msg = 'Update plugin repo successfully.'
        logger.info(msg)
        return True, msg

    @staticmethod
    def _get_plugin_yaml_files():
        """获取插件 YAML 文件列表"""
        plugin_repo_dir = Path(PLUGIN_REPO_DIR)
        if not plugin_repo_dir.exists():
            msg = f'Path {plugin_repo_dir} not exists.'
            logger.error(msg)
            return None, msg
        if not plugin_repo_dir.is_dir():
            msg = f'Path {plugin_repo_dir} is not a directory.'
            logger.error(msg)
            return None, msg
        
        plugin_yaml_list = [str(file) for file in plugin_repo_dir.iterdir()
                            if file.is_file() and (file.suffix == '.yaml' or file.suffix == '.yml')]
        logger.info(f"The plugin meta files: {plugin_yaml_list}")
        return plugin_yaml_list, ''

    @staticmethod
    def _parse_yaml_file(plugin_yaml, plugin_dict):
        """解析单个 YAML 文件并添加插件信息"""
        try:
            yaml_handler = YAMLHandler(file_path=plugin_yaml, logger=logger)
        except (FileError, yaml.YAMLError) as ex:
            return False, str(ex)
        
        for multi_version_plugins in yaml_handler.data.get('plugins'):
            for plugin_info in list(multi_version_plugins.values())[0]:
                plugin_info['key'] = plugin_info['name'] + '_' + plugin_info['version']
                plugin_info['updated_at'] = plugin_info.pop('updated')
                plugin_info['readme'] = PluginMethods._get_plugin_readme(plugin_info['key'])
                plugin_info['icon'] = PluginMethods._get_plugin_icon(plugin_info['key'])
                description = plugin_info.pop('description')
                plugin_info['description'] = {'default': description}
                
                key = plugin_info['key']
                if key not in plugin_dict:
                    plugin_dict[key] = plugin_info
                    continue
                elif plugin_info['updated_at'] > plugin_dict[key]['updated_at']:
                    plugin_dict[key] = plugin_info
                    logger.info(f"Duplicate key {key} found, keeping newer version.")
        return True, ''

    @staticmethod
    def _read_plugin_info():
        """读取插件信息并生成数据结构"""
        logger.info("Start to get YAML files.")
        plugin_yaml_list, msg = PluginMethods._get_plugin_yaml_files()
        if plugin_yaml_list is None:
            return [], msg

        logger.info("Start to read YAML files and generate plugin data.")
        plugin_dict = {}
        for plugin_yaml in plugin_yaml_list:
            success, error_msg = PluginMethods._parse_yaml_file(plugin_yaml, plugin_dict)
            if not success:
                return [], error_msg

        plugin_data = list(plugin_dict.values())
        msg = 'Generate plugin data successfully.'
        logger.info(msg)
        return plugin_data, msg

    @staticmethod
    def _get_plugin_readme(plugin_key: str = ""):
        """获取插件的README内容"""
        if not plugin_key:
            return ""
        plugin_dir = os.path.join(REPO_DETAILS_DIR, plugin_key)
        if not os.path.exists(plugin_dir):
            logger.error(f"Plugin directory not found: {plugin_dir}")
            return ""
        readme_path = os.path.join(plugin_dir, "doc", "readme.md")
        if not os.path.exists(readme_path):
            return ""
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read readme.md: {e}")
            return ""

    @staticmethod
    def _get_plugin_icon(plugin_key: str = ""):
        """获取插件的图标Base64编码"""
        if not plugin_key:
            return ""
        plugin_dir = os.path.join(REPO_DETAILS_DIR, plugin_key)
        icon_path = os.path.join(plugin_dir, "doc", "icon.png")
        if not os.path.exists(icon_path):
            return ""
        try:
            with open(icon_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to read icon.png: {e}")
            return ""

    @staticmethod
    def _check_plugin_file_exist(key: str):
        """检查插件文件是否存在
        Args:
            key: 插件唯一标识符
        Returns:
            bool: 文件是否存在
        """
        target_project = os.path.join(PLUGIN_CACHE_DIR, key)
        if not os.path.exists(target_project):
            return False
        required_files = [
            os.path.join(target_project, 'main.yaml'),
            os.path.join(target_project, 'config.yaml')
        ]
        required_dirs = [
            os.path.join(target_project, 'workspace')
        ]
        # 检查所有必需文件和目录是否存在
        for file_path in required_files:
            if not os.path.exists(file_path):
                return False
        for dir_path in required_dirs:
            if not os.path.isdir(dir_path):
                return False
        return True


    @staticmethod
    def _get_plugin_action_from_list(action_list, action_name):
        """从action列表中获取指定action
        Args:
            action_list: 插件action列表
            action_name: 要获取的action名称
        """
        for action in action_list:
            if action["name"] != action_name:
                continue
            return action
        return []