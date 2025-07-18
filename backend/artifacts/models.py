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
from django.db.models import UniqueConstraint


class Plugin(models.Model):

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            UniqueConstraint(fields=['name', 'version'], name='unique_plugin_name_version')
        ]

    class Type(models.TextChoices):
        APP = "app", "application"

    def __str__(self):
        return self.name

    name = models.CharField(
        "插件名称",
        max_length=1024,
        help_text="允许插件名称中带有版本号，表示软件本身的版本，而非插件的版本。"
    )
    version = models.CharField(
        "插件版本",
        max_length=256,
        help_text="注意该版本为插件版本，非部署软件版本"
    )
    updated_at = models.DateTimeField("插件更新时间")
    description = models.CharField("插件描述", max_length=2048)
    type = models.CharField(
        "插件类型",
        max_length=16,
        choices=Type.choices,
        default=Type.APP,
        help_text="保留字段，暂不生效"
    )
    sha256sum = models.CharField(
        "插件校验码",
        max_length=1024,
        help_text="插件 sha256sum 校验码"
    )
    size = models.PositiveBigIntegerField(
        "插件大小",
        help_text="插件大小，单位为 Bytes"
    )
    author = models.CharField("插件作者", max_length=256, blank=True, null=True)
    can_be_deployed_local = models.BooleanField(
        "是否支持本地单节点部署",
        default=False,
        help_text="该插件是否支持单节点部署以及是否支持和 oeDeploy 部署在同一节点"
    )
    repo = models.CharField("插件代码仓库链接", max_length=2048, blank=True, null=True)
    readme = models.CharField("README 文件链接", max_length=2048, blank=True, null=True)
    icon = models.CharField("插件图标链接", max_length=2048, blank=True, null=True)
    download_url = models.CharField("插件下载链接", max_length=2048, blank=True, null=True)


class MCPService(models.Model):

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            UniqueConstraint(fields=['name', 'version'], name='unique_mcp_name_version')
        ]

    def __str__(self):
        return self.name

    name = models.CharField("MCP 服务名称", max_length=1024)
    package_name = models.CharField("MCP 服务软件包名称", max_length=1024)
    version = models.CharField("MCP 服务软件包版本", max_length=256)
    updated_at = models.DateTimeField('MCP 服务更新时间')
    author = models.CharField("MCP 服务发布者", max_length=256, blank=True, null=True)
    description = models.CharField("MCP 服务描述", max_length=2048)
    size = models.PositiveBigIntegerField(
        "MCP 服务包大小",
        help_text="MCP 服务包大小，单位为 Bytes"
    )
    repo = models.CharField("MCP 服务代码仓库链接", max_length=2048, blank=True, null=True)
    readme = models.CharField("MCP 服务 README 文件链接", max_length=2048, blank=True, null=True)
    icon = models.CharField("MCP 服务图标链接", max_length=2048)
