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
from django.db.models import UniqueConstraint, JSONField

from tasks.models import Task


class OEDPPlugin(models.Model):

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            UniqueConstraint(fields=['name', 'version'], name='unique_plugin_name_version')
        ]

    class Type(models.TextChoices):
        APP = "app", "application"

    def __str__(self):
        return self.name

    name = models.CharField("名称", max_length=1024)
    version = models.CharField("版本", max_length=256)
    key = models.CharField("数据库索引", max_length=2048)
    updated_at = models.DateTimeField("更新时间")
    url = models.CharField("代码仓url", max_length=2048, blank=True, null=True)
    type = models.CharField("类型", max_length=16, choices=Type.choices, default=Type.APP, help_text="保留字段，暂不生效")
    author = models.CharField("发布者", max_length=256, blank=True, null=True)
    description = JSONField("简介", default=dict, help_text="字典格式,key:语言,value:文本")
    readme = models.TextField("README文本", blank=True, null=True)
    icon = models.TextField("图标数据", blank=True, null=True)
    localhost_available = models.BooleanField("是否支持本地单节点部署", default=False)
    download_status = models.CharField("下载状态", max_length=256, default=Task.Status.NOT_YET)
    action_list = JSONField("部署操作列表", default=list, help_text="列表,每个元素包含name,title,description,status")


class MCPServer(models.Model):

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            UniqueConstraint(fields=['name', 'version'], name='unique_mcp_name_version')
        ]

    def __str__(self):
        return self.name

    name = models.CharField("名称", max_length=1024)
    package_name = models.CharField("软件包名称", max_length=1024)
    version = models.CharField("软件包版本", max_length=256)
    key = models.CharField("数据库索引", max_length=2048)
    updated_at = models.DateTimeField('更新时间')
    url = models.CharField("代码仓url", max_length=2048, blank=True, null=True)
    author = models.CharField("发布者", max_length=256, blank=True, null=True)
    description = JSONField("简介", default=dict, help_text="字典格式,key:语言,value:文本")
    readme = models.TextField("README文本", blank=True, null=True)
    icon = models.TextField("图标数据", blank=True, null=True)
    mcp_config = JSONField("MCP配置内容",default=dict, help_text="完整的 mcp_config.json 内容",blank=True, null=True)
