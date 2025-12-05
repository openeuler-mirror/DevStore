#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from artifacts.utils import (
    clear_table,
    set_plugin_action_status,
    update_plugin_action_list,
    get_plugin_action_list,
    update_plugin_status,
    get_devstore_log,
    check_system_rpm_installed,
    calculate_weighted_relevance,
    process_search_with_relevance
)
from django.db import connection
from tasks.models import Task


class TestUtils(unittest.TestCase):

    def test_set_plugin_action_status(self):
        """测试设置插件action状态"""
        action_list = [
            {"name": "install", "status": Task.Status.NOT_YET},
            {"name": "uninstall", "status": Task.Status.NOT_YET}
        ]
        set_plugin_action_status(action_list, "install", Task.Status.IN_PROCESS)
        self.assertEqual(action_list[0]["status"], Task.Status.IN_PROCESS)
        self.assertEqual(action_list[1]["status"], Task.Status.NOT_YET)

    def test_set_plugin_action_status_not_found(self):
        """测试设置不存在的action状态"""
        action_list = [
            {"name": "install", "status": Task.Status.NOT_YET}
        ]
        set_plugin_action_status(action_list, "nonexistent", Task.Status.SUCCESS)
        # 应该不报错，只是找不到对应的action
        self.assertEqual(action_list[0]["status"], Task.Status.NOT_YET)

    @patch('artifacts.utils.is_process_running')
    def test_get_plugin_action_list(self, mock_is_running):
        """测试获取插件action列表"""
        mock_is_running.return_value = False
        
        plugin = MagicMock()
        plugin.key = "test_plugin_1.0.0"
        
        with patch('artifacts.utils.PLUGIN_CACHE_DIR', '/tmp/test_cache'):
            with patch('builtins.open', mock_open(read_data='action:\n  install:\n    title: "安装"\n    description: "安装插件"')):
                action_list = get_plugin_action_list(plugin)
                self.assertIsInstance(action_list, list)

    @patch('artifacts.utils.is_process_running')
    @patch('builtins.open', mock_open(read_data='action:\n  install:\n    title: "安装"\n    description: "安装插件"'))
    def test_get_plugin_action_list_with_running_process(self, mock_is_running):
        """测试获取运行中的插件action列表"""
        mock_is_running.return_value = True
        
        plugin = MagicMock()
        plugin.key = "test_plugin_1.0.0"
        plugin.name = "test_plugin"
        
        with patch('artifacts.utils.PLUGIN_CACHE_DIR', '/tmp/test_cache'):
            action_list = get_plugin_action_list(plugin)
            self.assertIsInstance(action_list, list)

    @patch('artifacts.utils.CommandExecutor')
    def test_check_system_rpm_installed_success(self, mock_executor):
        """测试检查已安装的RPM包"""
        mock_instance = MagicMock()
        mock_instance.run.return_value = ("", "", 0)
        mock_executor.return_value = mock_instance
        
        result = check_system_rpm_installed("test-package")
        self.assertTrue(result)

    @patch('artifacts.utils.CommandExecutor')
    def test_check_system_rpm_installed_not_found(self, mock_executor):
        """测试检查未安装的RPM包"""
        mock_instance = MagicMock()
        mock_instance.run.return_value = ("", "", 1)
        mock_executor.return_value = mock_instance
        
        result = check_system_rpm_installed("nonexistent-package")
        self.assertFalse(result)

    @patch('artifacts.utils.CommandExecutor')
    def test_check_system_rpm_installed_exception(self, mock_executor):
        """测试RPM检查异常情况"""
        mock_executor.side_effect = Exception("Command failed")
        
        result = check_system_rpm_installed("test-package")
        self.assertFalse(result)

    def test_get_devstore_log_nonexistent(self):
        """测试不存在的日志文件"""
        with patch('artifacts.utils.LOG_DIR', '/nonexistent/path'):
            log = get_devstore_log()
            self.assertEqual(log, "")

    def test_get_devstore_log_small_file(self):
        """测试小于100KB的日志文件"""
        test_content = "Test log content\n" * 100
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            with patch('artifacts.utils.LOG_DIR', os.path.dirname(temp_path)):
                with patch('os.path.join', return_value=temp_path):
                    log = get_devstore_log()
                    self.assertIn("Test log content", log)
        finally:
            os.unlink(temp_path)

    def test_process_search_with_relevance_empty(self):
        """测试空搜索关键词"""
        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        
        result = process_search_with_relevance(mock_queryset, "", sort='rec')
        self.assertIsNotNone(result)

    def test_process_search_with_relevance_with_keyword(self):
        """测试带关键词的搜索"""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        
        result = process_search_with_relevance(mock_queryset, "test keyword", sort='rec')
        self.assertIsNotNone(result)
        mock_queryset.filter.assert_called_once()

    def test_process_search_with_relevance_sort_new(self):
        """测试按时间排序"""
        mock_queryset = MagicMock()
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.annotate.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        
        result = process_search_with_relevance(mock_queryset, "test", sort='new')
        self.assertIsNotNone(result)

