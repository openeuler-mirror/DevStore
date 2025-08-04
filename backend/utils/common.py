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
