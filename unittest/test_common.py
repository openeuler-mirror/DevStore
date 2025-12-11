#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock
import tempfile
import stat

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from utils.common import is_process_running, validate_executable_file


class TestCommonUtils(unittest.TestCase):

    @patch('utils.common.psutil.process_iter')
    def test_is_process_running_found(self, mock_process_iter):
        """测试找到包含关键字的进程"""
        # 模拟进程迭代器
        mock_proc1 = MagicMock()
        mock_proc1.info = {
            'pid': 1234,
            'name': 'python.exe',
            'cmdline': ['python', 'test_script.py'],
            'create_time': time.time() - 100  # 100秒前创建
        }
        
        mock_proc2 = MagicMock()
        mock_proc2.info = {
            'pid': 5678,
            'name': 'chrome.exe',
            'cmdline': ['chrome', '--test-mode'],
            'create_time': time.time() - 50  # 50秒前创建
        }
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2]
        
        # 测试找到进程
        result = is_process_running('python')
        self.assertTrue(result)
        
        result = is_process_running('chrome')
        self.assertTrue(result)
        
        result = is_process_running('test')
        self.assertTrue(result)  # 在cmdline中找到'test'

    @patch('utils.common.psutil.process_iter')
    def test_is_process_running_not_found(self, mock_process_iter):
        """测试未找到包含关键字的进程"""
        # 模拟进程迭代器
        mock_proc = MagicMock()
        mock_proc.info = {
            'pid': 1234,
            'name': 'python.exe',
            'cmdline': ['python', 'other_script.py'],
            'create_time': time.time() - 100
        }
        
        mock_process_iter.return_value = [mock_proc]
        
        # 测试未找到进程
        result = is_process_running('java')
        self.assertFalse(result)
        
        result = is_process_running('chrome')
        self.assertFalse(result)

    @patch('utils.common.psutil.process_iter')
    def test_is_process_running_timeout(self, mock_process_iter):
        """测试进程运行超时被忽略"""
        # 模拟进程迭代器，进程创建时间超过timeout
        mock_proc = MagicMock()
        mock_proc.info = {
            'pid': 1234,
            'name': 'python.exe',
            'cmdline': ['python', 'test_script.py'],
            'create_time': time.time() - 700  # 700秒前创建，超过默认600秒timeout
        }
        
        mock_process_iter.return_value = [mock_proc]
        
        # 测试超时进程被忽略
        result = is_process_running('python')
        self.assertFalse(result)
        
        # 测试自定义timeout
        result = is_process_running('python', timeout=800)
        self.assertTrue(result)  # 800秒timeout，进程创建700秒，应该找到

    @patch('utils.common.psutil.process_iter')
    def test_is_process_running_exception_handling(self, mock_process_iter):
        """测试进程迭代异常处理"""
        # 模拟进程迭代器抛出异常
        mock_proc = MagicMock()
        mock_proc.info.side_effect = Exception("Access denied")
        
        mock_process_iter.return_value = [mock_proc]
        
        # 测试异常被正确处理
        result = is_process_running('python')
        self.assertFalse(result)  # 异常被捕获，返回False

    @patch('utils.common.psutil.process_iter')
    def test_is_process_running_case_insensitive(self, mock_process_iter):
        """测试关键字大小写不敏感"""
        # 模拟进程迭代器
        mock_proc = MagicMock()
        mock_proc.info = {
            'pid': 1234,
            'name': 'PYTHON.EXE',  # 大写
            'cmdline': ['Python', 'TestScript.py'],  # 混合大小写
            'create_time': time.time() - 100
        }
        
        mock_process_iter.return_value = [mock_proc]
        
        # 测试大小写不敏感匹配
        result = is_process_running('python')
        self.assertTrue(result)
        
        result = is_process_running('PYTHON')
        self.assertTrue(result)
        
        result = is_process_running('testscript')
        self.assertTrue(result)

    def test_validate_executable_file_success(self):
        """测试验证有效的可执行文件"""
        # 创建临时文件并设置可执行权限
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            file_path = f.name
            # 在Windows上设置可执行权限
            if os.name == 'nt':
                # Windows没有os.X_OK，我们只需要文件存在
                os.chmod(file_path, stat.S_IREAD | stat.S_IWRITE)
            else:
                os.chmod(file_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        
        try:
            # 测试验证成功
            is_valid, error_msg = validate_executable_file(file_path)
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
        finally:
            # 清理临时文件
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_validate_executable_file_empty_path(self):
        """测试验证空文件路径"""
        is_valid, error_msg = validate_executable_file("")
        self.assertFalse(is_valid)
        self.assertEqual(error_msg, "文件路径不能为空")
        
        is_valid, error_msg = validate_executable_file(None)
        self.assertFalse(is_valid)
        self.assertEqual(error_msg, "文件路径不能为空")

    def test_validate_executable_file_not_exist(self):
        """测试验证不存在的文件"""
        non_existent_file = "/tmp/nonexistent_file_123456789"
        is_valid, error_msg = validate_executable_file(non_existent_file)
        self.assertFalse(is_valid)
        self.assertIn("文件不存在", error_msg)

    def test_validate_executable_file_not_a_file(self):
        """测试验证目录而不是文件"""
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            is_valid, error_msg = validate_executable_file(temp_dir)
            self.assertFalse(is_valid)
            self.assertIn("路径不是文件", error_msg)

    @unittest.skipIf(os.name == 'nt', "跳过Windows上的权限测试")
    def test_validate_executable_file_no_execute_permission(self):
        """测试验证没有可执行权限的文件（非Windows系统）"""
        # 创建临时文件但不设置可执行权限
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            file_path = f.name
            # 只设置读写权限，没有执行权限
            os.chmod(file_path, stat.S_IREAD | stat.S_IWRITE)
        
        try:
            # 测试验证失败
            is_valid, error_msg = validate_executable_file(file_path)
            self.assertFalse(is_valid)
            self.assertIn("文件没有可执行权限", error_msg)
        finally:
            # 清理临时文件
            if os.path.exists(file_path):
                os.unlink(file_path)

    def test_validate_executable_file_relative_path(self):
        """测试验证相对路径文件"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', dir='.', delete=False) as f:
            file_name = os.path.basename(f.name)
            # 在Windows上设置权限
            if os.name == 'nt':
                os.chmod(f.name, stat.S_IREAD | stat.S_IWRITE)
            else:
                os.chmod(f.name, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        
        try:
            # 测试相对路径
            is_valid, error_msg = validate_executable_file(file_name)
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
        finally:
            # 清理临时文件
            if os.path.exists(file_name):
                os.unlink(file_name)


if __name__ == '__main__':
    unittest.main()

