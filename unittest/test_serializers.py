#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch

from artifacts.serializers import (
    ArtifactSerializer,
    MCPDetailSerializer,
    PluginDetailSerializer,
)
from artifacts.models import MCPServer, OEDPPlugin
from constants.choices import ArtifactTag
from tasks.models import Task


class TestSerializers(unittest.TestCase):

    def test_artifact_serializer_get_tag(self):
        """测试ArtifactSerializer获取标签"""
        mcp = MagicMock(spec=MCPServer)
        plugin = MagicMock(spec=OEDPPlugin)
        other = object()
        self.assertEqual(ArtifactSerializer.get_tag(mcp), ArtifactTag.MCP)
        self.assertEqual(ArtifactSerializer.get_tag(plugin), ArtifactTag.OEDP)
        self.assertEqual(ArtifactSerializer.get_tag(other), '')

    def test_plugin_detail_get_cmd_list(self):
        """测试插件命令列表"""
        plugin = MagicMock()
        plugin.name = "demo"
        cmd_list = PluginDetailSerializer.get_cmd_list(plugin)
        self.assertIn("oedp init demo -d ~", cmd_list)
        self.assertEqual(len(cmd_list), 3)

    @patch('artifacts.serializers.is_process_running')
    def test_mcp_detail_installed_status_running(self, mock_running):
        """测试MCP安装状态运行中"""
        mock_running.return_value = True
        mcp = MagicMock()
        mcp.package_name = "pkg"
        status = MCPDetailSerializer.get_installed_status(mcp)
        self.assertEqual(status, Task.Status.IN_PROCESS)

    @patch('artifacts.serializers.CommandExecutor')
    @patch('artifacts.serializers.is_process_running')
    def test_mcp_detail_installed_status_installed(self, mock_running, mock_executor):
        """测试MCP安装状态已安装"""
        mock_running.return_value = False
        mock_instance = MagicMock()
        mock_instance.run.return_value = ("", "", 0)
        mock_executor.return_value = mock_instance
        mcp = MagicMock()
        mcp.package_name = "pkg"
        status = MCPDetailSerializer.get_installed_status(mcp)
        self.assertEqual(status, Task.Status.SUCCESS)

    @patch('artifacts.serializers.CommandExecutor')
    @patch('artifacts.serializers.is_process_running')
    def test_mcp_detail_installed_status_not_installed(self, mock_running, mock_executor):
        """测试MCP安装状态未安装"""
        mock_running.return_value = False
        mock_instance = MagicMock()
        mock_instance.run.return_value = ("", "", 1)
        mock_executor.return_value = mock_instance
        mcp = MagicMock()
        mcp.package_name = "pkg"
        status = MCPDetailSerializer.get_installed_status(mcp)
        self.assertEqual(status, Task.Status.NOT_YET)

    @patch('artifacts.serializers.validate_executable_file', return_value=(True, ""))
    @patch('artifacts.serializers.CommandExecutor')
    def test_mcp_detail_get_app_list(self, mock_executor, mock_validate):
        """测试获取MCP应用列表"""
        mock_instance = MagicMock()
        mock_instance.run.return_value = ('[{"name":"a"}]', "", 0)
        mock_executor.return_value = mock_instance
        mcp = MagicMock()
        mcp.package_name = "pkg"
        serializer = MCPDetailSerializer(mcp, user_name='root')
        app_list = serializer.get_app_list(mcp)
        self.assertEqual(app_list, [{"name": "a"}])
        mock_validate.assert_called_once()

    def test_mcp_detail_get_cmd_list(self):
        """测试MCP命令列表"""
        mcp = MagicMock()
        mcp.package_name = "pkg"
        cmd_list = MCPDetailSerializer.get_cmd_list(mcp)
        self.assertEqual(cmd_list, ["sudo dnf install -y pkg"])


if __name__ == '__main__':
    unittest.main()

