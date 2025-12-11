/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-08-09
 * =================================================================================================================== */

import type { Router, RouteLocationNormalizedLoaded } from 'vue-router';

// 如果没有 icon 图片，生成背景色
export function generateIconBgColor(inputString: string): string {
  let hash = 0;
  for (let i = 0; i < inputString.length; i++) {
    hash = ((hash << 5) - hash) + inputString.charCodeAt(i);
    hash |= 0;
  }
  hash = Math.abs(hash);
  const r = (hash % 160) + 60;
  const g = ((hash >> 8) % 160) + 60;
  const b = (((hash >> 16) ^ inputString.length) % 160) + 60;
  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * 更新路由查询参数的工具函数
 * @param router - Vue Router 实例
 * @param route - 当前路由对象
 * @param updates - 要更新的查询参数对象
 * @returns Promise<void>
 */
export async function updateRouteQuery(
  router: Router,
  route: RouteLocationNormalizedLoaded,
  updates: Record<string, string | number | undefined>
): Promise<void> {
  const newQuery = { ...route.query };
  
  // 更新查询参数
  Object.entries(updates).forEach(([key, value]) => {
    if (value === undefined || value === '') {
      delete newQuery[key];
    } else {
      newQuery[key] = value.toString();
    }
  });
  
  await router.push({ path: route.path, query: newQuery });
}

/**
 * 获取当前系统用户名
 * @returns Promise<string> 返回用户名，如果获取失败返回 'unknown'
 */
export async function getCurrentUsername(): Promise<string> {
  try {
    // 检查是否在 Electron 环境中
    if (typeof window !== 'undefined' && (window as any).electronAPI) {
      const result = await (window as any).electronAPI.getUsername();
      if (result && result.success) {
        return result.username;
      }
      console.warn('Failed to get username from Electron:', result?.error);
    }
    
    // 如果不在 Electron 环境中或获取失败，返回默认值
    console.warn('Not in Electron environment or failed to get username, using fallback');
    return 'unknown';
  } catch (error) {
    console.error('Error getting username:', error);
    return 'unknown';
  }
}

// 导出语言检测相关函数
export { detectSystemLanguage, getSystemLanguages, isChineseLanguage } from './languageDetection';