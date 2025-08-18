/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-08-15
 * =================================================================================================================== */

import { watch } from 'vue';
import { ElMessage } from 'element-plus';

export interface StatusMessages {
  successMessage: string;
  removeMessage: string;
  failMessage: string;
}

export interface MessageConfig {
  duration: number;
  showClose: boolean;
}

/**
 * 创建通用状态变化监听器
 * @param statusGetter 获取状态值的函数
 * @param messages 消息配置对象
 * @param t 国际化翻译函数
 * @param config 消息显示配置
 */
export const createStatusWatcher = (
  statusGetter: () => string | undefined,
  messages: StatusMessages,
  t: (key: string) => string,
  config: MessageConfig = { duration: 3000, showClose: true }
) => {
  return watch(statusGetter, (newVal, oldVal) => {
    if (newVal !== oldVal && typeof oldVal !== 'undefined') {
      if ((oldVal === 'not yet' || oldVal === 'in process') && newVal === 'success') {
        ElMessage({
          type: 'success',
          message: t(messages.successMessage),
          duration: config.duration,
          showClose: config.showClose,
        });
      } else if (oldVal === 'success' && newVal === 'not yet') {
        ElMessage({
          type: 'success',
          message: t(messages.removeMessage),
          duration: config.duration,
          showClose: config.showClose,
        });
      } else if ((oldVal === 'not yet' || oldVal === 'in process') && newVal === 'fail') {
        ElMessage({
          type: 'warning',
          message: t(messages.failMessage),
          duration: config.duration,
          showClose: config.showClose,
        });
      }
    }
  });
};
