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

# 默认配置
SKIP_FRONTEND=false

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
  --skip-frontend    跳过前端构建，复用已有的构建结果
  -h, --help         显示此帮助信息

示例:
  $0                 完整构建（包括前端和后端）
  $0 --skip-frontend 跳过前端构建，仅打包RPM

注意:
  使用 --skip-frontend 选项时，请确保 frontend/release/linux-unpacked 目录存在
  且包含有效的前端构建结果。
EOF
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-frontend)
                SKIP_FRONTEND=true
                shift
                ;;
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

if [ "$SKIP_FRONTEND" = true ]; then
    log_info "构建模式: 跳过前端构建"
else
    log_info "构建模式: 完整构建"
fi

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

# 获取当前系统架构
get_system_arch() {
    local arch=$(uname -m)
    case "$arch" in
        x86_64)
            echo "x64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        *)
            log_error "不支持的架构: $arch"
            exit 1
            ;;
    esac
}

# 构建前端
build_frontend() {
    if [ "$SKIP_FRONTEND" = true ]; then
        log_info "跳过前端构建，检查已有构建结果..."
        
        cd "$PROJECT_ROOT/frontend"
        
        # 检查是否存在已构建的前端文件
        if [ ! -d "release/linux-unpacked" ]; then
            log_error "未找到已构建的前端文件目录: release/linux-unpacked"
            log_error "请先运行完整构建或移除 --skip-frontend 选项"
            exit 1
        fi
        
        # 检查关键文件是否存在
        if [ ! -f "release/linux-unpacked/dev-store-app" ]; then
            log_error "前端构建结果不完整，缺少主执行文件"
            log_error "请重新运行完整构建"
            exit 1
        fi
        
        log_info "发现有效的前端构建结果，继续使用"
        return 0
    fi
    
    log_info "开始构建前端..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # 获取当前架构
    local target_arch=$(get_system_arch)
    log_info "目标架构: $target_arch"
    
    # 设置Electron镜像
    export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
    
    # 安装依赖
    log_info "安装前端依赖..."
    npm install electron -D --registry=https://registry.npmmirror.com
    npm install --registry=https://registry.npmmirror.com
    
    # 构建应用
    log_info "构建前端应用..."
    npm run build
    
    # 使用 electron-builder 构建 RPM 包，指定架构
    log_info "构建 Electron 应用 ($target_arch)..."
    npx electron-builder --linux rpm --$target_arch
    
    # 检查构建结果
    if [ ! -d "release/linux-unpacked" ]; then
        log_error "前端构建失败，未找到 linux-unpacked 目录"
        exit 1
    fi
    
    log_info "前端构建完成"
}

# 准备后端文件
prepare_backend() {
    log_info "准备后端文件..."
    
    cd "$PROJECT_ROOT/backend"
    
    # 创建临时目录
    local temp_backend="$BUILD_DIR/temp_backend"
    rm -rf "$temp_backend"
    mkdir -p "$temp_backend"
    
    # 复制后端文件到临时目录
    cp -rf artifacts tasks constants dev_store utils manage.py mcp_manage.sh "$temp_backend/"
    cp -rf services "$temp_backend/"
    cp -rf configs "$temp_backend/"
    
    log_info "后端文件准备完成"
}

# 准备前端文件
prepare_frontend() {
    log_info "准备前端文件..."
    
    # 创建临时目录
    local temp_frontend="$BUILD_DIR/temp_frontend"
    rm -rf "$temp_frontend"
    mkdir -p "$temp_frontend"
    
    # 复制前端构建结果
    cp -rf "$PROJECT_ROOT/frontend/release/linux-unpacked" "$temp_frontend/"
    
    log_info "前端文件准备完成"
}

# 创建源码包
create_source_package() {
    log_info "创建源码包..."
    
    cd "$BUILD_DIR"
    
    # 获取当前架构
    local target_arch=$(get_system_arch)
    local rpm_arch
    case "$target_arch" in
        x64)
            rpm_arch="x86_64"
            ;;
        arm64)
            rpm_arch="aarch64"
            ;;
    esac
    
    # 创建源码包目录
    local source_dir="dev-store-1.0.0"
    rm -rf "$source_dir"
    mkdir -p "$source_dir"
    
    # 复制前端文件
    mkdir -p "$source_dir/opt/dev-store/app"
    cp -rf temp_frontend/linux-unpacked/* "$source_dir/opt/dev-store/app/"
    
    # 复制后端文件
    mkdir -p "$source_dir/var/lib/dev-store/src"
    cp -rf temp_backend/artifacts temp_backend/tasks temp_backend/constants temp_backend/dev_store temp_backend/utils temp_backend/manage.py temp_backend/mcp_manage.sh "$source_dir/var/lib/dev-store/src/"
    
    mkdir -p "$source_dir/var/lib/dev-store/services"
    cp -rf temp_backend/services/* "$source_dir/var/lib/dev-store/services/"
    
    mkdir -p "$source_dir/etc/dev-store"
    cp -rf temp_backend/configs/* "$source_dir/etc/dev-store/"
    
    # 创建必要的目录
    mkdir -p "$source_dir/var/log/dev-store"
    mkdir -p "$source_dir/usr/bin"
    mkdir -p "$source_dir/usr/share/applications"
    mkdir -p "$source_dir/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$source_dir/usr/share/icons/hicolor/128x128/apps"
    mkdir -p "$source_dir/usr/share/icons/hicolor/64x64/apps"
    mkdir -p "$source_dir/usr/share/icons/hicolor/48x48/apps"
    mkdir -p "$source_dir/usr/share/icons/hicolor/32x32/apps"
    mkdir -p "$source_dir/usr/share/icons/hicolor/16x16/apps"
    
    # 创建启动脚本
    cat > "$source_dir/usr/bin/dev-store" << 'EOF'
#!/bin/bash
cd /var/lib/dev-store/src
python3 manage.py runserver 0.0.0.0:28080
EOF
    
    # 创建桌面文件
    cat > "$source_dir/usr/share/applications/dev-store.desktop" << 'EOF'
[Desktop Entry]
Name=DevStore
Comment=Development Store Management System
Exec=/opt/dev-store/app/dev-store-app
Icon=dev-store
Type=Application
Categories=Development;
StartupWMClass=dev-store-app
EOF
    
    # 复制图标文件到多个尺寸目录
    if [ -f "$PROJECT_ROOT/frontend/src/assets/logo.png" ]; then
        # 复制到各个尺寸目录（假设logo.png是合适的尺寸）
        cp "$PROJECT_ROOT/frontend/src/assets/logo.png" "$source_dir/usr/share/icons/hicolor/256x256/apps/dev-store.png"
        cp "$PROJECT_ROOT/frontend/src/assets/logo.png" "$source_dir/usr/share/icons/hicolor/128x128/apps/dev-store.png"
        cp "$PROJECT_ROOT/frontend/src/assets/logo.png" "$source_dir/usr/share/icons/hicolor/64x64/apps/dev-store.png"
        cp "$PROJECT_ROOT/frontend/src/assets/logo.png" "$source_dir/usr/share/icons/hicolor/48x48/apps/dev-store.png"
        cp "$PROJECT_ROOT/frontend/src/assets/logo.png" "$source_dir/usr/share/icons/hicolor/32x32/apps/dev-store.png"
        cp "$PROJECT_ROOT/frontend/src/assets/logo.png" "$source_dir/usr/share/icons/hicolor/16x16/apps/dev-store.png"
        log_info "图标文件已复制到多个尺寸目录"
    else
        log_warn "未找到图标文件: $PROJECT_ROOT/frontend/src/assets/logo.png"
    fi
    
    # 复制项目根目录的文档和许可证文件
    cp "$PROJECT_ROOT/README.md" "$source_dir/" 2>/dev/null || true
    cp "$PROJECT_ROOT/README.en.md" "$source_dir/" 2>/dev/null || true
    cp "$PROJECT_ROOT/LICENSE" "$source_dir/" 2>/dev/null || true
    
    # 创建tar.gz源码包
    tar -czf "dev-store-1.0.0.tar.gz" "$source_dir"
    
    # 移动到RPM构建目录
    mv "dev-store-1.0.0.tar.gz" "$WORKSPACE_DIR/rpmbuild/SOURCES/"
    
    # 复制spec文件
    cp "dev-store.spec" "$WORKSPACE_DIR/rpmbuild/SPECS/"
    
    log_info "源码包创建完成"
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

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    
    cd "$BUILD_DIR"
    rm -rf temp_frontend temp_backend
    
    log_info "清理完成"
}

# 主函数
main() {
    check_dependencies
    setup_rpmbuild
    build_frontend
    prepare_backend
    prepare_frontend
    create_source_package
    build_rpm
    cleanup
    
    log_info "DevStore RPM包构建完成！"
}

# 执行主函数
main
