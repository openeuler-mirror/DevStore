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

import axios from 'axios';
import type { AxiosResponse } from 'axios';
import i18n from '@/lang/i18n';
import {FALL_BACK_LANG} from '@/lang';

const {t} = i18n.global;

function i18nDataConverter(data: unknown): void {
  const lang = i18n.global.locale.value;
  function valJudge(o: Record<string, unknown>, k: string, val: unknown): void {
    if (typeof val === 'object' && val !== null) {
      if (
        Object.prototype.hasOwnProperty.call(val, 'zh') === true &&
        Object.prototype.hasOwnProperty.call(val, 'en') === true) {
        o[k] = val[lang] ?? val[FALL_BACK_LANG];
        if (o[k] === '') {
          o[k] = val[FALL_BACK_LANG];
        }
      } else {
        Object.entries(val).forEach(kv => {
          valJudge(val as Record<string, unknown>, kv[0], kv[1]);
        });
      }
    }
  }
  if (typeof data === 'object' && data !== null) {
    Object.entries(data).forEach(kv => {
      valJudge(data as Record<string, unknown>, kv[0], kv[1]);
    });
  }
}

// 创建一个 axios 实例
const service = axios.create({
  baseURL: 'http://localhost:28080', // 所有的请求地址前缀部分
  // baseURL: '', // 所有的请求地址前缀部分
  timeout: 120000, // 请求超时时间毫秒
  withCredentials: false, // 异步请求携带cookie（目前无跨域xhr，设置为false）
  headers: {
    // 设置后端需要的传参类型
    'Content-Type': 'application/json'
  }
});

// 添加响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse<any, any>) => {
    if (response.config.responseType === 'blob') {
      return response;
    }
    // axios 返回数据 data
    const { data } = response;
    // 2xx 范围内的状态码都会触发该函数。
    i18nDataConverter(data);
    return data;
  },
  (error) => {
    if (error && error.response) {
      let msg = error.response.data?.message ?? t('setup.netRequestAbnormal');
      if (msg === '') {
        msg = t('setup.netRequestAbnormal');
      }
      console.log(msg);
    }

    if (error && error.message && error.message.includes('timeout')) {
      console.log('netRequestTimeout');
    }
    return Promise.reject(error);
  }
);

export default service;
