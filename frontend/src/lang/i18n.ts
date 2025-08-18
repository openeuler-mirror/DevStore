/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-07-31
 * =================================================================================================================== */

import { createI18n } from 'vue-i18n'; //引入vue-i18n组件
import messages from './index';
import { detectSystemLanguage } from '@/utils/languageDetection';

// 检测系统语言
const systemLanguage = detectSystemLanguage();

const i18n = createI18n({
  fallbackLocale: 'en',//预设语言环境
  globalInjection: true,
  locale: systemLanguage, // 根据系统语言自动设置
  messages // 本地化的语言环境信息
});

export default i18n;
