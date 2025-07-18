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
import re

from rest_framework import serializers

from artifacts.models import MCPService, Plugin
from constants.choices import ArtifactTag
from constants.paths import PLUGIN_CACHE_DIR
from tasks.models import Task
from utils.cmd_executor import CommandExecutor
from utils.common import is_process_running
from utils.logger import init_log

logger = init_log('run.log')


class ArtifactSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    version = serializers.CharField()
    author = serializers.CharField()
    description = serializers.CharField()
    icon = serializers.CharField()
    updated_at = serializers.DateTimeField()
    tag = serializers.SerializerMethodField()

    @staticmethod
    def get_tag(obj):
        if isinstance(obj, MCPService):
            return ArtifactTag.MCP
        elif isinstance(obj, Plugin):
            return ArtifactTag.OEDP
        else:
            return ''


class MCPDetailSerializer(serializers.ModelSerializer):
    tag = serializers.SerializerMethodField()
    installed_status = serializers.SerializerMethodField()
    
    class Meta:
        model = MCPService
        fields = (
            'id',
            'name',
            'version',
            'description',
            'readme',
            'tag',
            'installed_status',
        )

    @staticmethod
    def get_tag(obj):
        return ArtifactTag.MCP

    @staticmethod
    def get_installed_status(obj):
        if is_process_running(f'yum install -y {obj.package_name}'):
            return Task.Status.IN_PROCESS
        cmd = ['rpm', '-q', obj.package_name]
        cmd_executor = CommandExecutor(cmd)
        _, _, code = cmd_executor.run()
        if code != 0:
            return Task.Status.NOT_YET
        return Task.Status.SUCCESS


class PluginDetailSerializer(serializers.ModelSerializer):
    tag = serializers.SerializerMethodField()
    download_status = serializers.SerializerMethodField()

    class Meta:
        model = Plugin
        fields = (
            'name',
            'version',
            'description',
            'readme',
            'tag',
            'download_status',
        )

    @staticmethod
    def get_tag(obj):
        return ArtifactTag.OEDP

    @staticmethod
    def get_download_status(obj):
        if is_process_running(f'oedp init {obj.name}'):
            return Task.Status.IN_PROCESS
        if os.path.exists(os.path.join(PLUGIN_CACHE_DIR, obj.name)):
            return Task.Status.SUCCESS
        return Task.Status.NOT_YET


class PluginListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        plugins = [Plugin(**item) for item in validated_data]
        Plugin.objects.bulk_create(plugins)
        return plugins


class PluginBulkCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plugin
        fields = (
            'name',
            'version',
            'updated_at',
            'description',
            'type',
            'sha256sum',
            'size',
            'icon',
            'download_url',
        )
        list_serializer_class = PluginListSerializer

    @staticmethod
    def validate_sha256sum(value):
        pattern = r'^[a-fA-F0-9]{64}$'
        if not re.fullmatch(pattern, value.strip()):
            msg = 'Invalid sha256sum checksum format.'
            logger.error(msg)
            raise serializers.ValidationError(msg)
        return value


class MCPListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        mcps = [MCPService(**item) for item in validated_data]
        MCPService.objects.bulk_create(mcps)
        return mcps


class MCPBulkCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = MCPService
        fields = (
            'name',
            'package_name',
            'version',
            'updated_at',
            'description',
            'size',
            'repo',
        )
        list_serializer_class = MCPListSerializer
