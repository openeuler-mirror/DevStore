%global __os_install_post %{nil}
%global debug_package %{nil}

Name:           dev-store
Version:        1.0.0
Release:        1
Summary:        Development Store Management System

Group:          Development/Tools
License:        MulanPSL-2.0
URL:            https://gitee.com/openeuler/DevStore
Source0:        %{name}-%{version}-%{_target_cpu}.tar.gz

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

%description
DevStore is a comprehensive development store management system that provides
both frontend and backend components for managing development resources,
artifacts, and services. The system includes a modern Electron-based desktop
application and a Django-based backend API.

%prep
%setup -q -n %{name}-%{version}-%{_target_cpu}

%build
# 无需编译步骤

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

# 安装前端应用文件
cp -rf opt/dev-store/app/* %{buildroot}/opt/dev-store/app/

# 安装后端源码文件
cp -rf var/lib/dev-store/src/* %{buildroot}/var/lib/dev-store/src/
cp -rf var/lib/dev-store/services/* %{buildroot}/var/lib/dev-store/services/

# 安装配置文件
cp -rf etc/dev-store/* %{buildroot}/etc/dev-store/

# 安装启动脚本
cp -f usr/bin/dev-store %{buildroot}/usr/bin/

# 安装桌面文件
cp -f usr/share/applications/dev-store.desktop %{buildroot}/usr/share/applications/

# 安装图标文件到多个尺寸目录
cp -f usr/share/icons/hicolor/256x256/apps/dev-store.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/
cp -f usr/share/icons/hicolor/128x128/apps/dev-store.png %{buildroot}/usr/share/icons/hicolor/128x128/apps/
cp -f usr/share/icons/hicolor/64x64/apps/dev-store.png %{buildroot}/usr/share/icons/hicolor/64x64/apps/
cp -f usr/share/icons/hicolor/48x48/apps/dev-store.png %{buildroot}/usr/share/icons/hicolor/48x48/apps/
cp -f usr/share/icons/hicolor/32x32/apps/dev-store.png %{buildroot}/usr/share/icons/hicolor/32x32/apps/
cp -f usr/share/icons/hicolor/16x16/apps/dev-store.png %{buildroot}/usr/share/icons/hicolor/16x16/apps/

# 安装systemd服务文件
cp -f usr/lib/systemd/system/dev-store.service %{buildroot}/usr/lib/systemd/system/

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

echo "DevStore服务已安装。"
echo "使用以下命令管理服务："
echo "  启用自启动: systemctl enable dev-store"
echo "  启动服务: systemctl start dev-store"
echo "  停止服务: systemctl stop dev-store"
echo "  查看状态: systemctl status dev-store"
echo "  查看日志: journalctl -u dev-store -f"

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
    echo "DevStore服务已完全移除。"
fi

%changelog
* Tue Aug 19 2025 dingjiahui <dingjiahui4@huawei.com> - 1.0.0-1
- Initial release of DevStore
- Includes frontend Electron application
- Includes backend Django application
- Provides comprehensive development store management functionality
- Added systemd service support for easy service management
- Users can now start/stop DevStore using systemctl commands
