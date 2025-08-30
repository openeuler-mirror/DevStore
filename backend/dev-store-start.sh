#!/bin/bash
set -e

# 切换到项目目录
cd /var/lib/dev-store/src

# 启动服务器
python3 manage.py runserver 0.0.0.0:28080
