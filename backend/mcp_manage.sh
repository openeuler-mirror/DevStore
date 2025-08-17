#!/bin/bash
# mcp_manage.sh - MCP配置管理模块化版本，适合接口调用

# 获取实际调用者用户名（支持 sudo / su 场景）
CALL_USER=$(logname 2>/dev/null || echo $SUDO_USER || echo $USER)
# 获取调用者 home 目录
CALL_USER_HOME=$(getent passwd "$CALL_USER" | cut -d: -f6)
# == 预定义路径 ==
declare -A APP_CONFIG_PATHS=(
    ["DeepChat"]="$CALL_USER_HOME/.config/DeepChat/mcp_settings.json"
    ["roo-code"]="$CALL_USER_HOME/.config/VSCodium/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json"
)

declare -A APP_DISPLAY_NAMES=(
    ["roo-code"]="roo-code"
    ["DeepChat"]="DeepChat"
)

MCP_SERVERS_DIR="/opt/mcp-servers/servers"

# == 公用函数 ==
json_error() {
    local message="$1"
    echo "{\"error\":\"$message\"}"
}

fail() {
    local msg="$1"
    json_error "$msg"
    exit 1
}

get_app_config_path() {
    local app="$1"
    if [[ -n "${APP_CONFIG_PATHS[$app]}" ]]; then
        echo "${APP_CONFIG_PATHS[$app]}"
    else
        echo "$CALL_USER_HOME/.config/${app}/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json"
    fi
}

get_mcp_server_name_from_config() {
    local config_file="$1"

    # 检查文件是否存在
    if [[ ! -f "$config_file" ]]; then
        return 1
    fi

    # 从 mcp_config.json 中读取服务器配置的第一个键名
    local server_name
    server_name=$(jq -r '.mcpServers | keys[0]' "$config_file" 2>/dev/null)

    if [[ -n "$server_name" && "$server_name" != "null" ]]; then
        echo "$server_name"
        return 0
    fi

    return 1
}

# == 从配置文件中查找真实的服务器名称 ==
find_real_server_name() {
    local mcp_name="$1"
    local app="$2"
    local user_config
    user_config=$(get_app_config_path "$app")
    
    # 检查用户配置文件是否存在
    if [[ ! -f "$user_config" ]]; then
        return 1
    fi
    
    # 通过 find_mcp_config_file 找到配置文件
    local config_file
    config_file=$(find_mcp_config_file "$mcp_name")
    
    if [[ $? -eq 0 && -f "$config_file" ]]; then
        # 从MCP配置文件中获取真实的服务器名称
        local real_server_name
        real_server_name=$(get_mcp_server_name_from_config "$config_file")
        
        if [[ -n "$real_server_name" ]]; then
            # 检查用户配置中是否存在这个服务器名称
            if jq -e ".mcpServers.\"$real_server_name\"" "$user_config" >/dev/null 2>&1; then
                echo "$real_server_name"
                return 0
            fi
        fi
    fi
    
    return 1
}

# == 查找 MCP 配置文件 ==
find_mcp_config_file() {
    local package_name="$1"
    
    # 检查是否是完整路径
    if [[ -f "$package_name" ]]; then
        echo "$package_name"
        return 0
    fi
    
    # 直接使用rpm -ql查找包的mcp_config.json文件
    local config_file
    config_file=$(rpm -ql "$package_name" 2>/dev/null | grep "mcp_config.json$" | head -1)
    
    if [[ -n "$config_file" && -f "$config_file" ]]; then
        echo "$config_file"
        return 0
    fi
    
    return 1
}


is_app_installed() {
    local app="$1"
    
    case "$app" in
        "roo code"|"roo-code")
            if ! command -v "vscodium" >/dev/null 2>&1 && [[ ! -d "$CALL_USER_HOME/.config/VSCodium" ]]; then
                return 1
            fi
            if [[ -d "$CALL_USER_HOME/.config/VSCodium/User/globalStorage/rooveterinaryinc.roo-cline" ]]; then
                return 0
            fi
            return 1
            ;;
        "DeepChat")
            if command -v "deepchat" >/dev/null 2>&1; then
                return 0
            fi
            if [[ -d "$CALL_USER_HOME/.config/DeepChat" ]]; then
                return 0
            fi
            return 1
            ;;
        *)
            if command -v "$app" >/dev/null 2>&1; then
                return 0
            fi
            local config_dir="$CALL_USER_HOME/.config/$app"
            if [[ -d "$config_dir" ]]; then
                return 0
            fi
            return 1
            ;;
    esac
}

normalize_mcp_config() {
    local config_file="$1"
    local app="$2"
    
    case "$app" in
        "DeepChat")
            jq '
            .mcpServers |= with_entries(.value |= . + {
                descriptions: (.descriptions // .description // ""),
                icons: (.icons // "🔧"),
                autoApprove: (.autoApprove // []),
                type: (.type // "stdio"),
                env: (.env // {}),
                disable: (.disable // .disabled // false)
            })
            ' "$config_file"
            ;;
        *)
            cat "$config_file"
            ;;
    esac
}

write_config() {
    local mcp_name="$1"
    local app="$2"
    
    local config_file
    config_file=$(find_mcp_config_file "$mcp_name")
    if [[ $? -ne 0 ]]; then
        fail "找不到MCP配置文件: $mcp_name"
    fi
    
    if ! is_app_installed "$app"; then
        fail "$app 未安装或未使用过"
    fi
    
    local user_config
    user_config=$(get_app_config_path "$app")
    if [[ ! -f "$user_config" ]]; then
        fail "MCP配置文件不存在: $user_config，请先在 $app 中安装MCP扩展"
    fi
    
    local normalized_config
    normalized_config=$(normalize_mcp_config "$config_file" "$app")
    
    if echo "$normalized_config" | jq -s '.[1] * .[0]' "$user_config" - > "$user_config.tmp" 2>/dev/null; then
        mv -f "$user_config.tmp" "$user_config"
        echo "true"
    else
        rm -f "$user_config.tmp"
        fail "配置合并失败"
    fi
}

delete_config() {
    local server_name="$1"
    local app="$2"
    local user_config
    user_config=$(get_app_config_path "$app")
    
    if [[ ! -f "$user_config" ]]; then
        fail "配置文件不存在"
    fi
    
    # 使用find_real_server_name查找真实的服务器名称
    local real_server_name
    real_server_name=$(find_real_server_name "$server_name" "$app")
    
    if [[ -z "$real_server_name" ]]; then
        fail "服务器 '$server_name' 不存在"
    fi
    
    if jq "del(.mcpServers.\"$real_server_name\")" "$user_config" > "$user_config.tmp" 2>/dev/null; then
        mv -f "$user_config.tmp" "$user_config"
        echo "true"
    else
        rm -f "$user_config.tmp"
        fail "删除操作失败"
    fi
}

query_mcp_in_all_apps() {
    local mcp_name="$1"
    
    # 查找配置文件
    local config_file
    config_file=$(find_mcp_config_file "$mcp_name")
    if [[ $? -ne 0 ]]; then
        json_error "本地找不到MCP: $mcp_name"
        return 1
    fi

    local app_list='['
    local first=true

    for app in "${!APP_CONFIG_PATHS[@]}"; do
        local display_name="${APP_DISPLAY_NAMES[$app]:-$app}"
        local mcp_status="removed"

        if is_app_installed "$app"; then
            local real_server_name
            real_server_name=$(find_real_server_name "$mcp_name" "$app" 2>/dev/null)
            
            if [[ $? -eq 0 ]] && [[ -n "$real_server_name" ]]; then
                mcp_status="added"
            fi
        fi

        if [[ "$first" == true ]]; then
            first=false
        else
            app_list+=','
        fi
        app_list+="{\"name\":\"$display_name\",\"status\":\"$mcp_status\"}"
    done

    app_list+=']'
    echo "$app_list"
    return 0
}

# == 命令行参数解析 ==
usage() {
    cat <<EOF
MCP配置管理工具  (模块化接口版)
用法: $0 <command> [参数]

命令:
  status <server_name> <app>       - 查询指定服务器在特定应用中的状态
  add <mcp_name> <app>             - 添加MCP配置到指定应用
  del <server_name> <app>          - 从指定应用删除MCP配置
  mcp-status <mcp_name>            - 查询指定MCP在所有应用中的配置状态
  help                             - 显示帮助

支持的应用:
  roo-code    - Roo Code (基于VSCodium)
  DeepChat    - DeepChat独立应用

示例:
  $0 status oeDeploy roo-code      # 查询oeDeploy在Roo Code中的状态
  $0 add oeDeploy roo-code         # 将oeDeploy添加到Roo Code
  $0 del mcp-oedp roo-code         # 从Roo Code删除mcp-oedp
  $0 mcp-status oeDeploy           # 查看oeDeploy在所有应用中的配置状态
EOF
}

if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

cmd=$1
shift

case "$cmd" in
    add)
        [[ $# -eq 2 ]] || fail "add 需要2个参数 <mcp_name> <app>"
        write_config "$1" "$2"
        ;;
    del)
        [[ $# -eq 2 ]] || fail "del 需要2个参数 <server_name> <app>"
        delete_config "$1" "$2"
        ;;
    mcp-status)
        [[ $# -eq 1 ]] || fail "mcp-status 需要1个参数 <mcp_name>"
        query_mcp_in_all_apps "$1"
        ;;
    help|*)
        usage
        ;;
esac

