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
# Create: 2025-08-14
# ======================================================================================================================

from typing import Dict, Any
from rest_framework import status
from constants.paths import MCP_SCRIPT_PATH
from utils.cmd_executor import CommandExecutor
from utils.common import validate_executable_file



def manage_mcp_config(action: str, package_name: str, app_name: str, user_name: str) -> Dict[str, Any]:
    """管理MCP配置（添加或删除）"""
    if action not in ["add", "delete"]:
        return {
            "is_success": False,
            "message": "Invalid action type",
            "status_code": status.HTTP_400_BAD_REQUEST
        }

    # 校验MCP脚本文件
    is_valid, error_msg = validate_executable_file(MCP_SCRIPT_PATH)
    if not is_valid:
        return {
            "is_success": False,
            "message": f"MCP script validation failed: {error_msg}",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }

    try:
        script_cmd = "add" if action == "add" else "del"
        cmd = [MCP_SCRIPT_PATH, script_cmd, package_name, app_name, user_name]
        executor = CommandExecutor(cmd, timeout=30)
        stdout, stderr, returncode = executor.run()
        
        if returncode == 0:  # 成功执行
            action_msg = "added" if action == "add" else "deleted"
            return {
                "is_success": True,
                "message": f"MCP config {action_msg} successfully",
                "status_code": status.HTTP_200_OK
            }
        else:  # 执行失败
            error_msg = stderr or stdout or "Operation failed"
            return {
                "is_success": False,
                "message": error_msg,
                "status_code": status.HTTP_400_BAD_REQUEST
            }
                
    except Exception as e:
        return {
            "is_success": False,
            "message": f"Operation error: {str(e)}",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
