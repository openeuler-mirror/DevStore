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
# Create: 2025-07-18
# ======================================================================================================================

import glob
import gzip
import os.path
import shutil
from pathlib import Path
from xml.etree import ElementTree

import yaml
from django.db import connection
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from artifacts.models import MCPService, Plugin
from artifacts.serializers import (
    ArtifactSerializer,
    PluginBulkCreateSerializer,
    MCPBulkCreateSerializer,
    MCPDetailSerializer,
    PluginDetailSerializer
)
from artifacts.tasks.install_mcp_task import InstallMCPTask
from constants.choices import ArtifactTag
from constants.paths import PLUGIN_REPO_DIR, PLUGIN_CACHE_DIR
from tasks.models import Task
from tasks.scheduler import scheduler, check_scheduler_load
from utils.cmd_executor import CommandExecutor
from utils.file_handler.base_handler import FileError
from utils.file_handler.yaml_handler import YAMLHandler
from utils.logger import init_log
from utils.time import timestamp2local

logger = init_log('run.log')


class ArtifactViewSet(viewsets.GenericViewSet):

    @staticmethod
    def _update_plugin_info():
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
    def _read_plugin_info():
        # 获取记录插件信息的 YAML 文件
        logger.info("Start to get YAML files.")
        plugin_repo_dir = Path(PLUGIN_REPO_DIR)
        if not plugin_repo_dir.exists():
            msg = f'Path {plugin_repo_dir} not exists.'
            logger.error(msg)
            return [], msg
        if not plugin_repo_dir.is_dir():
            msg = f'Path {plugin_repo_dir} is not a directory.'
            logger.error(msg)
            return [], msg
        plugin_yaml_list = [str(file) for file in plugin_repo_dir.iterdir()
                            if file.is_file() and (file.suffix == '.yaml' or file.suffix == '.yml')]
        logger.info(f"The plugin meta files: {plugin_yaml_list}")

        # 读取 YAML 文件, 生成插件信息列表
        logger.info("Start to read YAML files and generate plugin data.")
        plugin_data = []
        for plugin_yaml in plugin_yaml_list:
            try:
                yaml_handler = YAMLHandler(file_path=plugin_yaml, logger=logger)
            except (FileError, yaml.YAMLError) as ex:
                return [], str(ex)
            for multi_version_plugins in yaml_handler.data.get('plugins'):
                for plugin_info in list(multi_version_plugins.values())[0]:
                    plugin_info['updated_at'] = plugin_info.pop('updated')
                    plugin_info['download_url'] = " ".join(plugin_info.pop('urls'))
                    plugin_data.append(plugin_info)

        msg = 'Generate plugin data successfully.'
        logger.info(msg)
        return plugin_data, msg

    @staticmethod
    def _update_mcp_info():
        cmd = ['yum', 'makecache', '--disablerepo=*', '--enablerepo=mcp']
        logger.info(f"Start to execute command [{' '.join(cmd)}].")
        cmd_executor = CommandExecutor(cmd)
        _, stderr, code = cmd_executor.run()
        if code != 0:
            msg = f"Failed to execute command: [{' '.join(cmd)}]. Error: {stderr}"
            logger.error(msg)
            return False, msg

        msg = 'Update MCP repo successfully.'
        logger.info(msg)
        return True, msg

    @staticmethod
    def _read_mcp_info():
        # 匹配 primary.xml.gz 文件
        logger.info('Start to match MCP meta file.')
        pattern = "/var/cache/dnf/mcp-*/repodata/*-primary.xml.gz"
        matches = glob.glob(pattern)
        if not matches:
            msg = "No match for *-primary.xml.gz."
            logger.error(msg)
            return [], msg
        primary_file = matches[0]
        logger.info(f"The MCP meta file: {primary_file}")

        # 开始解压 primary.xml.gz
        logger.info(f'Start to extract {primary_file}')
        output_file = primary_file.rstrip('.gz')
        try:
            with gzip.open(primary_file, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logger.info(f"extract successfully: {primary_file} -> {output_file}")
        except PermissionError:
            msg = "No permission."
            logger.error(msg)
            return [], msg
        except gzip.BadGzipFile:
            msg = f"{primary_file} is not a valid gzip format."
            logger.error(msg)
            return [], msg

        # 读取 primary.xml 文件，生成 MCP 服务信息列表
        logger.info("Start to read MCP information files and generate MCP data.")
        tree = ElementTree.parse(output_file)
        root = tree.getroot()
        namespace = {'common': 'http://linux.duke.edu/metadata/common'}
        mcp_data = []
        for package in root.findall('common:package', namespace):
            mcp_info = {}
            package_name = package.find('common:name', namespace).text.strip()
            if package_name == 'mcp-servers':
                continue
            else:
                mcp_info['package_name'] = package_name
                mcp_info['name'] = package_name.removeprefix('mcp-servers-')
            version = package.find('common:version', namespace)
            mcp_info['version'] = f"{version.get('epoch')}:{version.get('ver')}-{version.get('rel')}"
            timestamp = package.find('common:time', namespace).get('file')
            mcp_info['updated_at'] = timestamp2local(int(timestamp))
            mcp_info['description'] = package.find('common:description', namespace).text
            mcp_info['size'] = int(package.find('common:size', namespace).get('package'))
            mcp_info['repo'] = package.find('common:url', namespace).text
            mcp_data.append(mcp_info)

        if not mcp_data:
            msg = f"Failed to read mcp information."
            logger.error(msg)
            return [], msg

        msg = 'Generate MCP service data successfully.'
        logger.info(msg)
        return mcp_data, msg

    @staticmethod
    def _clear_table(table_name):
        """
        清空指定数据库表并重置自增主键
        """
        logger.info(f"Start to clear table '{table_name}'")
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name}")

    def list(self, request):
        logger.info("==== API: [GET] /v1.0/artifacts/ ====")
        tag = request.query_params.get('tag')
        if tag == ArtifactTag.OEDP:
            queryset = Plugin.objects.all()
        elif tag == ArtifactTag.MCP:
            queryset = MCPService.objects.all()
        else:
            msg = 'The query parameter [tag] is missing, or the value of the query parameter [tag] is invalid.'
            logger.error(msg)
            return Response({
                'is_success': False,
                'message': msg
            }, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.paginate_queryset(queryset)
        serializer = ArtifactSerializer(queryset, many=True)
        logger.info("Get list information successfully.")
        return self.get_paginated_response(serializer.data)

    @staticmethod
    def retrieve(request, pk):
        # TODO 添加任务状态判断逻辑
        logger.info(f"==== API: [GET] /v1.0/artifacts/{pk}/ ====")
        tag = request.query_params.get('tag')
        if tag == ArtifactTag.MCP:
            try:
                mcp_service = MCPService.objects.get(id=pk)
            except MCPService.DoesNotExist:
                msg = f"The MCP service with ID {pk} does not exist."
                logger.error(msg)
                return Response({
                    'is_success': False,
                    'message': msg
                }, status=status.HTTP_400_BAD_REQUEST)
            serializer = MCPDetailSerializer(mcp_service)
        elif tag == ArtifactTag.OEDP:
            try:
                plugin = Plugin.objects.get(id=pk)
            except Plugin.DoesNotExist:
                msg = f"The plugin with ID {pk} does not exist."
                logger.error(msg)
                return Response({
                    'is_success': False,
                    'message': msg
                }, status=status.HTTP_400_BAD_REQUEST)
            serializer = PluginDetailSerializer(plugin)
        else:
            msg = 'The query parameter [tag] is missing, or the value of the query parameter [tag] is invalid.'
            logger.error(msg)
            return Response({
                'is_success': False,
                'message': msg
            }, status=status.HTTP_400_BAD_REQUEST)
        msg = 'Get detail successfully.'
        logger.info(msg)
        return Response({
            'is_success': True,
            'message': msg,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def get_task_info(self, request):
        logger.info(f'==== API: [GET] /v1.0/artifacts/get_task_info/ ====')
        task_name = request.query_params.get('task_name')
        try:
            task = Task.objects.get(name=task_name)
        except Task.DoesNotExist:
            msg = f"Task {task_name} not found."
            return Response({
                'is_success': False,
                'message': msg
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'is_success': True,
            'message': "Checking task status successfully.",
            'data': {
                'name': task.name,
                'type': task.type,
                'status': task.status,
                'msg': task.msg
            }
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    @check_scheduler_load
    def install_mcp(self, request, pk):
        # TODO 同一时间只能安装一个 mcp-servers-xxx 的包
        # TODO 无法安装正在卸载的包
        logger.info(f'==== API: [GET] /v1.0/artifacts/{pk}/install_mcp/ ====')
        # 查询 MCP 服务包信息
        logger.info("Start query MCP service package information by id.")
        try:
            mcp_service = MCPService.objects.get(id=pk)
        except MCPService.DoesNotExist:
            msg = f"The MCP service with ID {pk} does not exist."
            logger.error(msg)
            return Response({
                'is_success': False,
                'message': msg
            }, status.HTTP_400_BAD_REQUEST)
        logger.info("Query MCP service package successfully.")

        # 检查 MCP 服务包是否已经安装，后端进行二次校验
        pkg_name = mcp_service.package_name
        logger.info(f"Start to check whether package {pkg_name} is installed.")
        cmd = ['rpm', '-q', pkg_name]
        cmd_executor = CommandExecutor(cmd)
        _, _, code = cmd_executor.run()
        if code == 0:
            msg = f"{pkg_name} has been installed."
            logger.info(msg)
            return Response({
                'is_success': True,
                'message': msg
            }, status=status.HTTP_200_OK)

        # 安装 MCP 服务包
        logger.info(f"Start to install package {pkg_name}")
        install_mcp_task = InstallMCPTask(pkg_name, name=f"install_{pkg_name}_task")
        scheduler.add_task(install_mcp_task)
        return Response({
            'is_success': True,
            'message': f"Package {pkg_name} is being installed.",
            'task_name': install_mcp_task.name
        }, status=status.HTTP_202_ACCEPTED)

    @action(methods=['GET'], detail=True)
    def uninstall_mcp(self, request, pk):
        # TODO 无法卸载正在安装的包
        logger.info(f"==== API: [GET] /v1.0/artifacts/{pk}/uninstall_mcp/ ====")
        # 查询 MCP 服务包信息
        logger.info("Start query MCP service package information by id.")
        try:
            mcp_service = MCPService.objects.get(id=pk)
        except MCPService.DoesNotExist:
            msg = f"The MCP service with ID {pk} does not exist."
            logger.error(msg)
            return Response({
                'is_success': False,
                'message': msg
            }, status.HTTP_400_BAD_REQUEST)
        logger.info("Query MCP service package successfully.")

        # 检查 MCP 服务包是否已经安装，后端进行二次校验
        pkg_name = mcp_service.package_name
        logger.info(f"Start to check whether package {pkg_name} is installed.")
        cmd = ['rpm', '-q', pkg_name]
        cmd_executor = CommandExecutor(cmd)
        _, _, code = cmd_executor.run()
        if code != 0:
            msg = f"{pkg_name} isn't installed."
            logger.info(msg)
            return Response({
                'is_success': True,
                'message': msg
            }, status=status.HTTP_200_OK)

        # 卸载 MCP 服务包
        logger.info(f"Start to uninstall package {pkg_name}")
        cmd = ['yum', 'remove', '-y', pkg_name]
        cmd_executor = CommandExecutor(cmd)
        _, stderr, code = cmd_executor.run()
        if code != 0:
            logger.error(f"Failed to uninstall {pkg_name}, error: {stderr}")
            return Response({
                'is_success': False,
                'message': stderr
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        msg = f"Package {pkg_name} is uninstalled successfully."
        logger.info(msg)
        return Response({
            'is_success': True,
            'message': msg
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def add_to_agent_app(self, request, pk):
        pass

    @action(methods=['GET'], detail=True)
    def download_plugin(self, request, pk):
        logger.info(f"==== API: [GET] /v1.0/artifacts/{pk}/download_plugin/ ====")
        # 查询插件信息
        logger.info("Start query plugin package information by id.")
        try:
            plugin = Plugin.objects.get(id=pk)
        except Plugin.DoesNotExist:
            msg = f"The plugin with ID {pk} does not exist."
            logger.error(msg)
            return Response({
                'is_success': False,
                'message': msg
            }, status.HTTP_400_BAD_REQUEST)
        logger.info("Query plugin package information successfully.")

        # 检查本地插件是否已经存在
        logger.info(f"Start to check whether plugin {plugin.name} already exists.")
        if os.path.exists(os.path.join(PLUGIN_CACHE_DIR, plugin.name)):
            msg = f"Plugin {plugin.name} already exists."
            logger.info(msg)
            return Response({
                'is_success': True,
                "message": msg
            }, status=status.HTTP_200_OK)

        # 下载插件
        logger.info(f"Start to download plugin {plugin.name}.")
        if not os.path.exists(PLUGIN_CACHE_DIR):
            os.makedirs(PLUGIN_CACHE_DIR)
            logger.info(f"Create directory: {PLUGIN_CACHE_DIR}.")
        cmd = ['oedp', 'init', plugin.name, '-d', PLUGIN_CACHE_DIR]
        cmd_executor = CommandExecutor(cmd)
        _, stderr, code = cmd_executor.run()
        if code != 0:
            logger.error(f"Failed to download plugin {plugin.name}, error: {stderr}")
            return Response({
                'is_success': False,
                "message": stderr
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        msg = f"Download plugin {plugin.name} successfully."
        logger.info(msg)
        return Response({
            'is_success': True,
            'message': msg
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def sync(self, request):
        # TODO 同步加锁，禁用黑名单接口
        logger.info("==== API: [GET] /v1.0/artifacts/sync/ ====")
        # 更新插件信息
        update_result, msg = self._update_plugin_info()
        if not update_result:
            return Response({
                'is_success': False,
                'message': msg
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 读取插件的信息
        plugin_data, msg = self._read_plugin_info()
        if not plugin_data:
            return Response({
                'is_success': False,
                'message': msg
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 将插件的信息存入数据库中
        serializer = PluginBulkCreateSerializer(data=plugin_data, many=True)
        self._clear_table(Plugin._meta.db_table)
        if not serializer.is_valid():
            logger.error(f"Failed to validate plugin data, errors: {serializer.errors}")
            return Response({
                'is_success': False,
                'errors': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        plugins = serializer.save()
        logger.info("Store plugin data to database successfully.")

        # 更新 MCP 服务的信息
        update_result, msg = self._update_mcp_info()
        if not update_result:
            return Response({
                'is_success': False,
                'message': msg
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 读取 MCP 服务的信息
        mcp_data, msg = self._read_mcp_info()
        if not mcp_data:
            return Response({
                'is_success': False,
                'message': msg
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 将 MCP 服务的信息存入数据库中
        serializer = MCPBulkCreateSerializer(data=mcp_data, many=True)
        self._clear_table(MCPService._meta.db_table)
        if not serializer.is_valid():
            logger.error(f"Failed to validate MCP data, errors: {serializer.errors}")
            return Response({
                'is_success': False,
                'errors': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        mcps = serializer.save()
        logger.info("Store MCP data to database successfully.")

        # 根据 tag 返回 OEDP 插件分页信息或 MCP 服务分页信息
        tag = request.query_params.get('tag') if request.query_params.get('tag') else ArtifactTag.OEDP
        if tag == ArtifactTag.OEDP:
            plugin_ids = [plugin.id for plugin in plugins]
            queryset = Plugin.objects.filter(id__in=plugin_ids)
        elif tag == ArtifactTag.MCP:
            mcp_ids = [mcp.id for mcp in mcps]
            queryset = MCPService.objects.filter(id__in=mcp_ids)
        else:
            msg = f'Invalid value of request parameter "tag", the values: {tag}'
            logger.error(msg)
            return Response({
                'is_success': False,
                'message': msg
            }, status=status.HTTP_400_BAD_REQUEST)

        plugin_queryset = self.paginate_queryset(queryset)
        artifact_serializer = ArtifactSerializer(plugin_queryset, many=True)
        return self.get_paginated_response(artifact_serializer.data)
