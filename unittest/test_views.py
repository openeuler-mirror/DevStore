#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from tasks.models import Task
from artifacts.views import ArtifactViewSet
from artifacts.models import OEDPPlugin, MCPServer
from constants.choices import ArtifactTag


class TestArtifactViewSet(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.viewset = ArtifactViewSet()

    @patch('artifacts.views.PluginMethods.sync_plugins')
    @patch('artifacts.views.MCPMethods.sync_mcps')
    def test_sync_both_success(self, mock_sync_mcps, mock_sync_plugins):
        """测试同步插件和MCP都成功"""
        mock_sync_plugins.return_value = {'is_success': True}
        mock_sync_mcps.return_value = {'is_success': True}
        
        request = self.factory.post('/v1.0/artifacts/sync/')
        self.viewset.request = request
        
        response = self.viewset.sync(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.sync_plugins')
    @patch('artifacts.views.MCPMethods.sync_mcps')
    def test_sync_plugin_success_mcp_fail(self, mock_sync_mcps, mock_sync_plugins):
        """测试插件同步成功但MCP失败"""
        mock_sync_plugins.return_value = {'is_success': True}
        mock_sync_mcps.return_value = {'is_success': False}
        
        request = self.factory.post('/v1.0/artifacts/sync/')
        self.viewset.request = request
        
        response = self.viewset.sync(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.sync_plugins')
    @patch('artifacts.views.MCPMethods.sync_mcps')
    def test_sync_both_fail(self, mock_sync_mcps, mock_sync_plugins):
        """测试同步插件和MCP都失败"""
        mock_sync_plugins.return_value = {'is_success': False}
        mock_sync_mcps.return_value = {'is_success': False}
        
        request = self.factory.post('/v1.0/artifacts/sync/')
        self.viewset.request = request
        
        response = self.viewset.sync(request)
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.OEDPPlugin.objects')
    @patch('artifacts.views.MCPServer.objects')
    def test_list_invalid_tag(self, mock_mcp_objects, mock_plugin_objects):
        """测试无效的tag参数"""
        mock_plugin_objects.count.return_value = 5
        mock_mcp_objects.count.return_value = 3
        
        request = self.factory.get('/v1.0/artifacts/')
        request.query_params = {'tag': 'invalid_tag'}
        self.viewset.request = request
        
        response = self.viewset.list(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    def test_details_missing_key(self):
        """测试缺少key参数"""
        request = self.factory.get('/v1.0/artifacts/details/')
        request.query_params = {'tag': ArtifactTag.OEDP}
        self.viewset.request = request
        
        # 由于KeyError，需要捕获异常
        with self.assertRaises(Exception):
            self.viewset.details(request)

    @patch('artifacts.views.MCPServer.objects')
    def test_details_mcp_not_exist(self, mock_objects):
        """测试MCP服务不存在"""
        mock_objects.get.side_effect = MCPServer.DoesNotExist
        
        request = self.factory.get('/v1.0/artifacts/details/')
        request.query_params = {'key': 'nonexistent', 'tag': ArtifactTag.MCP}
        self.viewset.request = request
        
        response = self.viewset.details(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.OEDPPlugin.objects')
    def test_details_plugin_not_exist(self, mock_objects):
        """测试插件不存在"""
        mock_objects.get.side_effect = OEDPPlugin.DoesNotExist
        
        request = self.factory.get('/v1.0/artifacts/details/')
        request.query_params = {'key': 'nonexistent', 'tag': ArtifactTag.OEDP}
        self.viewset.request = request
        
        response = self.viewset.details(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.download_plugin')
    def test_download_plugin_missing_key(self, mock_download):
        """测试下载插件缺少key参数"""
        mock_download.return_value = {'is_success': False, 'message': 'Key is None'}
        
        request = self.factory.post('/v1.0/artifacts/download_plugin/')
        request.query_params = {}
        self.viewset.request = request
        
        response = self.viewset.download_plugin(request)
        # 即使key为None，代码也会调用download_plugin并返回响应
        self.assertIsNotNone(response)

    @patch('artifacts.views.PluginMethods.download_plugin')
    def test_download_plugin_success(self, mock_download):
        """测试成功下载插件"""
        mock_download.return_value = {'is_success': True, 'message': 'Downloaded'}
        
        request = self.factory.post('/v1.0/artifacts/download_plugin/')
        request.query_params = {'key': 'test_plugin_1.0.0'}
        self.viewset.request = request
        
        response = self.viewset.download_plugin(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.delete_plugin')
    def test_delete_plugin_failed(self, mock_delete):
        """测试删除插件失败"""
        mock_delete.return_value = {'is_success': False, 'message': 'Delete failed'}
        
        request = self.factory.post('/v1.0/artifacts/delete_plugin/')
        request.query_params = {'key': 'test_plugin_1.0.0'}
        self.viewset.request = request
        
        response = self.viewset.delete_plugin(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.run_plugin_action')
    def test_plugin_action_success(self, mock_run_action):
        """测试成功执行插件action"""
        mock_run_action.return_value = {
            'is_success': True,
            'message': 'Action started',
            'task_name': 'test_task'
        }
        
        request = self.factory.post('/v1.0/artifacts/plugin_action/')
        request.query_params = {'key': 'test_plugin_1.0.0', 'action_name': 'install'}
        self.viewset.request = request
        
        response = self.viewset.plugin_action(request)
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.MCPMethods.mcp_package_action')
    def test_mcp_install_missing_key(self, mock_action):
        """测试安装MCP缺少key参数"""
        request = self.factory.post('/v1.0/artifacts/mcp_install/')
        request.query_params = {}
        self.viewset.request = request
        
        response = self.viewset.mcp_install(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.MCPMethods.mcp_package_action')
    def test_mcp_uninstall_success(self, mock_action):
        """测试成功卸载MCP"""
        mock_action.return_value = {
            'is_success': True,
            'message': 'Uninstalled',
            'status_code': 200
        }
        
        request = self.factory.post('/v1.0/artifacts/mcp_uninstall/')
        request.query_params = {'key': 'test_mcp_1.0.0'}
        self.viewset.request = request
        
        response = self.viewset.mcp_uninstall(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])

    def test_mcp_config_manage_missing_action(self):
        """测试MCP配置管理缺少action参数"""
        request = self.factory.post('/v1.0/artifacts/mcp_config_manage/')
        request.query_params = {}
        self.viewset.request = request
        
        response = self.viewset.mcp_config_manage(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.get_devstore_log')
    def test_log_devstore(self, mock_get_log):
        """测试获取DevStore日志"""
        mock_get_log.return_value = "Test log content"
        
        request = self.factory.get('/v1.0/artifacts/log/')
        request.query_params = {'key': 'DevStore'}
        self.viewset.request = request
        
        response = self.viewset.log(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])
        self.assertIn("log", response.data)

    @patch('artifacts.views.PluginMethods.get_plugin_log')
    def test_log_plugin(self, mock_get_log):
        """测试获取插件日志"""
        mock_get_log.return_value = (200, {
            'is_success': True,
            'message': 'Log fetched',
            'log': 'Plugin log content'
        })
        
        request = self.factory.get('/v1.0/artifacts/log/')
        request.query_params = {'key': 'test_plugin_1.0.0'}
        self.viewset.request = request
        
        response = self.viewset.log(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.sync_plugins')
    @patch('artifacts.views.MCPMethods.sync_mcps')
    def test_sync_plugin_only_success(self, mock_sync_mcps, mock_sync_plugins):
        """测试仅插件同步成功"""
        mock_sync_plugins.return_value = {'is_success': True}
        mock_sync_mcps.return_value = {'is_success': False}
        request = self.factory.post('/v1.0/artifacts/sync/')
        self.viewset.request = request
        response = self.viewset.sync(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Plugin data', response.data['message'])

    @patch('artifacts.views.PluginMethods.sync_plugins')
    @patch('artifacts.views.MCPMethods.sync_mcps')
    def test_sync_mcp_only_success(self, mock_sync_mcps, mock_sync_plugins):
        """测试仅MCP同步成功"""
        mock_sync_plugins.return_value = {'is_success': False}
        mock_sync_mcps.return_value = {'is_success': True}
        request = self.factory.post('/v1.0/artifacts/sync/')
        self.viewset.request = request
        response = self.viewset.sync(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('MCP service', response.data['message'])

    @patch('artifacts.views.PluginMethods.sync_plugins', side_effect=Exception("boom"))
    @patch('artifacts.views.MCPMethods.sync_mcps', return_value={'is_success': False})
    def test_sync_exception(self, mock_mcp, mock_plugin):
        """测试同步异常"""
        request = self.factory.post('/v1.0/artifacts/sync/')
        self.viewset.request = request
        with self.assertRaises(Exception):
            self.viewset.sync(request)

    @patch('artifacts.views.process_search_with_relevance')
    @patch('artifacts.views.ArtifactSerializer')
    @patch('artifacts.views.OEDPPlugin.objects')
    @patch('artifacts.views.MCPServer.objects')
    def test_list_success_oedp(self, mock_mcp_objects, mock_plugin_objects, mock_serializer, mock_process):
        """测试获取插件列表成功"""
        mock_plugin_objects.count.return_value = 2
        mock_mcp_objects.count.return_value = 1
        mock_queryset = MagicMock()
        mock_queryset.count.return_value = 2
        mock_process.return_value = mock_queryset

        request = self.factory.get('/v1.0/artifacts/')
        request.query_params = {'tag': ArtifactTag.OEDP, 'searchValue': 'test', 'sort': 'rec'}
        self.viewset.request = request

        self.viewset.paginate_queryset = MagicMock(return_value=['obj'])
        mock_response = Response({'results': [{'id': 1}]})
        self.viewset.get_paginated_response = MagicMock(return_value=mock_response)
        mock_serializer.return_value.data = [{'id': 1}]

        response = self.viewset.list(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])
        self.assertEqual(response.data['data']['oedp_count'], 2)

    @patch('artifacts.views.MCPDetailSerializer')
    @patch('artifacts.views.MCPServer.objects')
    def test_details_mcp_success(self, mock_objects, mock_serializer):
        """测试获取MCP详情成功"""
        mock_mcp = MagicMock()
        mock_objects.get.return_value = mock_mcp
        mock_serializer.return_value.data = {'id': 1}

        request = self.factory.get('/v1.0/artifacts/details/')
        request.query_params = {'key': 'mcp-key', 'tag': ArtifactTag.MCP, 'user_name': 'root'}
        self.viewset.request = request

        response = self.viewset.details(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])
        mock_serializer.assert_called_once_with(mock_mcp, 'root')

    @patch('artifacts.views.PluginDetailSerializer')
    @patch('artifacts.views.OEDPPlugin.objects')
    def test_details_plugin_success(self, mock_objects, mock_serializer):
        """测试获取插件详情成功"""
        mock_plugin = MagicMock()
        mock_objects.get.return_value = mock_plugin
        mock_serializer.return_value.data = {'id': 2}

        request = self.factory.get('/v1.0/artifacts/details/')
        request.query_params = {'key': 'plugin-key', 'tag': ArtifactTag.OEDP}
        self.viewset.request = request

        response = self.viewset.details(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])
        mock_serializer.assert_called_once_with(mock_plugin)

    @patch('artifacts.views.PluginMethods.run_plugin_action')
    def test_plugin_action_failed(self, mock_run_action):
        """测试执行插件action失败"""
        mock_run_action.return_value = {'is_success': False, 'message': 'failed'}

        request = self.factory.post('/v1.0/artifacts/plugin_action/')
        request.query_params = {'key': 'test', 'action_name': 'install'}
        self.viewset.request = request

        response = self.viewset.plugin_action(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.MCPMethods.mcp_package_action')
    def test_mcp_uninstall_missing_key(self, mock_action):
        """测试卸载MCP缺少key"""
        request = self.factory.post('/v1.0/artifacts/mcp_uninstall/')
        request.query_params = {}
        self.viewset.request = request

        response = self.viewset.mcp_uninstall(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])
        mock_action.assert_not_called()

    @patch('artifacts.views.MCPMethods.mcp_package_action')
    def test_mcp_install_custom_status(self, mock_action):
        """测试安装MCP自定义状态码"""
        mock_action.return_value = {'is_success': True, 'status_code': 202}

        request = self.factory.post('/v1.0/artifacts/mcp_install/')
        request.query_params = {'key': 'mcp'}
        self.viewset.request = request

        response = self.viewset.mcp_install(request)
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.MCPMethods.mcp_package_action')
    def test_mcp_install_fail(self, mock_action):
        """测试安装MCP失败"""
        mock_action.return_value = {'is_success': False, 'status_code': 500}
        request = self.factory.post('/v1.0/artifacts/mcp_install/')
        request.query_params = {'key': 'mcp'}
        self.viewset.request = request
        response = self.viewset.mcp_install(request)
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.data['is_success'])

    def test_mcp_config_manage_missing_package(self):
        """测试MCP配置管理缺少package_name"""
        request = self.factory.post('/v1.0/artifacts/mcp_config_manage/')
        request.query_params = {'action': 'add', 'app_name': 'app', 'user_name': 'root'}
        self.viewset.request = request

        response = self.viewset.mcp_config_manage(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.manage_mcp_config')
    def test_mcp_config_manage_success(self, mock_manage):
        """测试MCP配置管理成功"""
        mock_manage.return_value = {'is_success': True, 'status_code': 201}
        request = self.factory.post('/v1.0/artifacts/mcp_config_manage/')
        request.query_params = {
            'action': 'add',
            'package_name': 'pkg',
            'app_name': 'app',
            'user_name': 'root'
        }
        self.viewset.request = request

        response = self.viewset.mcp_config_manage(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['is_success'])

    def test_mcp_config_manage_missing_app(self):
        """测试MCP配置缺少app参数"""
        request = self.factory.post('/v1.0/artifacts/mcp_config_manage/')
        request.query_params = {'action': 'add', 'package_name': 'pkg', 'user_name': 'root'}
        self.viewset.request = request
        response = self.viewset.mcp_config_manage(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.set_plugin_config')
    def test_plugin_config_set(self, mock_set):
        """测试设置插件配置"""
        mock_set.return_value = (201, {'is_success': True})
        request = self.factory.get('/v1.0/artifacts/plugin_config/')
        request.query_params = {'key': 'p', 'operation': 'set', 'config_text': 'demo'}
        self.viewset.request = request

        response = self.viewset.plugin_config(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.reset_plugin_config')
    def test_plugin_config_reset(self, mock_reset):
        """测试重置插件配置"""
        mock_reset.return_value = (202, {'is_success': True})
        request = self.factory.get('/v1.0/artifacts/plugin_config/')
        request.query_params = {'key': 'p', 'operation': 'reset'}
        self.viewset.request = request

        response = self.viewset.plugin_config(request)
        self.assertEqual(response.status_code, 202)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.get_plugin_config')
    def test_plugin_config_get(self, mock_get):
        """测试获取插件配置"""
        mock_get.return_value = (200, {'is_success': True, 'config': {}})
        request = self.factory.get('/v1.0/artifacts/plugin_config/')
        request.query_params = {'key': 'p'}
        self.viewset.request = request

        response = self.viewset.plugin_config(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])

    def test_plugin_config_default_get(self):
        """测试插件配置默认获取"""
        with patch('artifacts.views.PluginMethods.get_plugin_config', return_value=(200, {'is_success': True})) as mock_get:
            request = self.factory.get('/v1.0/artifacts/plugin_config/')
            request.query_params = {'key': 'p', 'operation': 'get'}
            self.viewset.request = request
            response = self.viewset.plugin_config(request)
            self.assertEqual(response.status_code, 200)
            mock_get.assert_called_once()

    @patch('artifacts.views.PluginMethods.get_plugin_log')
    def test_log_plugin_failed(self, mock_get_log):
        """测试获取插件日志失败"""
        mock_get_log.return_value = (400, {'is_success': False, 'message': 'fail'})

        request = self.factory.get('/v1.0/artifacts/log/')
        request.query_params = {'key': 'p'}
        self.viewset.request = request

        response = self.viewset.log(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.Task.objects')
    def test_task_info_success(self, mock_objects):
        """测试查询任务信息成功"""
        mock_task = MagicMock()
        mock_task.name = 't'
        mock_task.type = 'install'
        mock_task.status = 'done'
        mock_task.msg = 'ok'
        mock_objects.get.return_value = mock_task
        request = self.factory.get('/v1.0/artifacts/task_info/')
        request.query_params = {'task_name': 't'}
        self.viewset.request = request
        response = self.viewset.task_info(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.Task.objects')
    def test_task_info_not_found(self, mock_objects):
        """测试查询任务不存在"""
        mock_objects.get.side_effect = Task.DoesNotExist
        request = self.factory.get('/v1.0/artifacts/task_info/')
        request.query_params = {'task_name': 'missing'}
        self.viewset.request = request
        response = self.viewset.task_info(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.download_plugin')
    def test_download_plugin_task(self, mock_download):
        """测试下载插件返回任务"""
        mock_download.return_value = {'is_success': True, 'task_name': 't'}
        request = self.factory.post('/v1.0/artifacts/download_plugin/')
        request.query_params = {'key': 'k'}
        self.viewset.request = request
        response = self.viewset.download_plugin(request)
        self.assertEqual(response.status_code, 202)

    @patch('artifacts.views.PluginMethods.delete_plugin')
    def test_delete_plugin_success(self, mock_delete):
        """测试删除插件成功"""
        mock_delete.return_value = {'is_success': True}
        request = self.factory.post('/v1.0/artifacts/delete_plugin/')
        request.query_params = {'key': 'k'}
        self.viewset.request = request
        response = self.viewset.delete_plugin(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_success'])

    @patch('artifacts.views.PluginMethods.run_plugin_action')
    def test_plugin_action_bad_request(self, mock_run_action):
        """测试action返回400"""
        mock_run_action.return_value = {'is_success': False, 'message': 'bad'}
        request = self.factory.post('/v1.0/artifacts/plugin_action/')
        request.query_params = {'key': 'k', 'action_name': 'a'}
        self.viewset.request = request
        response = self.viewset.plugin_action(request)
        self.assertEqual(response.status_code, 400)

    @patch('artifacts.views.PluginMethods.run_plugin_action')
    def test_plugin_action_success_200(self, mock_run_action):
        """测试action成功无任务"""
        mock_run_action.return_value = {'is_success': True, 'message': 'ok'}
        request = self.factory.post('/v1.0/artifacts/plugin_action/')
        request.query_params = {'key': 'k', 'action_name': 'a'}
        self.viewset.request = request
        response = self.viewset.plugin_action(request)
        self.assertEqual(response.status_code, 200)

    @patch('artifacts.views.manage_mcp_config', return_value={'is_success': False, 'status_code': 500})
    def test_mcp_config_manage_failed(self, mock_manage):
        """测试MCP配置管理失败"""
        request = self.factory.post('/v1.0/artifacts/mcp_config_manage/')
        request.query_params = {
            'action': 'add',
            'package_name': 'pkg',
            'app_name': 'app',
            'user_name': 'root'
        }
        self.viewset.request = request
        response = self.viewset.mcp_config_manage(request)
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.data['is_success'])


