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
import base64
import glob
import gzip
import json
import os
import shutil
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree
import zstandard as zstd
from rest_framework import status
from artifacts.models import MCPServer
from artifacts.serializers import MCPBulkCreateSerializer
from artifacts.tasks.mcp_action_task import MCPPackageTask
from artifacts.utils import clear_table,check_system_rpm_installed
from constants.paths import CACHE_DIR, MCP_BASE_DIR
from tasks.scheduler import scheduler
from utils.common import is_process_running
from utils.logger import init_log
from utils.cmd_executor import CommandExecutor
from utils.time import timestamp2local

logger = init_log('run.log')

class MCPMethods:
    
    @staticmethod
    def sync_mcps() -> Dict[str, Any]:
        """同步MCP服务信息"""
        try:           
            mcp_data, message = MCPMethods._read_mcp_info()
            if mcp_data is None:
                return {'is_success': False, 'message': message}

            clear_table(MCPServer._meta.db_table)
            
            if mcp_data:
                serializer = MCPBulkCreateSerializer(data=mcp_data, many=True)
                if not serializer.is_valid():
                    return {'is_success': False, 'message': serializer.errors}
                
                mcps = serializer.save()
                msg = f"Successfully synced {len(mcps)} MCP packages"
            else:
                msg = "No MCP packages found, database cleared"
            
            return {'is_success': True, 'message': msg}
            
        except Exception as e:
            logger.error(f"Sync MCP failed: {str(e)}")
            return {'is_success': False, 'message': f'Sync failed: {str(e)}'}

    @staticmethod
    def _read_mcp_info() -> Tuple[Optional[List[Dict]], str]:
        """读取MCP信息并生成数据结构"""
        try:
            cached_folders  = MCPMethods.get_packages_info(CACHE_DIR)
            remote_packages = MCPMethods._parse_all_primary_xml()
            if not remote_packages:
                return [], "No MCP packages found in any repodata"

            all_packages = []
            packages_to_update = []

            # 创建name_version键列表
            remote_pkg_keys = [f"{pkg['name']}_{pkg['version']}" for pkg in remote_packages]
            
            # 转换为集合以便快速查找
            remote_pkg_set = set(remote_pkg_keys)
            cached_folders_set = set(cached_folders)

            # 清理本地有但远程没有的包
            folders_to_delete = cached_folders_set - remote_pkg_set
            for folder_name in folders_to_delete:
                cache_path = os.path.join(CACHE_DIR, folder_name)
                if os.path.exists(cache_path):
                    try:
                        shutil.rmtree(cache_path, ignore_errors=True)
                        logger.info(f"Deleted obsolete cache folder: {folder_name}")
                        if folder_name in cached_folders:
                            cached_folders.remove(folder_name)
                            cached_folders_set.remove(folder_name)
                    except Exception as delete_error:
                        logger.warning(f"Failed to delete {cache_path}: {delete_error}")

            # 分类处理包
            for pkg in remote_packages:
                pkg_folder_name = f"{pkg['name']}_{pkg['version']}"
                
                if pkg_folder_name in cached_folders_set:
                    all_packages.append(pkg)
                else:
                    packages_to_update.append(pkg)

            if packages_to_update:
                MCPMethods._process_packages_batch(packages_to_update)
                all_packages.extend(packages_to_update)

            for pkg in all_packages:
                MCPMethods._read_package_resources(pkg)
            if not all_packages:
                return [], "No MCP packages found or updated"
            else:
                return all_packages, 'Generate MCP service data successfully.'
            
        except Exception as e:
            logger.error(f"Failed to read MCP info: {str(e)}")
            return None, f"Failed to read MCP info: {str(e)}"

    @staticmethod
    def get_packages_info(directory: str) -> List[str]:
        packages = []       
        if not os.path.exists(directory):
            return packages
        for item in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, item)):
                packages.append(item)
        return packages

    @staticmethod
    def _get_valid_repo_cache_dirs() -> List[str]:
        """获取当前启用的repo的有效缓存目录"""
        try:
            enabled_repos = MCPMethods._get_enabled_repos()
            if not enabled_repos:
                return []
            
            logger.info(f"Found enabled repos: {enabled_repos}")
            
            valid_dirs = []
            for repo_id in enabled_repos:
                cache_dir = MCPMethods._find_latest_repo_cache(repo_id, enabled_repos)
                if cache_dir:
                    valid_dirs.append(cache_dir)
            
            logger.info(f"Total valid repo cache directories: {len(valid_dirs)}")
            return valid_dirs
            
        except Exception as e:
            logger.error(f"Failed to get valid repo cache dirs: {e}")
            return []

    @staticmethod
    def _get_enabled_repos() -> List[str]:
        """获取启用的repo列表"""
        cmd_executor = CommandExecutor(['dnf', 'repolist', '--enabled', '--quiet'], timeout=30)
        stdout, stderr, returncode = cmd_executor.run()
        
        if returncode != 0:
            logger.error(f"Failed to get enabled repos: {stderr}")
            return []
        
        enabled_repos = []
        lines = stdout.strip().split('\n')
        for line in lines[1:]:  # 跳过标题行
            if line.strip():
                repo_id = line.split()[0]  # 第一列是repo ID
                enabled_repos.append(repo_id)
        
        return enabled_repos

    @staticmethod
    def _find_latest_repo_cache(repo_id: str, enabled_repos: List[str]) -> str:
        """为指定repo找到最新的有效缓存目录"""
        cache_base = "/var/cache/dnf"
        pattern = f"{repo_id}-*"
        matching_paths = glob.glob(os.path.join(cache_base, pattern))
        
        # 过滤出有效的缓存目录
        matching_dirs = []
        for path in matching_paths:
            if MCPMethods._is_valid_repo_cache_dir(path, repo_id, enabled_repos):
                matching_dirs.append(path)
        
        if not matching_dirs:
            logger.warning(f"No cache directory found for enabled repo: {repo_id}")
            return ""
        
        # 选择最新修改的目录
        latest_dir = max(matching_dirs, key=lambda d: os.path.getmtime(d))
        
        # 验证repodata目录存在
        repodata_dir = os.path.join(latest_dir, "repodata")
        if not os.path.exists(repodata_dir):
            logger.warning(f"Repodata directory not found for repo '{repo_id}': {repodata_dir}")
            return ""
        
        logger.info(f"Found valid cache for repo '{repo_id}': {latest_dir}")
        return latest_dir

    @staticmethod
    def _is_valid_repo_cache_dir(path: str, repo_id: str, enabled_repos: List[str]) -> bool:
        """检查目录是否是指定repo的有效缓存目录"""
        if not os.path.isdir(path):
            return False
        
        dir_name = os.path.basename(path)
        
        # 必须以 "repo_id-" 开头
        if not dir_name.startswith(repo_id + '-'):
            return False
        
        # 提取hash部分
        suffix = dir_name[len(repo_id) + 1:]
        if not suffix:  # hash部分不能为空
            return False
        
        # repo缓存目录的hash通常是长的字母数字字符串，不包含有意义的单词
        if '-' in suffix:
            # 如果suffix包含连字符，检查第一部分的特征
            first_part = suffix.split('-')[0]
            # hash的第一部分通常较长(>=6字符)且包含数字和字母随机混合
            if len(first_part) < 6 or first_part.isalpha():
                return False
        
        return True

    @staticmethod
    def _parse_all_primary_xml() -> List[Dict[str, Any]]:
        """从有效的repodata解析MCP包"""
        # 获取有效的repo缓存目录
        valid_repo_dirs = MCPMethods._get_valid_repo_cache_dirs()
        if not valid_repo_dirs:
            logger.error("No valid repo cache directories found")
            return []

        # 在有效的repo目录中查找primary.xml文件
        matches = []
        for repo_dir in valid_repo_dirs:
            repo_matches = glob.glob(f"{repo_dir}/repodata/*-primary.xml.*")
            matches.extend(repo_matches)
            
        if not matches:
            logger.error("No primary.xml files found in valid repodata")
            return []

        logger.info(f"Found {len(matches)} valid repodata files to scan from {len(valid_repo_dirs)} enabled repos")

        all_packages = {}
        for xml_file in matches:
            logger.info(f"Scanning repodata file: {xml_file}")
            packages = MCPMethods._parse_single_primary_xml(xml_file)
            for pkg in packages:
                pkg_name = pkg['name']
                pkg_version = pkg['version']
                if pkg_name not in all_packages:
                    all_packages[pkg_name] = {}
                all_packages[pkg_name][pkg_version] = pkg

        final_packages = []
        for pkg_versions in all_packages.values():
            final_packages.extend(pkg_versions.values())
    
        logger.info(f"Found {len(final_packages)} packages across valid repodata")
        return final_packages

    @staticmethod
    def _parse_single_primary_xml(primary_file: str) -> List[Dict[str, Any]]:
        """解析单个primary.xml文件，只提取MCP包"""
        output_file = primary_file.replace('.gz', '').replace('.zst', '')
        
        # 解压文件 - 支持gzip和zstd格式
        try:
            if primary_file.endswith('.gz'):
                with gzip.open(primary_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            elif primary_file.endswith('.zst'):
                dctx = zstd.ZstdDecompressor()
                with open(primary_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
                    dctx.copy_stream(f_in, f_out)
        except Exception as e:
            logger.error(f"Failed to extract {primary_file}: {e}")
            return []

        packages = []
        try:
            tree = ElementTree.parse(output_file)
            root = tree.getroot()
            namespace = {'common': 'http://linux.duke.edu/metadata/common'}

            for package in root.findall('common:package', namespace):
                package_name_elem = package.find('common:name', namespace)                  
                package_name = package_name_elem.text.strip()
                if not package_name.startswith('mcp-servers') or package_name == 'mcp-servers':
                    continue

                try:
                    version_elem = package.find('common:version', namespace)
                    time_elem = package.find('common:time', namespace)
                    desc_elem = package.find('common:description', namespace)
                    url_elem = package.find('common:url', namespace) 
                    arch_elem = package.find('common:arch', namespace)

                    name = package_name.removeprefix('mcp-servers-')
                    ver = version_elem.get('ver')
                    rel = version_elem.get('rel')
                    clean_rel = rel.split('.')[0] if rel else "1"
                    version_str = f"{ver}-{clean_rel}"
                    arch = arch_elem.text if arch_elem is not None else 'noarch'
                    download_tag = f"{package_name}-{ver}-{rel}.{arch}"

                    packages.append({
                        'package_name': package_name,
                        'name': name,
                        'version': version_str,
                        'updated_at': timestamp2local(int(time_elem.get('file'))),
                        'key': f"{name}_{version_str}",
                        'description': {'default': desc_elem.text if desc_elem is not None and desc_elem.text else ''},
                        'url': url_elem.text if url_elem is not None else '' ,
                        'download_tag': download_tag
                    })
                except Exception as e:
                    logger.error(f"Failed to parse {package_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to parse XML {output_file}: {e}")
        finally:
            # 清理临时文件
            if os.path.exists(output_file) and output_file != primary_file:
                try:
                    os.remove(output_file)
                except:
                    pass

        return packages

    @staticmethod
    def _process_packages_batch(packages: List[Dict]) -> List[Dict]:
        """批量处理需要更新的包"""
        # 批量下载
        download_tags = [pkg['download_tag'] for pkg in packages if 'download_tag' in pkg]
        rpm_dir = os.path.join(MCP_BASE_DIR, "rpm_packages")
        os.makedirs(rpm_dir, exist_ok=True)
        
        cmd = ['dnf', 'download', '--downloaddir', rpm_dir] + download_tags
        executor = CommandExecutor(cmd, timeout=300)
        stdout, stderr, returncode = executor.run()
        if returncode != 0:
            logger.error(f"Download failed: {stderr}")
            return []

        processed = []
        for pkg in packages:
            try:
                # 找RPM文件
                rpm_file = None
                
                for filename in os.listdir(rpm_dir):
                    if (filename.startswith(pkg['package_name']) and pkg['version'] in filename and filename.endswith('.rpm')):
                        rpm_file = os.path.join(rpm_dir, filename)
                        break
                if not rpm_file:
                    continue
                
                # 解压
                if MCPMethods._extract_rpm_package(pkg, rpm_file):
                    processed.append(pkg)
                # 删除临时RPM文件
                try:
                    os.remove(rpm_file)
                except Exception:
                    pass
                
            except Exception as e:
                logger.error(f"Failed to process {pkg['name']}: {e}")
        return processed

    @staticmethod
    def _extract_rpm_package(pkg: Dict, rpm_file: str) -> bool:
        """解压RPM包到缓存目录"""
        # 使用包含版本信息的缓存目录
        cache_dir = os.path.join(CACHE_DIR, f"{pkg['name']}_{pkg['version']}")
        
        # 重建缓存目录
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
        os.makedirs(cache_dir, exist_ok=True)
        
        # 解压RPM
        cmd = ['bash', '-c', f"cd '{cache_dir}' && rpm2cpio '{rpm_file}' | cpio -idm --quiet './opt/*'"]
        executor = CommandExecutor(cmd, timeout=120)
        stdout, stderr, returncode = executor.run()
        if returncode != 0:
            logger.error(f"Download failed: {stderr}")
            return []

    @staticmethod
    def _read_package_resources(pkg: Dict) -> bool:
        """从缓存目录读取包的资源文件"""
        cache_dir = os.path.join(CACHE_DIR, f"{pkg['name']}_{pkg['version']}")
        
        if not os.path.exists(cache_dir):
            logger.error(f"Cache directory not found for {pkg['name']}: {cache_dir}")
            return False
        
        readme = ""
        icon = ""
        mcp_config = {}
        
        # 读取资源文件
        base_path = os.path.join(cache_dir, 'opt', 'mcp-servers', 'servers')
        
        try:
            if not os.path.exists(base_path):
                logger.warning(f"Base path not found: {base_path}")
                return False
                
            for server_dir in os.listdir(base_path):
                server_path = os.path.join(base_path, server_dir, 'src')
                
                # 读取readme
                readme_path = os.path.join(server_path, 'readme.md')
                if os.path.exists(readme_path):
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        readme = f.read()
                    logger.debug(f"Read README for {pkg['name']}")
                
                # 读取icon
                icon_path = os.path.join(server_path, 'icon.png')
                if os.path.exists(icon_path):
                    with open(icon_path, 'rb') as f:
                        icon = base64.b64encode(f.read()).decode('utf-8')
                    logger.debug(f"Read icon for {pkg['name']}")
                
                # 读取配置
                config_path = os.path.join(base_path, server_dir, 'mcp_config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        mcp_config = json.load(f)
                    logger.debug(f"Read config for {pkg['name']}")
                
                break  
                
        except Exception as e:
            logger.error(f"Failed to read resources for {pkg['name']}: {e}")
            return False
        
        # 更新包信息
        pkg['readme'] = readme
        pkg['icon'] = icon
        pkg['mcp_config'] = mcp_config
        
        return True

    @staticmethod
    def mcp_package_action(key: str, action: str)-> Dict[str, Any]:
        """执行MCP包操作（安装/卸载）"""
        logger.info(f"Start {action} MCP package with key: {key}")
        
        try:
            # 验证action参数
            if action not in ['install', 'uninstall']:
                msg = f"Invalid action: {action}. Must be 'install' or 'uninstall'."
                logger.error(msg)
                return {'is_success': False, 'message': msg, 'status_code': status.HTTP_400_BAD_REQUEST}
            
            # 查询包信息
            try:
                mcp_server = MCPServer.objects.get(key=key)
            except MCPServer.DoesNotExist:
                msg = f"MCP package with key [{key}] does not exist."
                logger.error(msg)
                return {'is_success': False, 'message': msg, 'status_code': status.HTTP_404_NOT_FOUND}
            
            # 检查当前安装状态
            is_installed = check_system_rpm_installed(mcp_server.package_name)
            
            if action == 'install':
                if is_installed:
                    msg = f"MCP package [{mcp_server.name}] is already installed"
                    logger.info(msg)
                    return {'is_success': True, 'message': msg, 'status_code': status.HTTP_200_OK}
            
            elif action == 'uninstall':
                if not is_installed:
                    msg = f"MCP package [{mcp_server.name}] is not installed"
                    logger.info(msg)
                    return {'is_success': True, 'message': msg,'status_code': status.HTTP_200_OK}

            task_identifier = f"mcp_{action}_{key}_task"
            
            if is_process_running(task_identifier, timeout=600):
                msg = f"MCP package [{mcp_server.name}] {action} task is already running."
                logger.error(msg)
                return {'is_success': False, "message": msg, 'status_code': status.HTTP_409_CONFLICT}
            
            # 启动任务
            logger.info(f"Start to run MCP package [{mcp_server.name}] {action}.")
            mcp_task = MCPPackageTask(mcp_server, action, name=task_identifier)
            scheduler.add_task(mcp_task)
            
            msg = f"MCP package [{mcp_server.name}] {action} started."
            logger.info(msg)
            return {'is_success': True, 'message': msg, 'task_name': mcp_task.name,'status_code': status.HTTP_202_ACCEPTED}
        except Exception as e:
            logger.error(f"Unexpected error in mcp_package_action for key [{key}]: {str(e)}")
        return {
            'is_success': False,
            'message': f"Internal server error occurred while processing package [{key}]",
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
        }





