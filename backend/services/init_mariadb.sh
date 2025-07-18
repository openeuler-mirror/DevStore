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

auto=$1
CONFIG_DIR="/etc/dev-store/mariadb"
INIT_MARIADB_CONFIG_FILE="${CONFIG_DIR}/init_mariadb.conf"
SERVICES_DIR="/var/lib/dev-store/services"

CURRENT_DIR=$(pwd)
source ${CURRENT_DIR}/log.sh

# 读取配置文件
function read_config_value {
    local key="$1"

    # 判断配置文件中 key 是否存在
    local item=$(grep "^${key} =" "${INIT_MARIADB_CONFIG_FILE}")
    if [[ -z "${item}" ]]; then
        error "The key '${key}' not found in the configuration file ${INIT_MARIADB_CONFIG_FILE}"
        exit 1
    fi

    # 判断配置文件中对应 key 的值是否存在
    local value=$(echo "${item}" | awk -F= '{print $2}' | sed 's/[[:space:]]*$//' | xargs)

    if [[ -n "${value}" ]]; then
        echo "${value}"
    else
        error "The value of key '${key}' is empty in the configuration file ${INIT_MARIADB_CONFIG_FILE}"
        exit 1
    fi
}

# 检查密码复杂度，密码至少包含8个字符,大小写字母、数字、特殊符号三种以上
function check_password_complexity()
{
  local variable_content=$1
  local complexity=0

  if [[ ${#variable_content} -ge 8 ]]; then
    complexity=$((${complexity}+1))
  else
    return 1
  fi

  if [[ "${variable_content}" =~ [[:upper:]] ]]; then
    complexity=$((${complexity}+1))
  fi

  if [[ "${variable_content}" =~ [[:lower:]] ]]; then
    complexity=$((${complexity}+1))
  fi

  if [[ "${variable_content}" =~ [[:digit:]] ]]; then
    complexity=$((${complexity}+1))
  fi

  if [[ "${variable_content}" =~ [[:punct:]] ]]; then
    complexity=$((${complexity}+1))
  fi

  unset variable_content
  if [[ "${complexity}" -ge 4 ]]; then
    return 0
  else
    return 1
  fi
}


# 配置MariaDB服务
function configure_mariadb()
{
  local auto=$1
  local Y_N

  # 交互式执行会询问 MariaDB 是否已被配置过，自动执行默认 MariaDB 没有被配置过
  if [ "${auto}" == "auto" ]; then
    Y_N="n"
  else
    read -p "Whether MariaDB is configured? [Y/n] (default: n) " Y_N
  fi
  # 判断 MariaDB 是否已被配置过，若已被配置过则跳过，若没有则开始配置
  if [[ "${Y_N}" == "y" || "${Y_N}" == "Y" ]]; then
    return
  elif [[ ! -n "${Y_N}" || "${Y_N}" == "N" || "${Y_N}" == "n" ]]; then
    # 启动 MariaDB 服务
    info "Starting the MariaDB service."
    systemctl start mariadb
    if [[ $? -ne 0 ]]; then
      error "Failed to start the MariaDB service."
      exit 1
    fi
    # 检查服务是否启动
    mariadb_status=$(systemctl is-active mariadb)
    if [[ "${mariadb_status}" == "active" ]]; then
      info "The MariaDB service is active."
    else
      error "The MariaDB service is inactive."
      exit 1
    fi
    # 设置为开机自启动服务
    systemctl enable mariadb
    if [[ $? -ne 0 ]]; then
      warn "Failed to enable the MariaDB service."
    fi

    # 检查防火墙是否启动，如果启动则检查 3306 端口是否在防火墙白名单中，如果不存在则添加到白名单中
    info "Start to check firewall."
    if systemctl is-active --quiet firewalld; then
      port_3306=$(firewall-cmd --query-port=3306/tcp)
      if [[ "${port_3306}" == "no" ]]; then
        port_3306=$(firewall-cmd --zone=public --add-port=3306/tcp --permanent)
        firewall-cmd --reload
      fi
      port_3306=$(firewall-cmd --query-port=3306/tcp)
      if [[ "${port_3306}" != "yes" ]]; then
        error "Failed to enable port 3306."
        exit 1
      fi
    fi
    info "Check firewall done."

    # 执行 mysql_secure_installation，进行 MariaDB 的安全配置
    info "Execute the command [mysql_secure_installation] to perform MariaDB security configuration."
    if [ "${auto}" == "auto" ]; then
      default_root_pw="\n"
      switch_unix_socket="n"
      set_root_pw="y"
      root_password="$(read_config_value 'root_password')"
      change_root_pw="n"
      remove_anonymous_users="y"
      disallow_root_login_remotely="n"
      remove_test_database_and_access_to_it="y"
      reload_privilege_tables="y"
      # 首次安装，mariadb 的 root 密码为空，需要设置 root 密码
      input_string="${default_root_pw}"
      input_string+="${switch_unix_socket}\n"
      input_string+="${set_root_pw}\n"
      input_string+="${root_password}\n"
      input_string+="${root_password}\n"
      input_string+="${remove_anonymous_users}\n"
      input_string+="${disallow_root_login_remotely}\n"
      input_string+="${remove_test_database_and_access_to_it}\n"
      input_string+="${reload_privilege_tables}\n"
      expect -c "
set timeout 5
spawn mysql_secure_installation
expect \"Enter current password for root (enter for none):\"
send \"${input_string}\"
expect {
  \"*Thanks for using MariaDB!*\" {
    exit 0
  }
  default {
    exit 1
  }
}
"
      return_code=$?
      if [[ "${return_code}" == "1" ]]; then
        echo ""
        error "Automatically configuring the mariadb fails, please try to configure manually."
        exit 1
      fi
    else
      mysql_secure_installation
    fi
    info "Perform MariaDB security configuration successfully."
    return
  else
    error "The input is invalid. Please input again."
    exit 1
  fi
}


# 检查自定义数据库名字复杂度，自定义数据库名字至少包含2个字符,大小写字母、下划线、数字两种以上
function check_database_name()
{
  local variable_content=$1
  local complexity=0

  if [[ "${variable_content}" =~ [[:upper:]] ]]; then
    complexity=$((${complexity}+1))
  fi

  if [[ "${variable_content}" =~ [[:lower:]] ]]; then
    complexity=$((${complexity}+1))
  fi

  if [[ "${variable_content}" =~ [[:digit:]] ]]; then
    complexity=$((${complexity}+1))
  fi

  if [[ "${variable_content}" =~ "_" ]]; then
    complexity=$((${complexity}+1))
  fi
  # 包含 a-zA-Z0-9_ 之外的字符都不符合要求
  if [[ "${variable_content}" =~ [^a-zA-Z0-9_] ]]; then
    complexity=0
  fi

  unset variable_content
  if [[ ${complexity} -ge 2 ]]; then
    return 0
  else
    return 1
  fi
}

info "Start to configure MariaDB for dev-store."
configure_mariadb "${auto}"
unset Y_N

# 输入或获取 dev_store 密码，并检查其复杂度是否符合要求
if [ "${auto}" == "auto" ]; then
  dev_store_passwd=$(read_config_value "dev_store_password")
  check_password_complexity ${dev_store_passwd}
  if [[ $? -ne 0 ]]; then
    error "The password must contain at least eight characters, including uppercase lowercase digits and special characters."
    error "The password of the dev_store user for MariaDB is invalid. Please change the value of dev_store_password in the ${INIT_MARIADB_CONFIG_FILE}."
    exit 1
  fi
else
  stty -echo
  while true
  do
    should_break=false
    for i in {1..5}; do
      read -p "Enter the password of dev_store user for MariaDB: " dev_store_passwd_01
      echo ""
      read -p "Confirm: " dev_store_passwd_02
      echo ""
      if [[ "${dev_store_passwd_01}" == "${dev_store_passwd_02}" ]]; then
        should_break=true
        break
      fi
      error "The provided passwords do not match. Please re-enter them for verification."
    done
    if [ ! ${should_break} ]; then
      stty echo
      exit 1
    fi
    dev_store_passwd=${dev_store_passwd_01}
    check_password_complexity ${dev_store_passwd}
    if [[ $? -ne 0 ]]; then
      error "The password must contain at least eight characters, including uppercase lowercase digits and special characters."
      error "The password of the dev_store user for MariaDB is invalid. Please input again."
    else
      break
    fi
  done
  stty echo
fi

# 获取自定义数据库名
while true
do
  warn "If the database name already exists, it will be overwritten."
  if [ "${auto}" == "auto" ]; then
    Y_N="Y"
  else
    read -p "Use default dev_store_db database? [Y/n] (default: Y) " Y_N
  fi
  # 使用默认
  if [[ ! -n "${Y_N}" || "${Y_N}" == "y" || "${Y_N}" == "Y" ]]; then
    mariadb_name=dev_store_db
    break
  elif [[ "${Y_N}" == "N" || "${Y_N}" == "n" ]]; then
    # 用户自定义数据库
    read -p "Please input the name of the database to be created: " mariadb_name
    check_database_name ${mariadb_name}
    if [[ $? -ne 0 ]]; then
      error "The database name must contain at least two types of characters, including uppercase lowercase underscores and digits."
      error "The input database name entered is invalid. Please input again."
    else
      break
    fi
  else
    error "The input is invalid. Please input again."
  fi
done
unset Y_N

# 创建用户 dev_store 以及自定义名称的数据库
if [ "${auto}" == "auto" ]; then
  root_password=$(read_config_value "root_password")
else
  stty -echo
  read -p "Enter the password of the root user of the MariaDB again: " root_password
  echo ""
  stty echo
fi
info "Start to create user dev_store and database ${mariadb_name}."
mysql -uroot -p${root_password} << EOF
DROP DATABASE IF EXISTS ${mariadb_name};
CREATE DATABASE IF NOT EXISTS ${mariadb_name} CHARACTER SET utf8 COLLATE utf8_bin;

DELETE FROM mysql.user WHERE User='dev_store';
DELETE FROM mysql.db WHERE User='dev_store';
flush privileges;
# dev_store 用户权限仅限操作自定义新创建的数据库
CREATE USER 'dev_store'@'localhost' IDENTIFIED BY '${dev_store_passwd}';
GRANT ALL ON ${mariadb_name}.* TO 'dev_store'@'localhost' IDENTIFIED BY '${dev_store_passwd}' WITH GRANT OPTION;
flush privileges;
EOF
if [[ $? -ne 0 ]]; then
  error "Failed to create user dev_store and database ${mariadb_name}."
  exit 1
fi
info "Create user dev_store and database ${mariadb_name} successfully."

unset root_password

# 更新 mariadb.conf 和加密 dev_store 用户的密码
python3 "${SERVICES_DIR}/modify_mariadb_config.py" ${mariadb_name}
if [[ $? -ne 0 ]]; then
  error "Failed to update ${CONFIG_DIR}/mariadb.conf."
  exit 1
fi
python3 "${SERVICES_DIR}/encrypt_mariadb_passwd.py" ${dev_store_passwd}
if [[ $? -ne 0 ]]; then
  error "Failed to encrypt password of user dev_store."
  exit 1
fi

unset dev_store_passwd

info "MariaDB is configured successfully."