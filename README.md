# DevStore

#### 介绍

DevStore 是 DevStation 平台默认的软件商店，面向开发者提供 MCP 服务、OEDP 插件的快速安装能力。


#### 首次使用

如果您首次打开 DevStore，界面上没有任何组件，需要执行如下初始化操作。

1. 在配置文件中设置 MariaDB 的 root 密码 和 dev-store 密码：

```bash
sudo vim /etc/dev-store/mariadb/init_mariadb.conf
```

2. 初始化 MariaDB：

```bash
sh /var/lib/dev-store/services/init_mariadb.sh auto
```

3. 启动 DevStore 后端服务：

```bash
systemctl start dev-store && systemctl enable dev-store
```

4. 点击界面右上角的同步按钮，或者重启 DevStore。开始体验 DevStore。
