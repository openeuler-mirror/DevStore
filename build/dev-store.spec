%global debug_package %{nil}

Name:           dev-store
Version:        1.0.2
Release:        1
Summary:        Development Store Management System

Group:          Development/Tools
License:        MulanPSL-2.0
URL:            https://gitee.com/openeuler/DevStore
Source0:        %{name}-%{version}.tar.gz

# 依赖包
Requires:       python3-django-rest-framework
Requires:       mariadb-server
Requires:       expect
Requires:       dnf-plugins-core
Requires:       python3
Requires:       python3-mysqlclient
Requires:       python3-concurrent-log-handler
Requires:       python3-cryptography
Requires:       python3-Django
Requires:       python3-pyyaml
Requires:       python3-psutil
Requires:       python3-zstandard
Requires:       systemd

# 构建依赖
BuildRequires:  rpm-build
BuildRequires:  rpmdevtools
BuildRequires:  npm
BuildRequires:  ruby
BuildRequires:  ruby-devel
BuildRequires:  rubygems
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make

# 排除Electron应用目录的自动依赖分析
%global __provides_exclude_from ^/opt/dev-store/app/.*$
%global __requires_exclude_from ^/opt/dev-store/app/.*$
# 排除特定的Electron应用共享库依赖
%global __requires_exclude ^(libffmpeg\.so|libEGL\.so|libGLESv2\.so|libvulkan\.so|libvk_swiftshader\.so).*$

%description
DevStore is a comprehensive development store management system that provides
both frontend and backend components for managing development resources,
artifacts, and services. The system includes a modern Electron-based desktop
application and a Django-based backend API.

%prep
%setup -q -n %{name}-%{version}

%build
# 编译前端应用
cd frontend

# 设置Electron镜像
export ELECTRON_MIRROR=https://mirrors.huaweicloud.com/electron/

# 获取当前架构
case "%{_arch}" in
    x86_64)
        TARGET_ARCH="x64"
        ;;
    aarch64|arm64)
        TARGET_ARCH="arm64"
        ;;
    *)
        echo "不支持的架构: %{_arch}"
        exit 1
        ;;
esac

echo "目标架构: $TARGET_ARCH"

# 安装依赖 - 使用 npm ci 确保严格按照 package-lock.json
npm ci

# 构建应用
npm run build

# 设置环境变量以确保正确的架构构建
export TARGET_ARCH=$TARGET_ARCH

# 根据架构选择正确的构建命令，只构建unpacked目录
if [ "$TARGET_ARCH" = "arm64" ]; then
    npx electron-builder --linux dir --arm64
else
    npx electron-builder --linux dir --x64
fi

# 检查构建结果
if [ "$TARGET_ARCH" = "arm64" ]; then
    EXPECTED_DIR="release/linux-arm64-unpacked"
else
    EXPECTED_DIR="release/linux-unpacked"
fi

if [ ! -d "$EXPECTED_DIR" ]; then
    echo "前端构建失败，未找到 $EXPECTED_DIR 目录"
    ls -la release/ || true
    exit 1
fi

echo "前端构建完成"
cd ..

%install
# 创建安装目录结构
mkdir -p %{buildroot}/opt/dev-store/app
mkdir -p %{buildroot}/var/lib/dev-store/src
mkdir -p %{buildroot}/var/lib/dev-store/services
mkdir -p %{buildroot}/etc/dev-store
mkdir -p %{buildroot}/var/log/dev-store
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/128x128/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/64x64/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/48x48/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/32x32/apps
mkdir -p %{buildroot}/usr/share/icons/hicolor/16x16/apps
mkdir -p %{buildroot}/usr/lib/systemd/system

# 获取当前架构以确定前端构建结果目录
case "%{_arch}" in
    x86_64)
        FRONTEND_DIR="frontend/release/linux-unpacked"
        ;;
    aarch64|arm64)
        FRONTEND_DIR="frontend/release/linux-arm64-unpacked"
        ;;
    *)
        echo "不支持的架构: %{_arch}"
        exit 1
        ;;
esac

# 安装前端应用文件
cp -rf $FRONTEND_DIR/* %{buildroot}/opt/dev-store/app/

# 安装后端源码文件
cp -rf backend/artifacts %{buildroot}/var/lib/dev-store/src/
cp -rf backend/tasks %{buildroot}/var/lib/dev-store/src/
cp -rf backend/constants %{buildroot}/var/lib/dev-store/src/
cp -rf backend/dev_store %{buildroot}/var/lib/dev-store/src/
cp -rf backend/utils %{buildroot}/var/lib/dev-store/src/
cp -f backend/manage.py %{buildroot}/var/lib/dev-store/src/
cp -f backend/mcp_manage.sh %{buildroot}/var/lib/dev-store/src/

cp -rf backend/services/* %{buildroot}/var/lib/dev-store/services/

# 安装配置文件
cp -rf backend/configs/* %{buildroot}/etc/dev-store/

# 安装启动脚本
cp -f backend/dev-store-start.sh %{buildroot}/usr/bin/dev-store

# 安装桌面文件
cp -f build/dev-store.desktop %{buildroot}/usr/share/applications/

# 安装图标文件到多个尺寸目录
if [ -f "frontend/src/assets/logo.png" ]; then
    cp frontend/src/assets/logo.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/dev-store.png
    cp frontend/src/assets/logo.png %{buildroot}/usr/share/icons/hicolor/128x128/apps/dev-store.png
    cp frontend/src/assets/logo.png %{buildroot}/usr/share/icons/hicolor/64x64/apps/dev-store.png
    cp frontend/src/assets/logo.png %{buildroot}/usr/share/icons/hicolor/48x48/apps/dev-store.png
    cp frontend/src/assets/logo.png %{buildroot}/usr/share/icons/hicolor/32x32/apps/dev-store.png
    cp frontend/src/assets/logo.png %{buildroot}/usr/share/icons/hicolor/16x16/apps/dev-store.png
fi

# 安装systemd服务文件
cp -f build/dev-store.service %{buildroot}/usr/lib/systemd/system/

# 设置文件权限
chmod 755 %{buildroot}/opt/dev-store/app/dev-store-app
chmod 755 %{buildroot}/usr/bin/dev-store
chmod 644 %{buildroot}/usr/share/applications/dev-store.desktop

# 设置目录权限
chmod 755 %{buildroot}/opt/dev-store/app
chmod 755 %{buildroot}/var/lib/dev-store/src
chmod 755 %{buildroot}/var/lib/dev-store/services
chmod 755 %{buildroot}/etc/dev-store
chmod 755 %{buildroot}/var/log/dev-store

# 设置Python文件权限
find %{buildroot}/var/lib/dev-store/src -name "*.py" -exec chmod 644 {} \;
find %{buildroot}/var/lib/dev-store/src -name "*.sh" -exec chmod 755 {} \;

%files
%defattr(-,root,root,-)
%license LICENSE
%doc README.md README.en.md

# 前端应用文件 - 使用通配符以支持不同架构
%attr(755,root,root) /opt/dev-store/app/dev-store-app
%attr(755,root,root) /opt/dev-store/app/chrome-sandbox
%attr(755,root,root) /opt/dev-store/app/chrome_crashpad_handler
/opt/dev-store/app/*.pak
/opt/dev-store/app/*.so*
/opt/dev-store/app/*.dat
/opt/dev-store/app/*.bin
/opt/dev-store/app/*.json
/opt/dev-store/app/*.html
/opt/dev-store/app/*.txt
/opt/dev-store/app/locales/
/opt/dev-store/app/resources/

# 后端源码文件
%attr(644,root,root) /var/lib/dev-store/src/*.py
%attr(755,root,root) /var/lib/dev-store/src/*.sh
%attr(755,root,root) /var/lib/dev-store/src/artifacts/
%attr(755,root,root) /var/lib/dev-store/src/tasks/
%attr(755,root,root) /var/lib/dev-store/src/constants/
%attr(755,root,root) /var/lib/dev-store/src/dev_store/
%attr(755,root,root) /var/lib/dev-store/src/utils/
%attr(755,root,root) /var/lib/dev-store/services/

# 配置文件
%config(noreplace) /etc/dev-store/

# 日志目录
%attr(755,root,root) /var/log/dev-store

# 启动脚本
%attr(755,root,root) /usr/bin/dev-store

# 桌面文件
%attr(644,root,root) /usr/share/applications/dev-store.desktop

# 图标文件
%attr(644,root,root) /usr/share/icons/hicolor/256x256/apps/dev-store.png
%attr(644,root,root) /usr/share/icons/hicolor/128x128/apps/dev-store.png
%attr(644,root,root) /usr/share/icons/hicolor/64x64/apps/dev-store.png
%attr(644,root,root) /usr/share/icons/hicolor/48x48/apps/dev-store.png
%attr(644,root,root) /usr/share/icons/hicolor/32x32/apps/dev-store.png
%attr(644,root,root) /usr/share/icons/hicolor/16x16/apps/dev-store.png

# systemd服务文件
%attr(644,root,root) /usr/lib/systemd/system/dev-store.service

%post
# 安装后脚本
# 创建必要的目录和设置权限
mkdir -p /var/log/dev-store
chown -R root:root /var/log/dev-store
chmod 755 /var/log/dev-store

# 设置数据库目录权限
mkdir -p /var/lib/dev-store
chown -R root:root /var/lib/dev-store
chmod 755 /var/lib/dev-store

# 更新桌面数据库
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

# 更新图标缓存
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor
fi

# 重新加载systemd配置
systemctl daemon-reload

# Enable and start dev-store service (failure won't affect installation)
systemctl enable dev-store.service 2>/dev/null || {
    echo "Warning: Failed to enable dev-store service auto-start. Please run manually: systemctl enable dev-store"
}

systemctl start dev-store.service 2>/dev/null || {
    echo "Warning: Failed to start dev-store service. Please run manually: systemctl start dev-store"
    echo "Possible reasons: Dependencies not ready or configuration needs adjustment"
}

echo "DevStore service has been installed."
echo "Use the following commands to manage the service:"
echo "  Enable auto-start: systemctl enable dev-store"
echo "  Start service: systemctl start dev-store"
echo "  Stop service: systemctl stop dev-store"
echo "  Check status: systemctl status dev-store"
echo "  View logs: journalctl -u dev-store -f"

%preun
# 卸载前脚本
# 停止并禁用dev-store服务
if [ $1 -eq 0 ]; then
    # 完全卸载时执行
    systemctl stop dev-store.service 2>/dev/null || true
    systemctl disable dev-store.service 2>/dev/null || true
fi

%postun
# 卸载后脚本
if [ $1 -eq 0 ]; then
    # 完全卸载时执行
    systemctl daemon-reload
    echo "DevStore service has been completely removed."
fi

%changelog
* Sat Sep 13 2025 dingjiahui <dingjiahui4@huawei.com> - 1.0.2-1
- Fix JSON copy issue on MCP details page
* Tue Sep 2 2025 dingjiahui <dingjiahui4@huawei.com> - 1.0.1-1
- Support search functionality
- Fix the issue where the list is empty when returning to the homepage from the details page
- Auto-enable and start dev-store service after installation
- Add error handling to ensure service startup failures don't affect package installation
* Tue Aug 19 2025 dingjiahui <dingjiahui4@huawei.com> - 1.0.0-1
- Initial release of DevStore
- Includes frontend Electron application
- Includes backend Django application
- Provides comprehensive development store management functionality
- Added systemd service support for easy service management
- Users can now start/stop DevStore using systemctl commands
