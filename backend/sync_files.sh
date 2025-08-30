#!/usr/bin/env bash
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

# only for debug

set -e

SCRIPT_DIR=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
cd ${SCRIPT_DIR}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  --clean    清理并删除所有拷贝的文件"
    echo "  -h, --help 显示此帮助信息"
}

# 清理函数
clean_files() {
    echo "开始清理拷贝的文件..."
    
    # 删除配置文件
    if [ -d /etc/dev-store ]; then
        echo "删除 /etc/dev-store 目录"
        rm -rf /etc/dev-store
    fi
    
    # 删除日志目录
    if [ -d /var/log/dev-store ]; then
        echo "删除 /var/log/dev-store 目录"
        rm -rf /var/log/dev-store
    fi
    
    # 删除源文件目录
    if [ -d /var/lib/dev-store ]; then
        echo "删除 /var/lib/dev-store 目录"
        rm -rf /var/lib/dev-store
    fi
    
    echo "清理完成 $(date "+%Y-%m-%d %H:%M:%S")"
    exit 0
}

# 处理命令行参数
case "$1" in
    --clean)
        clean_files
        ;;
    -h|--help)
        show_help
        exit 0
        ;;
    "")
        # 继续执行正常的同步操作
        ;;
    *)
        echo "错误: 未知选项 '$1'"
        show_help
        exit 1
        ;;
esac

# CONFIG
[ ! -d /etc/dev-store ] && mkdir /etc/dev-store
rm -rf /etc/dev-store/*
cp -rf configs/* /etc/dev-store

# LOG
[ ! -d /var/log/dev-store ] && mkdir /var/log/dev-store

# SRC
[ ! -d /var/lib/dev-store ] && mkdir -p /var/lib/dev-store
rm -rf /var/lib/dev-store/*
[ ! -d /var/lib/dev-store/src ] && mkdir -p /var/lib/dev-store/src
rm -rf /var/lib/dev-store/src/*
cp -rf artifacts tasks constants dev_store utils manage.py mcp_manage.sh /var/lib/dev-store/src
cp -rf services /var/lib/dev-store

# 为 /var/lib/dev-store/src 目录下的所有文件增加可执行权限
echo "为 /var/lib/dev-store/src 目录下的文件增加可执行权限..."
chmod -R +x /var/lib/dev-store/src

echo "success $(date "+%Y-%m-%d %H:%M:%S")"
