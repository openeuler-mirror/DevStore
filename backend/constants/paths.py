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


# 配置文件目录
CONFIG_DIR = '/etc/dev-store'
# /etc/dev-store/task_scheduler.conf 任务调度器配置文件路径
TASK_SCHEDULER_CONFIG_FILE = os.path.join(CONFIG_DIR, 'task_scheduler.conf')

# 数据库文件目录
DB_DIR = '/var/lib/dev-store/db'
# /var/lib/dev-store/db/dev_store.db SQLite 数据库文件路径
SQLITE_DB_FILE = os.path.join(DB_DIR, 'dev_store.db')

# 日志目录
LOG_DIR = '/var/log/dev-store'

# 源码目录
SRC_DIR = '/var/lib/dev-store/src'
# /var/lib/dev-store/src/mcp_manage.sh MCP 管理脚本路径
MCP_SCRIPT_PATH = os.path.join(SRC_DIR, 'mcp_manage.sh')

# /etc/oedp/config/repo/cache OEDP 插件缓存目录
PLUGIN_REPO_DIR = '/etc/oedp/config/repo/cache'
# /etc/oedp/config/repo/details OEDP 插件配置信息缓存目录
REPO_DETAILS_DIR = '/var/oedp/details'
# MCP 服务缓存地址
CACHE_DIR = "/var/dev-store/mcp-assets"
# MCP 服务包存储地址
MCP_BASE_DIR ="/var/dev-store/mcp-save"
# 家目录
HOME_DIR = os.path.expanduser('~')
# 插件包缓存目录
PLUGIN_CACHE_DIR = os.path.join(HOME_DIR, '.oedp')
