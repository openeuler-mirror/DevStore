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
# Create: 2025-10-21
# ======================================================================================================================

import os
from constants.paths import SQLITE_DB_FILE

__all__ = ['get_settings_sqlite_config']


def get_settings_sqlite_config():
    """
    获取SQLite数据库配置
    """
    # 确保数据库文件所在目录存在
    db_dir = os.path.dirname(SQLITE_DB_FILE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, mode=0o755, exist_ok=True)
    
    database_config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SQLITE_DB_FILE,
        'OPTIONS': {
            'timeout': 20,
        },
        'TEST': {
            'NAME': ':memory:',
        }
    }
    
    return database_config
