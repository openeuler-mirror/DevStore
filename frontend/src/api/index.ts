/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-07-30
 * =================================================================================================================== */

import httpRequest from './request';

// 同步数据响应接口
export interface SyncResponse {
  is_success: boolean;
  time?: string;
  message?: string;
}

// 查询列表响应接口
export interface QueryListResponse {
  is_success: boolean;
  data?: {
    results: ServerAndPluginInfoObj[];
    mcp_count: number;
    oedp_count: number;
  };
  message?: string;
}

export interface ServerAndPluginInfoObj {
  id: string | number;
  name: string;
  package_name?: string; // MCP 服务软件包名称
  version: string;
  updated_at: string;
  url: string;
  description: {
    default: string;
    zh: string;
    en: string;
  };
  icon: string;
  author: string;
  readme: string;
  tag: string;
  installed_status?: 'not yet' | 'in process' | 'success' | 'fail';
  download_status?: 'not yet' | 'in process' | 'success' | 'fail';
  app_list?: string[];
  action_list?: string[];
  cmd_list: string[];
  mcp_config?: string;
  config_yaml?: string;
}

export type Tag = 'mcp' | 'oedp';

const prefix = '/v1.0/';

// layout
// 更新插件
export function syncData(): Promise<SyncResponse> {
  return httpRequest({
    url: `${prefix}artifacts/sync/`,
    method: 'post',
  });
}

// 首页
// 获取 MCP Server / oeDeploy 插件 列表
export function queryList(params: { tag: Tag; pageSize: number; curPage: number; searchValue: string; sort: 'recommended' | 'newest' }): Promise<QueryListResponse> {
  return httpRequest({
    url: `${prefix}artifacts/`,
    method: 'get',
    params,
  });
}

// 获取日志响应接口
export interface LogResponse {
  is_success: boolean;
  log?: string;
  message?: string;
}

// layout / 详情页
// hl: wip 获取日志
export function fetchLog(params: { key: string }): Promise<LogResponse> {
  return httpRequest({
    url: `${prefix}artifacts/log/`,
    method: 'get',
    params,
  });
}

// 详情页
// 获取详情页信息
export function queryDetail(params: { tag: Tag; key: string }) {
  return httpRequest({
    url: `${prefix}artifacts/details/`,
    method: 'get',
    params,
  });
}


// 详情页 - mcp
// hl: wip 下载软件包
export function getPackage(params: { tag: Tag; key: string }) {
  return httpRequest({
    url: `${prefix}artifacts/mcp_install/`,
    method: 'post',
    params,
  });
}

// hl: wip 卸载软件包
export function deletePackage(params: { tag: Tag; key: string }) {
  return httpRequest({
    url: `${prefix}artifacts/mcp_uninstall/`,
    method: 'post',
    params,
  });
}

// hl: wip 智能体应用管理
export function mcpAgent(params: { action: 'add' | 'delete'; package_name: string; app_name: string }) {
  return httpRequest({
    url: `${prefix}artifacts/mcp_config_manage/`,
    method: 'post',
    params,
  });
}


// 详情页 - oedp
// 下载插件
export function getPlugin(params: { key: string }) {
  return httpRequest({
    url: `${prefix}artifacts/download_plugin/`,
    method: 'post',
    params,
  });
}

// 删除软件包
export function removePlugin(params: { key: string }) {
  return httpRequest({
    url: `${prefix}artifacts/delete_plugin/`,
    method: 'post',
    params,
  });
}

// 执行部署操作
export function issueAction(params: { key: string; action_name: string }) {
  return httpRequest({
    url: `${prefix}artifacts/plugin_action/`,
    method: 'post',
    params,
  });
}

// 获取、修改、还原 YAML
export function operateYaml(params: { key: string; operation: 'get' | 'set' | 'reset'; config_text: string }) {
  return httpRequest({
    url: `${prefix}artifacts/plugin_config/`,
    method: 'get',
    params,
  });
}
