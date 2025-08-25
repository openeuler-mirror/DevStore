#!/bin/bash

# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# DevStore is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2025-08-18

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
BUILD_DIR="$SCRIPT_DIR"
WORKSPACE_DIR="$HOME"

log_info "开始清理 DevStore 构建环境"

# 清理构建目录中的临时文件
clean_build_dir() {
    log_info "清理构建目录临时文件..."
    
    cd "$BUILD_DIR"
    
    # 清理源码包
    for tarball in dev-store-*.tar.gz; do
        if [ -f "$tarball" ]; then
            rm -f "$tarball"
            log_info "已清理源码包: $tarball"
        fi
    done
    
    # 清理打包过程中可能产生的临时源码目录
    for dir in dev-store-*; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            log_info "已清理临时源码目录: $dir"
        fi
    done
}

# 清理RPM构建环境
clean_rpmbuild() {
    log_info "清理RPM构建环境..."
    
    cd "$WORKSPACE_DIR"
    
    if [ -d "rpmbuild" ]; then
        rm -rf rpmbuild
        log_info "已清理 rpmbuild 目录"
    else
        log_warn "rpmbuild 目录不存在，无需清理"
    fi
}

# 清理前端构建产物
clean_frontend() {
    log_info "清理前端构建产物..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # 清理node_modules（可选）
    if [ "$1" = "--all" ]; then
        if [ -d "node_modules" ]; then
            rm -rf node_modules
            log_info "已清理 node_modules 目录"
        fi
        
        if [ -f "package-lock.json" ]; then
            rm -f package-lock.json
            log_info "已清理 package-lock.json"
        fi
    fi
    
    # 清理构建产物
    if [ -d "dist" ]; then
        rm -rf dist
        log_info "已清理 dist 目录"
    fi
    
    if [ -d "release" ]; then
        rm -rf release
        log_info "已清理 release 目录"
    fi
    

}

# 清理 electron-builder 缓存
clean_electron_cache() {
    log_info "清理 electron-builder 缓存..."
    
    local cache_dir="$HOME/.cache/electron-builder"
    
    if [ -d "$cache_dir" ]; then
        rm -rf "$cache_dir"
        log_info "已清理 electron-builder 缓存目录: $cache_dir"
    else
        log_warn "electron-builder 缓存目录不存在，无需清理"
    fi
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --all          清理所有文件，包括node_modules、package-lock.json和electron-builder缓存"
    echo "  --rpmbuild     仅清理RPM构建环境"
    echo "  --frontend     仅清理前端构建产物"
    echo "  --build        仅清理构建目录临时文件"
    echo "  --cache        仅清理electron-builder缓存"
    echo "  -h, --help     显示此帮助信息"
    echo ""
    echo "清理内容:"
    echo "  - 源码包 (dev-store-*.tar.gz)"
    echo "  - 临时源码目录"
    echo "  - RPM构建环境 (~/rpmbuild/)"
    echo "  - 前端构建产物 (dist/, release/)"
    echo "  - Electron缓存 (~/.cache/electron-builder/)"
    echo ""
    echo "默认行为: 清理构建目录临时文件和源码包"
}

# 主函数
main() {
    case "${1:-}" in
        --all)
            clean_build_dir
            clean_rpmbuild
            clean_frontend --all
            clean_electron_cache
            ;;
        --rpmbuild)
            clean_rpmbuild
            ;;
        --frontend)
            clean_frontend
            ;;
        --build)
            clean_build_dir
            ;;
        --cache)
            clean_electron_cache
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        "")
            clean_build_dir
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    
    log_info "清理完成！"
}

# 执行主函数
main "$@"
