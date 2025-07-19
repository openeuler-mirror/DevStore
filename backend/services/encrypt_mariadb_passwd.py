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

from constants.paths import MARIADB_JSON_FILE
from utils.cipher import CustomCipher
from utils.file_handler.json_handler import JSONHandler


if __name__ == '__main__':
    try:
        plaintext = sys.argv[1]
        custom_cipher = CustomCipher()
        ciphertext_data = custom_cipher.encrypt_plaintext(plaintext)
        json_handler = JSONHandler(file_path=MARIADB_JSON_FILE, should_print=True)
        json_handler.data.update(ciphertext_data)
        json_handler.save()
    except Exception as ex:
        print(ex)
        sys.exit(1)
