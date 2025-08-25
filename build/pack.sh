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
# Create: 2025-08-26

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

# 显示帮助信息
show_help() {
    cat << EOF
用法: $0 [选项]

选项:
  -h, --help         显示此帮助信息

功能:
  将DevStore源码打包成tar.gz文件，用于后续的RPM构建。
  会自动过滤临时文件和构建产物，但保留所有源码文件。

输出:
  在build目录下生成 dev-store-VERSION.tar.gz 文件

注意:
  - 源码包无需区分架构，因为只包含源码文件
  - 会过滤掉node_modules、.git、临时文件等
  - 保留所有源码、配置文件和必要的资源文件
EOF
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 获取脚本所在目录
SCRIPT_DIR=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
BUILD_DIR="$SCRIPT_DIR"

# 解析命令行参数
parse_arguments "$@"

log_info "开始打包 DevStore 源码"
log_info "项目根目录: $PROJECT_ROOT"
log_info "构建目录: $BUILD_DIR"

# 从spec文件中获取版本号
get_version_from_spec() {
    local spec_file="$BUILD_DIR/dev-store.spec"
    if [ ! -f "$spec_file" ]; then
        log_error "未找到spec文件: $spec_file"
        exit 1
    fi
    
    # 使用grep和sed提取版本号
    local version=$(grep "^Version:" "$spec_file" | sed 's/Version:\s*//' | tr -d ' ')
    if [ -z "$version" ]; then
        log_error "无法从spec文件中提取版本号"
        exit 1
    fi
    
    echo "$version"
}



# 创建源码包
create_source_package() {
    log_info "创建源码包..."
    
    cd "$BUILD_DIR"
    
    # 获取版本号
    local version=$(get_version_from_spec)
    log_info "版本号: $version"
    
    # 创建源码包目录（源码包无需区分架构）
    local source_dir="dev-store-$version"
    rm -rf "$source_dir"
    mkdir -p "$source_dir"
    
    log_info "复制源码文件..."
    
    # 复制后端源码（保持目录结构）
    cd "$PROJECT_ROOT"
    
    # 复制后端目录，过滤不需要的文件
    if [ -d "backend" ]; then
        log_info "复制后端源码..."
        rsync -av --exclude='__pycache__' \
                  --exclude='*.pyc' \
                  --exclude='*.pyo' \
                  --exclude='.pytest_cache' \
                  --exclude='*.egg-info' \
                  --exclude='venv' \
                  --exclude='env' \
                  --exclude='.env' \
                  --exclude='db.sqlite3' \
                  --exclude='*.log' \
                  --exclude='logs' \
                  backend/ "$BUILD_DIR/$source_dir/backend/"
    fi
    
    # 复制前端源码，过滤不需要的文件
    if [ -d "frontend" ]; then
        log_info "复制前端源码..."
        rsync -av --exclude='node_modules' \
                  --exclude='dist' \
                  --exclude='build' \
                  --exclude='release' \
                  --exclude='.next' \
                  --exclude='.nuxt' \
                  --exclude='coverage' \
                  --exclude='.nyc_output' \
                  --exclude='*.log' \
                  --exclude='npm-debug.log*' \
                  --exclude='yarn-debug.log*' \
                  --exclude='yarn-error.log*' \
                  --exclude='.DS_Store' \
                  --exclude='Thumbs.db' \
                  frontend/ "$BUILD_DIR/$source_dir/frontend/"
    fi
    
    # 复制构建脚本和配置文件
    if [ -d "build" ]; then
        log_info "复制构建配置..."
        rsync -av --exclude='temp_*' \
                  --exclude='*.tar.gz' \
                  --exclude='*.rpm' \
                  --exclude='BUILD_GUIDE.md' \
                  build/ "$BUILD_DIR/$source_dir/build/"
    fi
    
    # 复制项目根目录的重要文件
    for file in README.md README.en.md LICENSE .gitignore; do
        if [ -f "$file" ]; then
            cp "$file" "$BUILD_DIR/$source_dir/" 2>/dev/null || true
        fi
    done
    
    # 复制其他可能存在的目录（可扩展性考虑）
    for dir in docs scripts tools; do
        if [ -d "$dir" ]; then
            log_info "复制 $dir 目录..."
            rsync -av --exclude='.git' \
                      --exclude='*.tmp' \
                      --exclude='*.temp' \
                      "$dir/" "$BUILD_DIR/$source_dir/$dir/"
        fi
    done
    
    cd "$BUILD_DIR"
    
    # 创建tar.gz源码包（源码包无需区分架构）
    local tarball_name="dev-store-$version.tar.gz"
    log_info "创建压缩包: $tarball_name"
    tar -czf "$tarball_name" "$source_dir"
    
    # 清理临时目录
    rm -rf "$source_dir"
    
    log_info "源码包创建完成: $BUILD_DIR/$tarball_name"
    
    # 显示包的大小
    local size=$(ls -lh "$tarball_name" | awk '{print $5}')
    log_info "源码包大小: $size"
}

# 主函数
main() {
    create_source_package
    log_info "DevStore 源码打包完成！"
}

# 执行主函数
main
