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
import time
import psutil


def is_process_running(keyword, timeout=600):
    """
    检查是否有进程的命令行或名称中包含指定关键字
    :param keyword: 要搜索的关键字（字符串）
    :return: True/False 表示是否找到匹配的进程
             如果进程运行超时(可能出现运行故障),则忽略
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            # 检查进程名或命令行参数中是否包含关键字
            if keyword.lower() in ' '.join(proc.info['cmdline']).lower() or \
                    keyword.lower() in proc.info['name'].lower():
                # 检查进程运行时间是否超过600秒
                if (time.time() - proc.info['create_time']) > timeout:
                    continue
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def validate_executable_file(file_path):
    """
    校验执行文件的存在性和可执行权限
    :param file_path: 要校验的文件路径
    :return: tuple (is_valid, error_message)
             is_valid: bool, 文件是否有效
             error_message: str, 错误信息（如果有）
    """
    if not file_path:
        return False, "文件路径不能为空"

    # 检查文件是否存在
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"

    # 检查是否为文件
    if not os.path.isfile(file_path):
        return False, f"路径不是文件: {file_path}"

    # 检查是否有可执行权限
    if not os.access(file_path, os.X_OK):
        return False, f"文件没有可执行权限: {file_path}"

    return True, ""
