#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from artifacts.methods.mcp_methods import MCPMethods
from artifacts.models import MCPServer


class TestMCPMethods(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_get_packages_info_empty(self):
        """测试获取空目录的包信息"""
        result = MCPMethods.get_packages_info(self.test_dir)
        self.assertEqual(result, [])

    def test_get_packages_info_with_packages(self):
        """测试获取包含包的目录信息"""
        pkg1 = os.path.join(self.test_dir, "package1_1.0.0")
        pkg2 = os.path.join(self.test_dir, "package2_2.0.0")
        os.makedirs(pkg1)
        os.makedirs(pkg2)
        
        result = MCPMethods.get_packages_info(self.test_dir)
        self.assertEqual(len(result), 2)
        self.assertIn("package1_1.0.0", result)
        self.assertIn("package2_2.0.0", result)

    def test_get_packages_info_nonexistent(self):
        """测试获取不存在目录的包信息"""
        result = MCPMethods.get_packages_info("/nonexistent/path")
        self.assertEqual(result, [])

    @patch('artifacts.methods.mcp_methods.CommandExecutor')
    def test_get_enabled_repos(self, mock_executor):
        """测试获取启用的仓库列表"""
        mock_instance = MagicMock()
        mock_instance.run.return_value = (
            "repo id                  repo name\nrepo1                    Test Repo 1\nrepo2                    Test Repo 2",
            "", 0
        )
        mock_executor.return_value = mock_instance
        
        result = MCPMethods._get_enabled_repos()
        self.assertEqual(len(result), 2)
        self.assertIn("repo1", result)
        self.assertIn("repo2", result)

    @patch('artifacts.methods.mcp_methods.CommandExecutor')
    def test_get_enabled_repos_failed(self, mock_executor):
        """测试获取仓库列表失败"""
        mock_instance = MagicMock()
        mock_instance.run.return_value = ("", "Error", 1)
        mock_executor.return_value = mock_instance
        
        result = MCPMethods._get_enabled_repos()
        self.assertEqual(result, [])

    def test_is_valid_repo_cache_dir_not_dir(self):
        """测试非目录路径"""
        test_file = os.path.join(self.test_dir, "not_a_dir")
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = MCPMethods._is_valid_repo_cache_dir(test_file, "repo1", ["repo1"])
        self.assertFalse(result)

    def test_is_valid_repo_cache_dir_wrong_prefix(self):
        """测试错误的前缀"""
        test_dir = os.path.join(self.test_dir, "wrong-prefix-123abc")
        os.makedirs(test_dir)
        
        result = MCPMethods._is_valid_repo_cache_dir(test_dir, "repo1", ["repo1"])
        self.assertFalse(result)

    def test_is_valid_repo_cache_dir_no_suffix(self):
        """测试没有后缀的目录名"""
        test_dir = os.path.join(self.test_dir, "repo1-")
        os.makedirs(test_dir)
        
        result = MCPMethods._is_valid_repo_cache_dir(test_dir, "repo1", ["repo1"])
        self.assertFalse(result)

    def test_is_valid_repo_cache_dir_valid(self):
        """测试有效的缓存目录"""
        test_dir = os.path.join(self.test_dir, "repo1-abc123def")
        os.makedirs(test_dir)
        
        result = MCPMethods._is_valid_repo_cache_dir(test_dir, "repo1", ["repo1"])
        self.assertTrue(result)

    @patch('artifacts.methods.mcp_methods.CommandExecutor')
    def test_extract_rpm_package(self, mock_executor):
        """测试解压RPM包"""
        mock_instance = MagicMock()
        mock_instance.run.return_value = ("", "", 0)
        mock_executor.return_value = mock_instance
        
        pkg = {
            'name': 'test-pkg',
            'version': '1.0.0'
        }
        
        with patch('artifacts.methods.mcp_methods.CACHE_DIR', self.test_dir):
            result = MCPMethods._extract_rpm_package(pkg, "/path/to/test.rpm")
            # 函数返回None（实际代码没有明确返回值）
            self.assertIsNone(result)

    @patch('artifacts.methods.mcp_methods.MCPMethods._get_valid_repo_cache_dirs')
    def test_parse_all_primary_xml_no_repos(self, mock_get_dirs):
        """测试没有有效仓库的情况"""
        mock_get_dirs.return_value = []
        
        result = MCPMethods._parse_all_primary_xml()
        self.assertEqual(result, [])

    @patch('artifacts.methods.mcp_methods.MCPMethods._get_valid_repo_cache_dirs')
    @patch('glob.glob')
    def test_parse_all_primary_xml_no_files(self, mock_glob, mock_get_dirs):
        """测试没有primary.xml文件的情况"""
        mock_get_dirs.return_value = ["/var/cache/dnf/test-repo"]
        mock_glob.return_value = []
        
        result = MCPMethods._parse_all_primary_xml()
        self.assertEqual(result, [])

    @patch('artifacts.methods.mcp_methods.MCPServer.objects')
    def test_mcp_package_action_invalid_action(self, mock_objects):
        """测试无效的操作类型"""
        result = MCPMethods.mcp_package_action("test_key", "invalid_action")
        self.assertFalse(result['is_success'])
        self.assertIn("Invalid action", result['message'])

    @patch('artifacts.methods.mcp_methods.MCPServer.objects')
    def test_mcp_package_action_not_exist(self, mock_objects):
        """测试操作不存在的MCP包"""
        mock_objects.get.side_effect = MCPServer.DoesNotExist
        
        result = MCPMethods.mcp_package_action("nonexistent_key", "install")
        self.assertFalse(result['is_success'])
        self.assertIn("does not exist", result['message'])

    @patch('artifacts.methods.mcp_methods.MCPServer.objects')
    @patch('artifacts.methods.mcp_methods.check_system_rpm_installed')
    def test_mcp_package_action_already_installed(self, mock_check, mock_objects):
        """测试安装已安装的包"""
        mock_mcp = MagicMock()
        mock_mcp.name = "test-mcp"
        mock_mcp.package_name = "mcp-servers-test"
        mock_objects.get.return_value = mock_mcp
        mock_check.return_value = True
        
        result = MCPMethods.mcp_package_action("test_key", "install")
        self.assertTrue(result['is_success'])
        self.assertIn("already installed", result['message'])

    @patch('artifacts.methods.mcp_methods.MCPServer.objects')
    @patch('artifacts.methods.mcp_methods.check_system_rpm_installed')
    def test_mcp_package_action_not_installed_uninstall(self, mock_check, mock_objects):
        """测试卸载未安装的包"""
        mock_mcp = MagicMock()
        mock_mcp.name = "test-mcp"
        mock_mcp.package_name = "mcp-servers-test"
        mock_objects.get.return_value = mock_mcp
        mock_check.return_value = False
        
        result = MCPMethods.mcp_package_action("test_key", "uninstall")
        self.assertTrue(result['is_success'])
        self.assertIn("not installed", result['message'])

    @patch('artifacts.methods.mcp_methods.MCPServer.objects')
    @patch('artifacts.methods.mcp_methods.check_system_rpm_installed')
    @patch('artifacts.methods.mcp_methods.is_process_running')
    def test_mcp_package_action_already_running(self, mock_running, mock_check, mock_objects):
        """测试任务已在运行"""
        mock_mcp = MagicMock()
        mock_mcp.name = "test-mcp"
        mock_mcp.package_name = "mcp-servers-test"
        mock_objects.get.return_value = mock_mcp
        mock_check.return_value = False
        mock_running.return_value = True
        
        result = MCPMethods.mcp_package_action("test_key", "install")
        self.assertFalse(result['is_success'])
        self.assertIn("already running", result['message'])

    def test_read_package_resources_not_exist(self):
        """测试读取不存在的包资源"""
        pkg = {
            'name': 'nonexistent',
            'version': '1.0.0'
        }
        
        with patch('artifacts.methods.mcp_methods.CACHE_DIR', self.test_dir):
            result = MCPMethods._read_package_resources(pkg)
            self.assertFalse(result)

    def test_read_package_resources_no_base_path(self):
        """测试缺少基础路径的包"""
        cache_dir = os.path.join(self.test_dir, "test_1.0.0")
        os.makedirs(cache_dir)
        
        pkg = {
            'name': 'test',
            'version': '1.0.0'
        }
        
        with patch('artifacts.methods.mcp_methods.CACHE_DIR', self.test_dir):
            result = MCPMethods._read_package_resources(pkg)
            self.assertFalse(result)

    @patch('artifacts.methods.mcp_methods.MCPBulkCreateSerializer')
    @patch('artifacts.methods.mcp_methods.clear_table')
    @patch('artifacts.methods.mcp_methods.MCPMethods._read_mcp_info')
    def test_sync_mcps_success(self, mock_read, mock_clear, mock_serializer_cls):
        """测试同步MCP成功"""
        mock_read.return_value = ([{'name': 'a', 'version': '1', 'package_name': 'mcp-servers-a', 'key': 'a_1', 'updated_at': MagicMock(), 'description': {}, 'url': '', 'readme': '', 'icon': '', 'mcp_config': {}}], 'ok')
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = [MagicMock()]
        mock_serializer_cls.return_value = mock_serializer

        result = MCPMethods.sync_mcps()
        self.assertTrue(result['is_success'])
        mock_clear.assert_called()
        mock_serializer.save.assert_called_once()

    @patch('artifacts.methods.mcp_methods.clear_table')
    @patch('artifacts.methods.mcp_methods.MCPMethods._read_mcp_info')
    def test_sync_mcps_read_failed(self, mock_read, mock_clear):
        """测试读取失败同步MCP"""
        mock_read.return_value = (None, 'fail')
        result = MCPMethods.sync_mcps()
        self.assertFalse(result['is_success'])
        mock_clear.assert_called()

    @patch('artifacts.methods.mcp_methods.MCPMethods._parse_all_primary_xml')
    @patch('artifacts.methods.mcp_methods.MCPMethods.get_packages_info')
    def test_read_mcp_info_no_remote(self, mock_cache, mock_parse):
        """测试无远程包"""
        mock_cache.return_value = []
        mock_parse.return_value = []
        data, msg = MCPMethods._read_mcp_info()
        self.assertEqual(data, [])
        self.assertIn("No MCP packages", msg)

    @patch('artifacts.methods.mcp_methods.shutil.rmtree')
    @patch('artifacts.methods.mcp_methods.os.path.exists')
    @patch('artifacts.methods.mcp_methods.MCPMethods._parse_all_primary_xml')
    @patch('artifacts.methods.mcp_methods.MCPMethods.get_packages_info')
    def test_read_mcp_info_clean_obsolete(self, mock_cache, mock_parse, mock_exists, mock_rmtree):
        """测试清理过期缓存"""
        mock_cache.return_value = ['old_1.0']
        mock_parse.return_value = [{'name': 'pkg', 'version': '1.0', 'download_tag': 'd', 'key': 'pkg_1.0'}]
        mock_exists.return_value = True
        with patch('artifacts.methods.mcp_methods.MCPMethods._process_packages_batch', return_value=None):
            with patch('artifacts.methods.mcp_methods.MCPMethods._read_package_resources', return_value=True):
                data, _ = MCPMethods._read_mcp_info()
                self.assertEqual(len(data), 1)
                mock_rmtree.assert_called()

    @patch('artifacts.methods.mcp_methods.CommandExecutor')
    def test_process_packages_batch_download_fail(self, mock_exec):
        """测试批量处理下载失败"""
        mock_exec.return_value.run.return_value = ("", "err", 1)
        res = MCPMethods._process_packages_batch([{'download_tag': 'a', 'package_name': 'p', 'name': 'n', 'version': '1'}])
        self.assertEqual(res, [])

    @patch('artifacts.methods.mcp_methods.CommandExecutor')
    def test_process_packages_batch_no_rpm(self, mock_exec):
        """测试找不到RPM文件"""
        mock_exec.return_value.run.return_value = ("", "", 0)
        with patch('artifacts.methods.mcp_methods.os.listdir', return_value=[]):
            res = MCPMethods._process_packages_batch([{'download_tag': 'a', 'package_name': 'p', 'name': 'n', 'version': '1'}])
            self.assertEqual(res, [])

    @patch('artifacts.methods.mcp_methods.CommandExecutor')
    def test_extract_rpm_package_failed(self, mock_exec):
        """测试解压失败"""
        mock_exec.return_value.run.return_value = ("", "err", 1)
        pkg = {'name': 'n', 'version': '1'}
        with patch('artifacts.methods.mcp_methods.CACHE_DIR', self.test_dir):
            ok = MCPMethods._extract_rpm_package(pkg, '/tmp/a.rpm')
            self.assertFalse(ok)

    def test_read_package_resources_success(self):
        """测试成功读取资源"""
        cache_dir = os.path.join(self.test_dir, "srv_1")
        base = os.path.join(cache_dir, 'opt', 'mcp-servers', 'servers', 'demo', 'src')
        os.makedirs(base, exist_ok=True)
        with open(os.path.join(base, 'readme.md'), 'w') as f:
            f.write("readme")
        with open(os.path.join(base, 'icon.png'), 'wb') as f:
            f.write(b'123')
        config_path = os.path.join(cache_dir, 'opt', 'mcp-servers', 'servers', 'demo', 'mcp_config.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump({"a": 1}, f)

        pkg = {'name': 'srv', 'version': '1'}
        with patch('artifacts.methods.mcp_methods.CACHE_DIR', self.test_dir):
            ok = MCPMethods._read_package_resources(pkg)
            self.assertTrue(ok)
            self.assertEqual(pkg['mcp_config'], {"a": 1})

    @patch('artifacts.methods.mcp_methods.is_process_running')
    @patch('artifacts.methods.mcp_methods.scheduler')
    @patch('artifacts.methods.mcp_methods.MCPServer.objects')
    @patch('artifacts.methods.mcp_methods.check_system_rpm_installed')
    def test_mcp_package_action_install_start(self, mock_check, mock_objects, mock_scheduler, mock_running):
        """测试启动安装任务"""
        mock_running.return_value = False
        mock_check.return_value = False
        mock_mcp = MagicMock()
        mock_mcp.name = 'demo'
        mock_mcp.package_name = 'pkg'
        mock_objects.get.return_value = mock_mcp

        res = MCPMethods.mcp_package_action('k', 'install')
        self.assertTrue(res['is_success'])
        mock_scheduler.add_task.assert_called_once()

    @patch('artifacts.methods.mcp_methods.is_process_running')
    @patch('artifacts.methods.mcp_methods.MCPServer.objects')
    @patch('artifacts.methods.mcp_methods.check_system_rpm_installed')
    def test_mcp_package_action_uninstall_not_running(self, mock_check, mock_objects, mock_running):
        """测试卸载未安装包"""
        mock_running.return_value = False
        mock_check.return_value = False
        mock_mcp = MagicMock()
        mock_mcp.name = 'demo'
        mock_mcp.package_name = 'pkg'
        mock_objects.get.return_value = mock_mcp

        res = MCPMethods.mcp_package_action('k', 'uninstall')
        self.assertTrue(res['is_success'])
        self.assertIn('not installed', res['message'])

    @patch('artifacts.methods.mcp_methods.is_process_running')
    @patch('artifacts.methods.mcp_methods.MCPServer.objects')
    @patch('artifacts.methods.mcp_methods.check_system_rpm_installed')
    def test_mcp_package_action_conflict(self, mock_check, mock_objects, mock_running):
        """测试任务冲突"""
        mock_check.return_value = False
        mock_running.return_value = True
        mock_mcp = MagicMock()
        mock_mcp.name = 'demo'
        mock_mcp.package_name = 'pkg'
        mock_objects.get.return_value = mock_mcp

        res = MCPMethods.mcp_package_action('k', 'install')
        self.assertFalse(res['is_success'])
        self.assertEqual(res['status_code'], 409)

    @patch('artifacts.methods.mcp_methods.MCPServer.objects')
    def test_mcp_package_action_exception(self, mock_objects):
        """测试异常返回"""
        mock_objects.get.side_effect = Exception("boom")
        res = MCPMethods.mcp_package_action('k', 'install')
        self.assertFalse(res['is_success'])
        self.assertEqual(res['status_code'], 500)

