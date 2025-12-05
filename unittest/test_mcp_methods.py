#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
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

