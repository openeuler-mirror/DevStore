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

from django.db import models


class Task(models.Model):

    class Type(models.TextChoices):
        MCP_INSTALL = 'MI', 'mcp install'
        MCP_UNINSTALL = 'MU', 'mcp uninstall'
        PLUGIN_DOWNLOAD = 'PD', 'plugin download'
        PLUGIN_REMOVE = 'PR', 'plugin remove'
        PLUGIN_ACTION = 'PA', 'plugin action'


    class Status(models.TextChoices):
        NOT_YET = 'not yet', 'not yet'
        IN_PROCESS = 'in process', 'in process'
        SUCCESS = 'success', 'success'
        FAIL = 'fail', 'fail'

    name = models.CharField('任务名称', max_length=128, unique=True)
    type = models.CharField('任务类型', max_length=8, choices=Type.choices)
    status = models.CharField('任务状态', max_length=16, choices=Status.choices)
    msg = models.CharField('任务信息', max_length=256)
    created_at = models.DateTimeField('任务创建时间', auto_now_add=True)
