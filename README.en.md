# DevStore

#### Introduction

DevStore is the default software store for the DevStation platform, providing developers with quick installation capabilities for MCP services and OEDP plugins.


#### First-time Usage

If you are opening DevStore for the first time and see no components on the interface, you need to perform the following initialization steps.

1. Set the MariaDB root password and dev-store password in the configuration file:

```bash
sudo vim /etc/dev-store/mariadb/init_mariadb.conf
```

2. Initialize MariaDB:

```bash
sudo sh /var/lib/dev-store/services/init_mariadb.sh auto
```

3. Start the DevStore backend service:

```bash
sudo systemctl start dev-store && sudo systemctl enable dev-store
```

4. Click the sync button in the upper right corner of the interface, or restart DevStore. Start experiencing DevStore.
