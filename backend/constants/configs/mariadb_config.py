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

import json
from configparser import MissingSectionHeaderError, ParsingError

from constants.paths import MARIADB_CONFIG_FILE, MARIADB_JSON_FILE
from utils.cipher import CustomCipher
from utils.file_handler.base_handler import FileError
from utils.file_handler.conf_handler import ConfHandler
from utils.logger import init_log

__all__ = ['MariaDBConfig', 'get_settings_mariadb_config']
run_logger = init_log("run.log")


class MariaDBConfig:
    NAME = ''
    HOST = ''
    PORT = ''
    USER = ''
    PASSWORD = ''


try:
    conf_handler = ConfHandler(file_path=MARIADB_CONFIG_FILE, logger=run_logger)
except (FileError, MissingSectionHeaderError, ParsingError):
    pass
else:
    MariaDBConfig.NAME = conf_handler.get('mariadb', 'name', default='')
    MariaDBConfig.HOST = conf_handler.get('mariadb', 'host', default='')
    MariaDBConfig.PORT = conf_handler.get('mariadb', 'port', default='')
    MariaDBConfig.USER = conf_handler.get('mariadb', 'user', default='')
    MariaDBConfig.PASSWORD = conf_handler.get('mariadb', 'password', default='')


def get_settings_mariadb_config():
    with open(MARIADB_JSON_FILE, mode='r') as fr_handle:
        ciphertext_data = json.load(fr_handle)
    custom_cipher = CustomCipher()
    plaintext = custom_cipher.decrypt_ciphertext_data(ciphertext_data)
    database_config = {
        'NAME': MariaDBConfig.NAME,
        'HOST': MariaDBConfig.HOST,
        'PORT': MariaDBConfig.PORT,
        'USER': MariaDBConfig.USER,
        'PASSWORD': plaintext,
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'init_command': 'SET sql_mode="STRICT_TRANS_TABLES"',
            'charset': 'utf8',
            'autocommit': True
        },
        'TEST': {
            'CHARSET': 'utf8',
            'COLLATION': 'utf8_bin'
        }
    }
    del plaintext
    return database_config
