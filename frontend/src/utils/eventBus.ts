/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-08-12
 * =================================================================================================================== */

/**
 * 事件总线工具类
 * 用于组件间通信
 */
class EventBus {
  private events: { [key: string]: Function[] } = {};

  /**
   * 注册事件监听器
   * @param event 事件名称
   * @param callback 回调函数
   */
  on(event: string, callback: Function) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(callback);
  }

  /**
   * 触发事件
   * @param event 事件名称
   * @param data 传递的数据
   */
  emit(event: string, data?: any) {
    if (this.events[event]) {
      this.events[event].forEach(callback => callback(data));
    }
  }

  /**
   * 移除事件监听器
   * @param event 事件名称
   * @param callback 要移除的回调函数
   */
  off(event: string, callback?: Function) {
    if (!this.events[event]) return;
    
    if (callback) {
      this.events[event] = this.events[event].filter(cb => cb !== callback);
    } else {
      delete this.events[event];
    }
  }
}

// 创建全局事件总线实例
export const eventBus = new EventBus();

// 定义事件类型常量
export const EVENT_TYPES = {
  SYNC_SUCCESS: 'sync-success', // 同步成功事件
};