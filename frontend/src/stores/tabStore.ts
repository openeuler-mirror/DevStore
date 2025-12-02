/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-12-02
 * =================================================================================================================== */

import { reactive, toRef, computed } from 'vue';

export interface Tab {
  id: string;
  title: string;
  route: {
    path: string;
    query?: Record<string, any>;
  };
}

interface TabStore {
  tabs: Tab[];
  activeTabId: string;
}

const tabStore = reactive<TabStore>({
  tabs: [{
    id: 'home',
    title: 'Home',
    route: { path: '/', query: { tag: 'mcp' } }
  }],
  activeTabId: 'home'
});

export function useTabStore() {
  const addTab = (tab: Tab) => {
    const existingTab = tabStore.tabs.find(t => t.id === tab.id);
    if (existingTab) {
      // 如果页签已存在，切换到该页签
      tabStore.activeTabId = tab.id;
    } else {
      // 否则新增页签
      tabStore.tabs.push(tab);
      tabStore.activeTabId = tab.id;
    }
  };

  const removeTab = (tabId: string) => {
    const index = tabStore.tabs.findIndex(t => t.id === tabId);
    if (index === -1) return;

    // 不允许删除最后一个页签
    if (tabStore.tabs.length === 1) return;

    tabStore.tabs.splice(index, 1);

    // 如果删除的是当前激活的页签，切换到相邻页签
    if (tabStore.activeTabId === tabId) {
      const newIndex = Math.max(0, index - 1);
      tabStore.activeTabId = tabStore.tabs[newIndex].id;
    }
  };

  const setActiveTab = (tabId: string) => {
    if (tabStore.tabs.find(t => t.id === tabId)) {
      tabStore.activeTabId = tabId;
    }
  };

  const updateCurrentTab = (route: { path: string; query?: Record<string, any> }) => {
    const currentTab = tabStore.tabs.find(t => t.id === tabStore.activeTabId);
    if (currentTab) {
      currentTab.route = route;
    }
  };

  const updateCurrentTabId = (newId: string) => {
    const currentTab = tabStore.tabs.find(t => t.id === tabStore.activeTabId);
    if (currentTab) {
      currentTab.id = newId;
      tabStore.activeTabId = newId;
    }
  };

  const updateTabTitle = (tabId: string, title: string) => {
    const tab = tabStore.tabs.find(t => t.id === tabId);
    if (tab) {
      tab.title = title;
    }
  };

  const reorderTabs = (fromIndex: number, toIndex: number) => {
    const [movedTab] = tabStore.tabs.splice(fromIndex, 1);
    tabStore.tabs.splice(toIndex, 0, movedTab);
  };

  const findHomeTab = () => {
    return tabStore.tabs.find(t => t.route.path === '/');
  };

  return {
    tabs: tabStore.tabs,
    activeTabId: computed(() => tabStore.activeTabId),
    addTab,
    removeTab,
    setActiveTab,
    updateCurrentTab,
    updateCurrentTabId,
    updateTabTitle,
    reorderTabs,
    findHomeTab
  };
}

