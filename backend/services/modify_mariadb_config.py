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

import sys

if "/var/lib/dev-store/src" not in sys.path:
    sys.path.append("/var/lib/dev-store/src")

from constants.paths import MARIADB_CONFIG_FILE
from utils.file_handler.conf_handler import ConfHandler


if __name__ == '__main__':
    try:
        database_name = sys.argv[1]
        conf_handler = ConfHandler(file_path=MARIADB_CONFIG_FILE, should_print=True)
        conf_handler.set('mariadb', 'name', database_name)
        conf_handler.save()
    except Exception as ex:
        print(ex)
        sys.exit(1)
