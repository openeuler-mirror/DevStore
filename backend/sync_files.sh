#!/usr/bin/env bash
# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# oeDeploy is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2025-07-18
# ======================================================================================================================

set -e

[ ! -d /var/lib/dev-store ] && mkdir -p /var/lib/dev-store
[ ! -d /var/lib/dev-store/src ] && mkdir -p /var/lib/dev-store/src
cp -rf artifacts tasks constants dev_store utils manage.py /var/lib/dev-store/src
cp -rf services /var/lib/dev-store
echo "success $(date "+%Y-%m-%d %H:%M:%S")"
