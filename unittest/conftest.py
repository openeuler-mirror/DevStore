#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import tempfile
import django
from pathlib import Path

# 设置Django项目路径
backend_path = Path(__file__).resolve().parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

# 创建临时目录用于测试
test_temp_dir = Path(tempfile.mkdtemp(prefix='devstore_test_'))
db_dir = test_temp_dir / 'db'
log_dir = test_temp_dir / 'logs'
cache_dir = test_temp_dir / 'cache'
mcp_dir = test_temp_dir / 'mcp'
plugin_cache_dir = test_temp_dir / 'home' / '.oedp'

for path in (db_dir, log_dir, cache_dir, mcp_dir, plugin_cache_dir):
    path.mkdir(parents=True, exist_ok=True)

# 设置环境变量和常量以指向临时目录
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dev_store.settings')
os.environ['HOME'] = str(test_temp_dir / 'home')

# 将常量指向测试目录，避免写入系统路径
import constants.paths as paths  # noqa: E402
paths.DB_DIR = str(db_dir)
paths.SQLITE_DB_FILE = str(db_dir / 'dev_store.db')
paths.LOG_DIR = str(log_dir)
paths.CACHE_DIR = str(cache_dir)
paths.MCP_BASE_DIR = str(mcp_dir)
paths.PLUGIN_CACHE_DIR = str(plugin_cache_dir)

# 初始化Django
django.setup()
