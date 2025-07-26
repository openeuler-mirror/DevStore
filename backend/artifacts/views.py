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

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from artifacts.methods.mcp_methods import MCPMethods
from artifacts.methods.plugin_methods import PluginMethods
from artifacts.models import MCPServer, OEDPPlugin
from artifacts.serializers import (
    ArtifactSerializer,
    MCPDetailSerializer,
    PluginDetailSerializer,
)
from artifacts.tasks.install_mcp_task import InstallMCPTask
from constants.choices import ArtifactTag
from constants.paths import PLUGIN_CACHE_DIR
from tasks.models import Task
from tasks.scheduler import scheduler, check_scheduler_load
from utils.cmd_executor import CommandExecutor
from utils.logger import init_log

logger = init_log('run.log')


class ArtifactViewSet(viewsets.GenericViewSet):

    @action(methods=['POST'], detail=False)
    def sync(self, request):
        """同步插件和MCP服务信息
        """
        # TODO：同步加锁，禁用黑名单接口
        logger.info("==== API: [POST] /v1.0/artifacts/sync/ ====")
        
        # 使用PluginMethods同步插件信息
        result = PluginMethods.sync_plugins()
        if not result['is_success']:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 使用MCPMethods同步MCP服务信息
        result = MCPMethods.sync_mcps()
        if not result['is_success']:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 仅返回调用结果
        msg = "Sync data successfully."
        logger.info(msg)
        return Response({'is_success': True, 'message': msg}, status=status.HTTP_200_OK)

    def list(self, request):
        """获取插件和MCP服务列表
        """
        logger.info("==== API: [GET] /v1.0/artifacts/ ====")
        tag = request.query_params.get('tag')
        oedp_queryset = OEDPPlugin.objects.all()
        mcp_queryset = MCPServer.objects.all()
        oedp_count = oedp_queryset.count()
        mcp_count = mcp_queryset.count()
        if tag == ArtifactTag.OEDP:
            queryset = oedp_queryset
        elif tag == ArtifactTag.MCP:
            queryset = mcp_queryset
        else:
            msg = 'The query parameter [tag] is missing, or the value of the query parameter [tag] is invalid.'
            logger.error(msg)
            return Response({'is_success': False, 'message': msg}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.paginate_queryset(queryset)
        serializer = ArtifactSerializer(queryset, many=True)
        response = self.get_paginated_response(serializer.data)
        data = { 'oedp_count': oedp_count, 'mcp_count': mcp_count }
        data.update(response.data)
        msg = "Get list information successfully."
        response.data = { 'is_success': True, 'message': msg, 'data': data }
        logger.info(msg)
        return response
    
    @action(methods=['GET'], detail=False)
    def details(self, request):
        """获取插件或MCP服务的详细信息
        """
        logger.info(f'==== API: [GET] /v1.0/artifacts/details/ ====')
        key = request.query_params.get('key')
        tag = request.query_params.get('tag')
        if tag == ArtifactTag.MCP:
            try:
                mcp_service = MCPServer.objects.get(key=key)
            except MCPServer.DoesNotExist:
                msg = f"The MCP Server with key [{key}] does not exist."
                logger.error(msg)
                return Response({'is_success': False, 'message': msg}, status=status.HTTP_400_BAD_REQUEST)
            serializer = MCPDetailSerializer(mcp_service)
        elif tag == ArtifactTag.OEDP:
            try:
                plugin = OEDPPlugin.objects.get(key=key)
            except OEDPPlugin.DoesNotExist:
                msg = f"The plugin with key [{key}] does not exist."
                logger.error(msg)
                return Response({'is_success': False, 'message': msg}, status=status.HTTP_400_BAD_REQUEST)
            serializer = PluginDetailSerializer(plugin)
        else:
            msg = 'The query parameter [tag] is missing, or the value of the query parameter [tag] is invalid.'
            logger.error(msg)
            return Response({'is_success': False, 'message': msg}, status=status.HTTP_400_BAD_REQUEST)
        msg = 'Get detail successfully.'
        logger.info(msg)
        return Response({'is_success': True, 'message': msg, 'data': serializer.data}, status=status.HTTP_200_OK)
    
    @action(methods=['GET'], detail=False)
    def task_info(self, request):
        """获取任务信息
        """
        logger.info(f'==== API: [GET] /v1.0/artifacts/task_info/ ====')
        task_name = request.query_params.get('task_name')
        try:
            task = Task.objects.get(name=task_name)
        except Task.DoesNotExist:
            msg = f"Task [{task_name}] not found."
            return Response({'is_success': False, 'message': msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'is_success': True,
            'message': "Checking task status successfully.",
            'data': {'name': task.name, 'type': task.type, 'status': task.status, 'msg': task.msg}
        }, status=status.HTTP_200_OK)
    
    @action(methods=['POST'], detail=False)
    @check_scheduler_load
    def download_plugin(self, request):
        """下载指定插件
        """
        logger.info(f"==== API: [POST] /v1.0/artifacts/download_plugin/ ====")
        key = request.query_params.get('key')
        result = PluginMethods.download_plugin(key)
        
        status_code = status.HTTP_200_OK
        if not result['is_success']:
            status_code = status.HTTP_400_BAD_REQUEST
        elif 'task_name' in result:
            status_code = status.HTTP_202_ACCEPTED
            
        return Response(result, status=status_code)
    
    @action(methods=['POST'], detail=False)
    def delete_plugin(self, request):
        """删除指定插件
        """
        logger.info(f"==== API: [POST] /v1.0/artifacts/delete_plugin/ ====")
        key = request.query_params.get('key')
        result = PluginMethods.delete_plugin(key)
        
        status_code = status.HTTP_200_OK
        if not result['is_success']:
            status_code = status.HTTP_400_BAD_REQUEST
            
        return Response(result, status=status_code)
    
    @action(methods=['POST'], detail=False)
    def plugin_action(self, request):
        """执行插件的某个部署操作
        """
        logger.info(f"==== API: [POST] /v1.0/artifacts/plugin_action/ ====")
        key = request.query_params.get('key')
        action_name = request.query_params.get('action_name')
        
        result = PluginMethods.run_plugin_action(key, action_name)
        status_code = status.HTTP_200_OK
        if not result['is_success']:
            status_code = status.HTTP_400_BAD_REQUEST
        elif 'task_name' in result:
            status_code = status.HTTP_202_ACCEPTED
            
        return Response(result, status=status_code)

    @action(methods=['GET'], detail=True)
    @check_scheduler_load
    def install_mcp(self, request, pk):
        """安装MCP服务
        """
        # TODO：同一时间只能安装一个 mcp-servers-xxx 的包
        # TODO：无法安装正在卸载的包
        logger.info(f'==== API: [GET] /v1.0/artifacts/{pk}/install_mcp/ ====')
        # 查询 MCP 服务包信息
        logger.info("Start query MCP service package information by key.")
        try:
            mcp_service = MCPServer.objects.get(id=pk)
        except MCPServer.DoesNotExist:
            msg = f"The MCP service with key {pk} does not exist."
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
        """卸载MCP服务
        """
        # TODO：无法卸载正在安装的包
        logger.info(f"==== API: [GET] /v1.0/artifacts/{pk}/uninstall_mcp/ ====")
        # 查询 MCP 服务包信息
        logger.info("Start query MCP service package information by key.")
        try:
            mcp_service = MCPServer.objects.get(id=pk)
        except MCPServer.DoesNotExist:
            msg = f"The MCP service with key {pk} does not exist."
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
