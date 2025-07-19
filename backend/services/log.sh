#!/bin/bash
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

# 日志模块 - 默认配置
# 默认日志级别 (DEBUG, INFO, WARN, ERROR, FATAL)
LOG_LEVEL="INFO"
# 日志目录
LOG_DIR="/var/log/dev-store/init-services"
# 日志文件名
LOG_FILE="$(date "+%Y%m%d%H%M%S%1N").log"
# 日志文件最大大小 (10MB)
MAX_LOG_SIZE=10485760

# 检查并创建日志目录
mkdir -p "${LOG_DIR}"

# 日志级别颜色定义
declare -A LOG_COLORS=(
    ["DEBUG"]="\033[0;36m"   # 青色
    ["INFO"]="\033[0;32m"    # 绿色
    ["WARN"]="\033[0;33m"    # 黄色
    ["ERROR"]="\033[0;31m"   # 红色
)
LOG_RESET="\033[0m"         # 重置颜色

# 日志级别权重（用于比较）
declare -A LOG_WEIGHTS=(
    ["DEBUG"]=10
    ["INFO"]=20
    ["WARN"]=30
    ["ERROR"]=40
)

# 检查当前日志级别是否足够输出
should_log() {
    local msg_level="$1"
    [[ ${LOG_WEIGHTS[${msg_level}]} -ge ${LOG_WEIGHTS[${LOG_LEVEL}]} ]]
}

# 日志轮转检查
rotate_logs() {
    local log_path="${LOG_DIR}/${LOG_FILE}"
    [[ ! -f "${log_path}" ]] && return
    local current_size=$(wc -c < "${log_path}")
    if [[ ${current_size} -ge ${MAX_LOG_SIZE} ]]; then
        local timestamp=$(date +%Y%m%d%H%M%S)
        mv "${log_path}" "${LOG_DIR}/${LOG_FILE%.*}_${timestamp}.log"
        echo "Log rotated: ${log_path} -> ${LOG_DIR}/${LOG_FILE%.*}_${timestamp}.log"
    fi
}

# 核心日志函数
log() {
    local level="$1"
    shift
    local message="$*"
    if ! should_log "${level}"; then
        return
    fi
    rotate_logs
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S.%3N")
    local log_entry="[${timestamp}] [${level}] ${message}"
    # 输出到终端（带颜色）
    if [ -t 1 ]; then
        echo -e "${LOG_COLORS[${level}]}${log_entry}${LOG_RESET}"
    else
        echo "${log_entry}"
    fi
    # 写入日志文件（不带颜色）
    echo "${log_entry}" >> "${LOG_DIR}/${LOG_FILE}"
}

# 快捷日志函数
debug() { log "DEBUG" "$@"; }
info()  { log "INFO"  "$@"; }
warn()  { log "WARN"  "$@"; }
error() { log "ERROR" "$@"; }
start_info() {
    local str="$1"
    local str_len=${#str}
    local total_len=60

    # 计算两侧 '=' 的数量
    local equals_len=$(( (total_len - str_len - 2) / 2 ))

    # 生成左侧 '=' 字符串
    local left_equals=$(printf "%${equals_len}s" | tr ' ' '=')

    # 生成右侧 '=' 字符串（可能比左侧多1个字符，以防奇数情况）
    local right_equals=$left_equals
    if [ $(( (total_len - str_len) % 2 )) -ne 0 ]; then
        right_equals+="="
    fi

    log "INFO" "${left_equals} ${str} ${right_equals}"
}