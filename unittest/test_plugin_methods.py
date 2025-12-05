#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
import tempfile
import shutil
import yaml
from unittest.mock import patch, MagicMock, mock_open
from artifacts.methods.plugin_methods import PluginMethods
from artifacts.models import OEDPPlugin
from tasks.models import Task


class TestPluginMethods(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.plugin_cache = os.path.join(self.test_dir, "plugin_cache")
        os.makedirs(self.plugin_cache)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('artifacts.methods.plugin_methods.OEDPPlugin.objects')
    def test_download_plugin_not_exist(self, mock_objects):
        """测试下载不存在的插件"""
        mock_objects.get.side_effect = OEDPPlugin.DoesNotExist
        
        result = PluginMethods.download_plugin("nonexistent_key")
        self.assertFalse(result['is_success'])
        self.assertIn("does not exist", result['message'])

    @patch('artifacts.methods.plugin_methods.OEDPPlugin.objects')
    def test_delete_plugin_not_exist(self, mock_objects):
        """测试删除不存在的插件"""
        mock_objects.get.side_effect = OEDPPlugin.DoesNotExist
        
        result = PluginMethods.delete_plugin("nonexistent_key")
        self.assertFalse(result['is_success'])
        self.assertIn("does not exist", result['message'])

    @patch('artifacts.methods.plugin_methods.OEDPPlugin.objects')
    @patch('artifacts.methods.plugin_methods.PLUGIN_CACHE_DIR')
    def test_delete_plugin_already_deleted(self, mock_cache_dir, mock_objects):
        """测试删除已删除的插件"""
        mock_cache_dir.return_value = self.plugin_cache
        
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.key = "test_plugin_1.0.0"
        mock_plugin.download_status = Task.Status.NOT_YET
        mock_objects.get.return_value = mock_plugin
        
        with patch('artifacts.methods.plugin_methods.update_plugin_status', return_value=True):
            result = PluginMethods.delete_plugin("test_plugin_1.0.0")
            self.assertTrue(result['is_success'])

    @patch('artifacts.methods.plugin_methods.OEDPPlugin.objects')
    def test_run_plugin_action_not_exist(self, mock_objects):
        """测试运行不存在插件的action"""
        mock_objects.get.side_effect = OEDPPlugin.DoesNotExist
        
        result = PluginMethods.run_plugin_action("nonexistent_key", "install")
        self.assertFalse(result['is_success'])
        self.assertIn("does not exist", result['message'])

    @patch('artifacts.methods.plugin_methods.OEDPPlugin.objects')
    def test_run_plugin_action_not_downloaded(self, mock_objects):
        """测试运行未下载插件的action"""
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.key = "test_plugin_1.0.0"
        mock_plugin.download_status = Task.Status.NOT_YET
        mock_objects.get.return_value = mock_plugin
        
        with patch('artifacts.methods.plugin_methods.PluginMethods._check_plugin_file_exist', return_value=False):
            result = PluginMethods.run_plugin_action("test_plugin_1.0.0", "install")
            self.assertFalse(result['is_success'])
            self.assertIn("not downloaded", result['message'])

    @patch('artifacts.methods.plugin_methods.OEDPPlugin.objects')
    def test_run_plugin_action_invalid_action(self, mock_objects):
        """测试运行不存在的action"""
        mock_plugin = MagicMock()
        mock_plugin.name = "test_plugin"
        mock_plugin.key = "test_plugin_1.0.0"
        mock_plugin.download_status = Task.Status.SUCCESS
        mock_plugin.action_list = [{"name": "install", "status": Task.Status.NOT_YET}]
        mock_objects.get.return_value = mock_plugin
        
        with patch('artifacts.methods.plugin_methods.PluginMethods._check_plugin_file_exist', return_value=True):
            result = PluginMethods.run_plugin_action("test_plugin_1.0.0", "nonexistent")
            self.assertFalse(result['is_success'])
            self.assertIn("has no action", result['message'])

    def test_check_plugin_file_exist_not_exist(self):
        """测试检查不存在的插件文件"""
        with patch('artifacts.methods.plugin_methods.PLUGIN_CACHE_DIR', self.plugin_cache):
            result = PluginMethods._check_plugin_file_exist("nonexistent_key")
            self.assertFalse(result)

    def test_check_plugin_file_exist_missing_files(self):
        """测试检查缺少必要文件的插件"""
        plugin_dir = os.path.join(self.plugin_cache, "test_plugin_1.0.0")
        os.makedirs(plugin_dir)
        
        # 只创建main.yaml，缺少config.yaml
        with open(os.path.join(plugin_dir, "main.yaml"), 'w') as f:
            f.write("test: data")
        
        with patch('artifacts.methods.plugin_methods.PLUGIN_CACHE_DIR', self.plugin_cache):
            result = PluginMethods._check_plugin_file_exist("test_plugin_1.0.0")
            self.assertFalse(result)

    def test_check_plugin_file_exist_complete(self):
        """测试检查完整的插件文件"""
        plugin_dir = os.path.join(self.plugin_cache, "test_plugin_1.0.0")
        os.makedirs(plugin_dir)
        
        # 创建所有必需文件
        with open(os.path.join(plugin_dir, "main.yaml"), 'w') as f:
            f.write("test: data")
        with open(os.path.join(plugin_dir, "config.yaml"), 'w') as f:
            f.write("config: data")
        os.makedirs(os.path.join(plugin_dir, "workspace"))
        
        with patch('artifacts.methods.plugin_methods.PLUGIN_CACHE_DIR', self.plugin_cache):
            result = PluginMethods._check_plugin_file_exist("test_plugin_1.0.0")
            self.assertTrue(result)

    @patch('artifacts.methods.plugin_methods.CommandExecutor')
    def test_update_plugin_info_oedp_not_installed(self, mock_executor):
        """测试oedp未安装情况"""
        mock_instance = MagicMock()
        mock_instance.run.return_value = ("", "", 1)
        mock_executor.return_value = mock_instance
        
        success, msg = PluginMethods._update_plugin_info()
        self.assertFalse(success)
        self.assertIn("not installed", msg)

    @patch('artifacts.methods.plugin_methods.CommandExecutor')
    def test_update_plugin_info_update_failed(self, mock_executor):
        """测试oedp repo update失败"""
        mock_instance = MagicMock()
        # 第一次调用返回成功（rpm -q），第二次返回失败（oedp repo update）
        mock_instance.run.side_effect = [("", "", 0), ("", "Update failed", 1)]
        mock_executor.return_value = mock_instance
        
        success, msg = PluginMethods._update_plugin_info()
        self.assertFalse(success)
        self.assertIn("Failed to execute", msg)

    def test_get_plugin_yaml_files_not_exist(self):
        """测试插件仓库目录不存在"""
        with patch('artifacts.methods.plugin_methods.PLUGIN_REPO_DIR', '/nonexistent/path'):
            yaml_files, msg = PluginMethods._get_plugin_yaml_files()
            self.assertIsNone(yaml_files)
            self.assertIn("not exists", msg)

    def test_get_plugin_yaml_files_not_dir(self):
        """测试插件仓库路径不是目录"""
        test_file = os.path.join(self.test_dir, "not_a_dir")
        with open(test_file, 'w') as f:
            f.write("test")
        
        with patch('artifacts.methods.plugin_methods.PLUGIN_REPO_DIR', test_file):
            yaml_files, msg = PluginMethods._get_plugin_yaml_files()
            self.assertIsNone(yaml_files)
            self.assertIn("not a directory", msg)

    def test_get_plugin_yaml_files_success(self):
        """测试成功获取yaml文件列表"""
        repo_dir = os.path.join(self.test_dir, "repo")
        os.makedirs(repo_dir)
        
        # 创建测试文件
        with open(os.path.join(repo_dir, "test1.yaml"), 'w') as f:
            f.write("test")
        with open(os.path.join(repo_dir, "test2.yml"), 'w') as f:
            f.write("test")
        with open(os.path.join(repo_dir, "test.txt"), 'w') as f:
            f.write("test")
        
        with patch('artifacts.methods.plugin_methods.PLUGIN_REPO_DIR', repo_dir):
            yaml_files, msg = PluginMethods._get_plugin_yaml_files()
            self.assertIsNotNone(yaml_files)
            self.assertEqual(len(yaml_files), 2)

    def test_get_plugin_readme_not_exist(self):
        """测试获取不存在的readme"""
        with patch('artifacts.methods.plugin_methods.REPO_DETAILS_DIR', self.test_dir):
            readme = PluginMethods._get_plugin_readme("nonexistent_plugin")
            self.assertEqual(readme, "")

    def test_get_plugin_readme_success(self):
        """测试成功获取readme"""
        plugin_dir = os.path.join(self.test_dir, "test_plugin_1.0.0", "doc")
        os.makedirs(plugin_dir)
        
        readme_content = "# Test Plugin\n\nThis is a test."
        with open(os.path.join(plugin_dir, "readme.md"), 'w') as f:
            f.write(readme_content)
        
        with patch('artifacts.methods.plugin_methods.REPO_DETAILS_DIR', self.test_dir):
            readme = PluginMethods._get_plugin_readme("test_plugin_1.0.0")
            self.assertEqual(readme, readme_content)

    def test_get_plugin_icon_not_exist(self):
        """测试获取不存在的图标"""
        with patch('artifacts.methods.plugin_methods.REPO_DETAILS_DIR', self.test_dir):
            icon = PluginMethods._get_plugin_icon("nonexistent_plugin")
            self.assertEqual(icon, "")

    def test_get_plugin_action_from_list_found(self):
        """测试从列表中找到action"""
        action_list = [
            {"name": "install", "status": Task.Status.NOT_YET},
            {"name": "uninstall", "status": Task.Status.NOT_YET}
        ]
        result = PluginMethods._get_plugin_action_from_list(action_list, "install")
        self.assertEqual(result["name"], "install")

    def test_get_plugin_action_from_list_not_found(self):
        """测试从列表中找不到action"""
        action_list = [
            {"name": "install", "status": Task.Status.NOT_YET}
        ]
        result = PluginMethods._get_plugin_action_from_list(action_list, "nonexistent")
        self.assertEqual(result, [])

    @patch('artifacts.methods.plugin_methods.PLUGIN_CACHE_DIR')
    def test_get_plugin_config_not_downloaded(self, mock_cache_dir):
        """测试获取未下载插件的配置"""
        mock_cache_dir.return_value = self.plugin_cache
        
        with patch('artifacts.methods.plugin_methods.PluginMethods._check_plugin_file_exist', return_value=False):
            status_code, result = PluginMethods.get_plugin_config("test_key")
            self.assertEqual(status_code, 400)
            self.assertFalse(result['is_success'])

    @patch('artifacts.methods.plugin_methods.PLUGIN_CACHE_DIR')
    def test_set_plugin_config_not_downloaded(self, mock_cache_dir):
        """测试设置未下载插件的配置"""
        mock_cache_dir.return_value = self.plugin_cache
        
        with patch('artifacts.methods.plugin_methods.PluginMethods._check_plugin_file_exist', return_value=False):
            status_code, result = PluginMethods.set_plugin_config("test_key", "config: test")
            self.assertEqual(status_code, 400)
            self.assertFalse(result['is_success'])

    @patch('artifacts.methods.plugin_methods.PLUGIN_CACHE_DIR')
    def test_reset_plugin_config_not_downloaded(self, mock_cache_dir):
        """测试重置未下载插件的配置"""
        mock_cache_dir.return_value = self.plugin_cache
        
        with patch('artifacts.methods.plugin_methods.PluginMethods._check_plugin_file_exist', return_value=False):
            status_code, result = PluginMethods.reset_plugin_config("test_key")
            self.assertEqual(status_code, 400)
            self.assertFalse(result['is_success'])

    @patch('artifacts.methods.plugin_methods.PLUGIN_CACHE_DIR')
    def test_get_plugin_log_not_downloaded(self, mock_cache_dir):
        """测试获取未下载插件的日志"""
        mock_cache_dir.return_value = self.plugin_cache
        
        with patch('artifacts.methods.plugin_methods.PluginMethods._check_plugin_file_exist', return_value=False):
            status_code, result = PluginMethods.get_plugin_log("test_key")
            self.assertEqual(status_code, 400)
            self.assertFalse(result['is_success'])

