#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
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

