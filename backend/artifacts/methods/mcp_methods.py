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
# Create: 2025-07-30
# ======================================================================================================================

import glob
import gzip
import shutil
from xml.etree import ElementTree

from artifacts.models import MCPServer
from artifacts.utils import clear_table
from utils.cmd_executor import CommandExecutor
from utils.logger import init_log
from utils.time import timestamp2local

logger = init_log('run.log')


class MCPMethods:

    @staticmethod
    def sync_mcps():
        """同步MCP服务信息"""
        # 更新 MCP 服务的信息
        update_result, msg = MCPMethods._update_mcp_info()
        if not update_result:
            return { 'is_success': False, 'message': msg }
        # 读取 MCP 服务的信息
        mcp_data, msg = MCPMethods._read_mcp_info()
        if not mcp_data:
            return { 'is_success': False, 'message': msg }
        # 将 MCP 服务的信息存入数据库中
        from artifacts.serializers import MCPBulkCreateSerializer
        serializer = MCPBulkCreateSerializer(data=mcp_data, many=True)
        clear_table(MCPServer._meta.db_table)
        if not serializer.is_valid():
            logger.error(f"Failed to validate MCP data, errors: {serializer.errors}")
            return { 'is_success': False, 'message': serializer.errors }
        mcps = serializer.save()
        msg = "Sync MCP data successfully."
        logger.info(msg)
        return { 'is_success': True, 'message': msg }

    @staticmethod
    def _update_mcp_info():
        """更新MCP仓库信息"""
        cmd = ['yum', 'makecache', '--disablerepo=*', '--enablerepo=mcp']
        logger.info(f"Start to execute command [{' '.join(cmd)}].")
        cmd_executor = CommandExecutor(cmd)
        _, stderr, code = cmd_executor.run()
        if code != 0:
            msg = f"Failed to execute command: [{' '.join(cmd)}]. Error: {stderr}"
            logger.error(msg)
            return False, msg
        msg = 'Update MCP repo successfully.'
        logger.info(msg)
        return True, msg

    @staticmethod
    def _read_mcp_info():
        """读取MCP信息并生成数据结构"""
        # 匹配 primary.xml.gz 文件
        logger.info('Start to match MCP meta file.')
        pattern = "/var/cache/dnf/mcp-*/repodata/*-primary.xml.gz"
        matches = glob.glob(pattern)
        if not matches:
            msg = "No match for *-primary.xml.gz."
            logger.error(msg)
            return [], msg
        primary_file = matches[0]
        logger.info(f"The MCP meta file: {primary_file}")

        # 开始解压 primary.xml.gz
        logger.info(f'Start to extract {primary_file}')
        output_file = primary_file.rstrip('.gz')
        try:
            with gzip.open(primary_file, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logger.info(f"extract successfully: {primary_file} -> {output_file}")
        except PermissionError:
            msg = "No permission."
            logger.error(msg)
            return [], msg
        except gzip.BadGzipFile:
            msg = f"{primary_file} is not a valid gzip format."
            logger.error(msg)
            return [], msg

        # 读取 primary.xml 文件，生成 MCP 服务信息列表
        logger.info("Start to read MCP information files and generate MCP data.")
        tree = ElementTree.parse(output_file)
        root = tree.getroot()
        namespace = {'common': 'http://linux.duke.edu/metadata/common'}
        mcp_data = []
        for package in root.findall('common:package', namespace):
            mcp_info = {}
            package_name = package.find('common:name', namespace).text.strip()
            if package_name == 'mcp-servers':
                continue
            else:
                mcp_info['package_name'] = package_name
                mcp_info['name'] = package_name.removeprefix('mcp-servers-')
            version = package.find('common:version', namespace)
            mcp_info['version'] = f"{version.get('ver')}-{version.get('rel')}"  # 暂未考虑epoch
            timestamp = package.find('common:time', namespace).get('file')
            mcp_info['updated_at'] = timestamp2local(int(timestamp))
            mcp_info['key'] = mcp_info['name'] + '_' + mcp_info['version']
            mcp_info['description'] = dict()
            mcp_info['description']['default'] = package.find('common:description', namespace).text
            mcp_info['size'] = int(package.find('common:size', namespace).get('package'))
            mcp_info['repo'] = package.find('common:url', namespace).text
            mcp_data.append(mcp_info)

        if not mcp_data:
            msg = f"Failed to read mcp information."
            logger.error(msg)
            return [], msg
        msg = 'Generate MCP service data successfully.'
        logger.info(msg)
        return mcp_data, msg
