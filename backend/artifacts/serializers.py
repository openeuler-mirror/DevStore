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

from artifacts.models import MCPServer, OEDPPlugin
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
    key = serializers.CharField()
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    author = serializers.CharField()
    description = serializers.JSONField()
    icon = serializers.CharField()
    tag = serializers.SerializerMethodField()

    @staticmethod
    def get_tag(obj):
        if isinstance(obj, MCPServer):
            return ArtifactTag.MCP
        elif isinstance(obj, OEDPPlugin):
            return ArtifactTag.OEDP
        else:
            return ''


class PluginDetailSerializer(serializers.ModelSerializer):
    tag = serializers.SerializerMethodField()
    cmd_list = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = OEDPPlugin
        fields = (
            'id',
            'name',
            'version',
            'key',
            'tag',
            'updated_at',
            'url',
            'type',
            'author',
            'description',
            'readme',
            'icon',
            'localhost_available',
            'cmd_list',
            'download_status',
            'action_list',
        )

    @staticmethod
    def get_tag(obj):
        return ArtifactTag.OEDP
    
    @staticmethod
    def get_cmd_list(obj):
        cmd_list = [
            f"oedp init {obj.name} -d ~",
            f"vim ~/{obj.name}/config.yaml",
            f"oedp run install -p ~/{obj.name}"
        ]
        return cmd_list


class MCPDetailSerializer(serializers.ModelSerializer):
    tag = serializers.SerializerMethodField()
    installed_status = serializers.SerializerMethodField()
    cmd_list = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    
    class Meta:
        model = MCPServer
        fields = (
            'id',
            'name',
            'package_name',
            'version',
            'key',
            'tag',
            'updated_at',
            'url',
            'author',
            'description',
            'readme',
            'icon',
            'cmd_list',
            'installed_status',
            'app_list',
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
    
    @staticmethod
    def get_cmd_list(obj):
        cmd_list = [
            f"sudo yum install -y {obj.package_name}"
        ]
        return cmd_list


class PluginListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        plugins = [OEDPPlugin(**item) for item in validated_data]
        OEDPPlugin.objects.bulk_create(plugins)
        return plugins


class PluginBulkCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = OEDPPlugin
        fields = (
            'name',
            'version',
            'key',
            'updated_at',
            'url',
            'type',
            'author',
            'description',
            'readme',
            'icon',
            'localhost_available',
            'download_status',
            'action_list',
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
        mcps = [MCPServer(**item) for item in validated_data]
        MCPServer.objects.bulk_create(mcps)
        return mcps


class MCPBulkCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = MCPServer
        fields = (
            'name',
            'package_name',
            'version',
            'key',
            'updated_at',
            'url',
            'author',
            'description',
            'readme',
            'icon',
            'app_list',
        )
        list_serializer_class = MCPListSerializer


class PluginItemSerializer(serializers.ModelSerializer):
    """
    单个OEDPPlugin实例的序列化器，支持更新操作
    """
    def update(self, instance, validated_data):
        """
        更新OEDPPlugin实例
        :param instance: 要更新的OEDPPlugin实例
        :param validated_data: 已验证的数据
        :return: 更新后的OEDPPlugin实例
        """
        # 更新所有允许修改的字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    class Meta:
        model = OEDPPlugin
        fields = (
            'name',
            'version',
            'key',
            'updated_at',
            'url',
            'type',
            'author',
            'description',
            'readme',
            'icon',
            'localhost_available',
            'download_status',
            'action_list',
        )
