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

import datetime
from zoneinfo import ZoneInfo

import pytz

from utils.cmd_executor import CommandExecutor


def get_time_zone():
    """
    获取系统时区，若获取失败则返回默认时区 Asia/Shanghai
    """
    default_time_zone = 'Asia/Shanghai'
    cmd = ['ls', '-l', '/etc/localtime']
    cmd_executor = CommandExecutor(cmd)
    stdout, _, return_code = cmd_executor.run()
    if return_code != 0:
        return default_time_zone

    contents = stdout.split('zoneinfo/')
    if len(contents) == 2:
        time_zone = contents[-1].strip()
        # 校验获取的时区是否合法
        try:
            pytz.timezone(time_zone)
        except pytz.UnknownTimeZoneError:
            return default_time_zone
        return time_zone
    return default_time_zone


def timestamp2local(timestamp):
    """
    将时间戳转换为本地时间
    """
    local_tz = ZoneInfo(get_time_zone())
    return datetime.datetime.fromtimestamp(int(timestamp), tz=local_tz).strftime("%Y-%m-%d %H:%M:%S%z")
