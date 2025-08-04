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

import os

from datetime import datetime
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
from artifacts.utils import get_devstore_log
from utils.mcp_tools import get_mcp_status_in_apps, manage_mcp_config
from constants.choices import ArtifactTag
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
        data_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = "Sync data successfully."
        logger.info(msg)
        return Response({'is_success': True, 'message': msg, 'time': data_time}, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='sync-mcp')
    def sync_mcp_only(self, request):
        """单独同步MCP服务信息（新增接口）"""
        logger.info("==== API: [POST] /v1.0/artifacts/sync-mcp/ ====")

        # 只同步MCP服务信息
        result = MCPMethods.sync_mcps()
        if not result['is_success']:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        msg = "Sync MCP data successfully."
        logger.info(msg)
        return Response({'is_success': True, 'message': msg}, status=status.HTTP_200_OK)


    @action(methods=['POST'], detail=False)
    @check_scheduler_load
    def mcp_install(self, request):
        """安装MCP包"""
        logger.info(f"==== API: [POST] /v1.0/artifacts/mcp_install/ ====")
        
        # 获取必需参数
        key = request.query_params.get('key')
        
        # 参数验证
        if not key:
            return Response(
                {'is_success': False, 'message': f"Missing required parameter: {key}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Installing MCP package for key: {key}")
        
        # 调用统一的MCP包管理方法
        result = MCPMethods.mcp_package_action(key, 'install')
        
        # 根据结果设置HTTP状态码
        status_code = result.get('status_code', status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(result, status=status_code)


    @action(methods=['POST'], detail=False)
    @check_scheduler_load
    def mcp_uninstall(self, request):
        """卸载MCP包"""
        logger.info(f"==== API: [POST] /v1.0/artifacts/mcp_uninstall/ ====")
        
        # 获取必需参数
        key = request.query_params.get('key')
        
        # 参数验证
        if not key:
            return Response(
                {'is_success': False, 'message': f"Missing required parameter: {key}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Uninstalling MCP package for key: {key}")
        
        # 调用统一的MCP包管理方法
        result = MCPMethods.mcp_package_action(key, 'uninstall')
        
        # 根据结果设置HTTP状态码
        status_code = result.get('status_code', status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(result, status=status_code)

    @action(methods=['GET'], detail=False)
    def mcp_apps_status(self, request):
        """获取MCP在所有智能体应用中的配置状态"""
        logger.info(f"==== API: [GET] /v1.0/artifacts/mcp_apps_status/ ====")
        
        # 获取必需参数
        package_name = request.query_params.get('package_name')
        
        # 参数验证
        if not package_name:
            return Response(
                {'is_success': False, 'message': f"Missing required parameter: package_name"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Querying MCP status in apps for: {package_name}")
        
        # 调用MCP状态查询方法
        result = get_mcp_status_in_apps(package_name)
        
        # 根据结果设置HTTP状态码
        status_code = result.get('status_code', status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 创建响应并添加防缓存头
        response = Response(result, status=status_code)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return Response(result, status=status_code)

    @action(methods=['POST'], detail=False)
    def mcp_config_manage(self, request):
        """管理MCP配置（添加或删除）"""
        logger.info(f"==== API: [POST] /v1.0/artifacts/mcp_config_manage/ ====")
        
        # 获取必需参数
        action = request.query_params.get('action')
        package_name = request.query_params.get('package_name')
        app_name = request.query_params.get('app_name')
        
        # 参数验证
        if not action:
            return Response(
                {'is_success': False, 'message': f"Missing required parameter: action"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        if not package_name:
            return Response(
                {'is_success': False, 'message': f"Missing required parameter: package_name"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        if not app_name:
            return Response(
                {'is_success': False, 'message': f"Missing required parameter: app_name"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Managing MCP config - action: {action}, mcp: {package_name}, app: {app_name}")
        
        # 调用MCP配置管理方法
        result = manage_mcp_config(action, package_name, app_name)
        
        # 根据结果设置HTTP状态码
        status_code = result.get('status_code', status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(result, status=status_code)


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
        logger.debug(msg)
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
    @check_scheduler_load
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
    
    @action(methods=['GET'], detail=False)
    def plugin_config(self, request):
        """插件用户配置相关操作
        """
        logger.info(f"==== API: [POST] /v1.0/artifacts/plugin_config/ ====")
        key = request.query_params.get('key')
        operation = request.query_params.get('operation', "get")
        config_text = request.query_params.get('config_text', "")

        if operation == "set":
            status_code, result = PluginMethods.set_plugin_config(key, config_text)
        elif operation == "reset":
            status_code, result = PluginMethods.reset_plugin_config(key)
        else:
            status_code, result = PluginMethods.get_plugin_config(key)
        
        return Response(result, status=status_code)
    
    @action(methods=['GET'], detail=False)
    def log(self, request):
        """插件用户配置相关操作
        """
        logger.debug(f"==== API: [POST] /v1.0/artifacts/log/ ====")
        key = request.query_params.get('key')
        if key == "DevStore":
            log_text = get_devstore_log()
            result = {'is_success': True, "message": "Fetch DevStore log done.", "log": log_text}
            status_code = status.HTTP_200_OK
        else:
            status_code, result = PluginMethods.get_plugin_log(key)
        return Response(result, status=status_code)
