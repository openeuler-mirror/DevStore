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

from configparser import MissingSectionHeaderError, ParsingError

from constants.paths import TASK_SCHEDULER_CONFIG_FILE
from utils.file_handler.base_handler import FileError
from utils.file_handler.conf_handler import ConfHandler
from utils.logger import init_log

run_logger = init_log("run.log")

# 默认值
MAX_CONCURRENCY = 10
try:
    conf_handler = ConfHandler(file_path=TASK_SCHEDULER_CONFIG_FILE, logger=run_logger)
except (FileError, MissingSectionHeaderError, ParsingError):
    pass
else:
    try:
        MAX_CONCURRENCY = conf_handler.getint('scheduler', 'max_concurrency', default=10)
    except ValueError as ex:
        run_logger.warning(f"Failed to get value of max_concurrency, error: {ex}")
