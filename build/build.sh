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

# 显示帮助信息
show_help() {
    cat << EOF
用法: $0 [选项]

选项:
  -h, --help         显示此帮助信息

功能:
  使用已打包的源码执行RPM构建。
  
前置条件:
  需要先运行 pack.sh 创建源码包。

架构支持:
  脚本会自动检测当前系统架构（x86_64 或 aarch64/arm64）
  并使用对应的源码包进行构建。

注意:
  - 编译操作已集成到spec文件中
  - 此脚本仅执行rpmbuild命令
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
WORKSPACE_DIR="$HOME"

# 解析命令行参数
parse_arguments "$@"

log_info "开始构建 DevStore RPM 包"
log_info "项目根目录: $PROJECT_ROOT"
log_info "构建目录: $BUILD_DIR"
log_info "工作目录: $WORKSPACE_DIR"

# 检查必要的工具
check_dependencies() {
    log_info "检查构建依赖..."
    
    local missing_deps=()
    
    for cmd in rpmbuild rpmdev-setuptree; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "缺少必要的构建工具: ${missing_deps[*]}"
        log_error "请安装: sudo dnf install rpm-build rpmdevtools"
        exit 1
    fi
    
    log_info "构建依赖检查完成"
}

# 设置RPM构建环境
setup_rpmbuild() {
    log_info "设置RPM构建环境..."
    
    cd "$WORKSPACE_DIR"
    
    # 清理旧的构建环境
    if [ -d "rpmbuild" ]; then
        log_warn "清理旧的rpmbuild目录"
        rm -rf rpmbuild
    fi
    
    # 创建新的构建环境
    rpmdev-setuptree
    
    log_info "RPM构建环境设置完成"
}

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



# 准备构建文件
prepare_build_files() {
    log_info "准备构建文件..."
    
    cd "$BUILD_DIR"
    
    # 获取版本号
    local version=$(get_version_from_spec)
    
    # 检查源码包是否存在（源码包无需区分架构）
    local tarball_name="dev-store-$version.tar.gz"
    if [ ! -f "$tarball_name" ]; then
        log_error "未找到源码包: $tarball_name"
        log_error "请先运行 pack.sh 创建源码包"
        exit 1
    fi
    
    log_info "发现源码包: $tarball_name"
    
    # 复制源码包到RPM构建目录
    cp "$tarball_name" "$WORKSPACE_DIR/rpmbuild/SOURCES/"
    
    # 复制spec文件
    cp "dev-store.spec" "$WORKSPACE_DIR/rpmbuild/SPECS/"
    
    log_info "构建文件准备完成"
}

# 构建RPM包
build_rpm() {
    log_info "开始构建RPM包..."
    
    cd "$WORKSPACE_DIR/rpmbuild/SPECS"
    
    # 构建RPM包
    rpmbuild -ba dev-store.spec
    
    log_info "RPM包构建完成"
    
    # 显示构建结果
    log_info "构建结果:"
    find "$WORKSPACE_DIR/rpmbuild/RPMS" -name "*.rpm" -type f
    find "$WORKSPACE_DIR/rpmbuild/SRPMS" -name "*.rpm" -type f
}

# 主函数
main() {
    check_dependencies
    setup_rpmbuild
    prepare_build_files
    build_rpm
    
    log_info "DevStore RPM包构建完成！"
    log_info ""
    log_info "使用方法："
    log_info "1. 先运行: ./pack.sh    # 打包源码"
    log_info "2. 再运行: ./build.sh   # 构建RPM包"
}

# 执行主函数
main