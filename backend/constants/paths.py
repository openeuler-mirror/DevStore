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
# /etc/dev-store/mariadb/mariadb.conf MariaDB 配置文件路径
MARIADB_CONFIG_FILE = os.path.join(CONFIG_DIR, 'mariadb', 'mariadb.conf')
# /etc/dev-store/mariadb/mariadb_ciphertext_data.json MariaDB 密文数据 json 文件
MARIADB_JSON_FILE = os.path.join(CONFIG_DIR, 'mariadb', 'mariadb_ciphertext_data.json')
# /etc/dev-store/task_scheduler.conf 任务调度器配置文件路径
TASK_SCHEDULER_CONFIG_FILE = os.path.join(CONFIG_DIR, 'task_scheduler.conf')

# 日志目录
LOG_DIR = '/var/log/dev-store'

# /etc/oedp/config/repo/cache OEDP 插件缓存目录
PLUGIN_REPO_DIR = '/etc/oedp/config/repo/cache'
# /etc/oedp/config/repo/details OEDP 插件配置信息缓存目录
REPO_DETAILS_DIR = '/var/oedp/details'
# MCP 服务 repo 文件
MCP_REPO_FILE = '/etc/yum.repos.d/mcp.repo'
# 家目录
HOME_DIR = os.path.expanduser('~')
# 插件包缓存目录
PLUGIN_CACHE_DIR = os.path.join(HOME_DIR, '.oedp')

