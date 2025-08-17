/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-08-16
 * =================================================================================================================== */

import type { LangKey } from '@/lang';

/**
 * 检测系统语言
 * 如果是中文类的语言，返回 'zh'，否则返回 'en'
 * @returns {LangKey} 检测到的语言代码
 */
export function detectSystemLanguage(): LangKey {
  try {
    // 优先检查浏览器语言设置
    const browserLanguage = navigator.language || navigator.languages?.[0];
    
    if (browserLanguage) {
      // 检查是否为中文相关语言
      const lowerLang = browserLanguage.toLowerCase();
      if (lowerLang.startsWith('zh') || lowerLang.includes('chinese')) {
        return 'zh';
      }
    }

    // 在 Electron 环境中，也可以检查系统语言环境变量
    if (typeof window !== 'undefined' && (window as any).electronAPI) {
      try {
        // 如果有 Electron API，可以尝试获取系统语言
        const systemLocale = (window as any).electronAPI?.getSystemLocale?.();
        if (systemLocale) {
          const lowerLocale = systemLocale.toLowerCase();
          if (lowerLocale.startsWith('zh') || lowerLocale.includes('chinese')) {
            return 'zh';
          }
        }
      } catch (error) {
        console.warn('Failed to get system locale from Electron:', error);
      }
    }

    // 默认返回英文
    return 'en';
  } catch (error) {
    console.warn('Failed to detect system language:', error);
    return 'en';
  }
}

/**
 * 获取系统支持的语言（用于备选方案）
 * @returns {string[]} 支持的语言列表
 */
export function getSystemLanguages(): string[] {
  try {
    if (navigator.languages) {
      return Array.from(navigator.languages);
    }
    if (navigator.language) {
      return [navigator.language];
    }
    return ['en'];
  } catch (error) {
    console.warn('Failed to get system languages:', error);
    return ['en'];
  }
}

/**
 * 检查指定语言是否为中文类语言
 * @param {string} language 语言代码
 * @returns {boolean} 是否为中文类语言
 */
export function isChineseLanguage(language: string): boolean {
  if (!language) return false;
  const lowerLang = language.toLowerCase();
  return lowerLang.startsWith('zh') || 
         lowerLang.includes('chinese') ||
         lowerLang === 'cn' ||
         lowerLang.startsWith('zh-cn') ||
         lowerLang.startsWith('zh-tw') ||
         lowerLang.startsWith('zh-hk');
}
