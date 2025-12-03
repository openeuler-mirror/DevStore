<!-- Copyright (c) 2025 Huawei Technologies Co., Ltd. -->
<!-- oeDeploy is licensed under the Mulan PSL v2 .-->
<!-- You can use this software according to the terms and conditions of the Mulan PSL v2. -->
<!-- You may obtain a copy of Mulan PSL v2 at: -->
<!--   http://license.coscl.org.cn/MulanPSL2 -->
<!-- THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR -->
<!-- IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR -->
<!-- PURPOSE. -->
<!-- See the Mulan PSL v2 for more details. -->
<!-- Create: 2025-07-31 -->
<!-- =================================================================================================================== -->

<template>
  <div class="app-container">
    <!-- 顶部栏：多页签 + 窗口控制 -->
    <div class="titlebar">
      <div class="titlebar-left">
        <div class="app-title">DevStore</div>
        <div class="tabs-container">
          <div 
            v-for="(tab, index) in tabs" 
            :key="tab.id" 
            :class="['tab', { active: tab.id === activeTabId }]"
            :draggable="true"
            @click="switchTab(tab.id)"
            @dragstart="handleDragStart(index, $event)"
            @dragover.prevent="handleDragOver(index)"
            @drop="handleDrop(index)"
            @dragend="handleDragEnd">
            <span class="tab-title">{{ tab.title }}</span>
            <el-icon 
              v-if="tabs.length > 1"
              class="tab-close" 
              @click.stop="closeTab(tab.id)">
              <Close />
            </el-icon>
          </div>
        </div>
      </div>
      <div class="titlebar-right">
        <div class="window-control" @click="minimizeWindow">
          <el-icon><Minus /></el-icon>
        </div>
        <div class="window-control" @click="toggleMaximize">
          <el-icon><FullScreen /></el-icon>
        </div>
        <div class="window-control close-btn" @click="closeWindow">
          <el-icon><Close /></el-icon>
        </div>
      </div>
    </div>

    <div class="layout">
      <!-- 导航栏 -->
      <div class="navbar">
        <el-menu
            class="navbar-menu"
            mode="horizontal">
          <el-sub-menu index="2">
            <template #title>{{ t('nav.userDoc') }}</template>
            <el-menu-item index="2-1" @click="openLink('https://gitee.com/openeuler/DevStore/blob/master/README.md')">中文文档</el-menu-item>
            <el-menu-item index="2-2" @click="openLink('https://gitee.com/openeuler/DevStore/blob/master/README.en.md')">English Doc</el-menu-item>
          </el-sub-menu>
          <el-menu-item index="3">{{ t('nav.devDoc') }}</el-menu-item>
          <el-sub-menu index="4" class="code-repository">
            <template #title>{{ t('nav.codeRepository') }}</template>
            <el-menu-item index="4-1" @click="openLink('https://gitee.com/openeuler/DevStore')">DevStore</el-menu-item>
            <el-menu-item index="4-2" @click="openLink('https://gitee.com/openeuler/mcp-servers')">mcp-servers</el-menu-item>
            <el-menu-item index="4-3" @click="openLink('https://gitee.com/openeuler/oeDeploy')">oeDeploy</el-menu-item>
          </el-sub-menu>
          <el-menu-item index="5">{{ t('nav.feedback') }}</el-menu-item>
          <el-menu-item index="6" @click="isLogVisible = true">{{ t('nav.log') }}</el-menu-item>
        </el-menu>
        
        <!-- 右侧更新时间 + 按钮 -->
        <div class="update-time">
          {{ t('nav.updateTime') }}{{ updateTime }}
          <el-icon class="sync"><IconLoad @click="handleSync" /></el-icon>
        </div>
      </div>

      <!--  日志弹窗 -->
      <log-dialog v-if="isLogVisible" v-model="isLogVisible" type="DevStore" />

      <!-- 下方 slot -->
      <div class="main-slot">
        <router-view v-slot="{ Component }">
          <keep-alive :max="10">
            <component :is="Component" :key="keepAliveKey" />
          </keep-alive>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Close, Minus, FullScreen } from '@element-plus/icons-vue';
import { IconLoad } from '@computing/opendesign-icons';
import LogDialog from '@/views/components/LogDialog.vue';
import { syncData, type SyncResponse } from '@/api/index';
import { eventBus, EVENT_TYPES } from '@/utils/eventBus';
import { useTabStore } from '@/stores/tabStore';

const {t, locale} = useI18n();
const router = useRouter();
const route = useRoute();
const isLogVisible = ref<boolean>(false);
const MESSAGE_DURATION = 3000;

const updateTime = ref<string>('2025');

// 页签管理
const { tabs, activeTabId, addTab, removeTab, setActiveTab, updateCurrentTab, updateCurrentTabId, updateTabTitle, reorderTabs, findHomeTab } = useTabStore();

// 计算keep-alive的key：Home页使用固定key，Detail页使用path
const keepAliveKey = computed(() => {
  if (route.name === 'Home') {
    // Home组件使用固定key，但内部通过页签ID管理不同状态
    return 'home';
  }
  // Detail页使用path，确保不同的detail有独立的缓存
  return route.path;
});

// 页签拖拽
const draggedTabIndex = ref<number | null>(null);

const handleDragStart = (index: number, event: DragEvent) => {
  draggedTabIndex.value = index;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
  }
};

const handleDragOver = (index: number) => {
  if (draggedTabIndex.value !== null && draggedTabIndex.value !== index) {
    reorderTabs(draggedTabIndex.value, index);
    draggedTabIndex.value = index;
  }
};

const handleDrop = (index: number) => {
  // 拖拽已经在dragover中处理
};

const handleDragEnd = () => {
  draggedTabIndex.value = null;
};

// 切换页签
const switchTab = (tabId: string) => {
  setActiveTab(tabId);
  const tab = tabs.find(t => t.id === tabId);
  if (tab) {
    router.push({ path: tab.route.path, query: tab.route.query });
  }
};

// 关闭页签
const closeTab = (tabId: string) => {
  removeTab(tabId);
  // 切换到当前激活的页签
  const activeTab = tabs.find(t => t.id === activeTabId.value);
  if (activeTab) {
    router.push({ path: activeTab.route.path, query: activeTab.route.query });
  }
};

// 窗口控制
const minimizeWindow = () => {
  if (window.electronAPI?.minimizeWindow) {
    window.electronAPI.minimizeWindow();
  }
};

const toggleMaximize = () => {
  if (window.electronAPI?.toggleMaximize) {
    window.electronAPI.toggleMaximize();
  }
};

const closeWindow = () => {
  if (window.electronAPI?.closeWindow) {
    window.electronAPI.closeWindow();
  }
};

// 监听路由变化，更新当前页签的路由信息、ID和标题
watch(() => route.fullPath, () => {
  const currentTabId = activeTabId.value;
  
  // 根据路由类型更新ID和标题
  if (route.path === '/') {
    // Home页 - 只更新路由信息和标题，不改变页签ID
    // Home页签的ID由toHomePage方法或初始化时确定
    updateCurrentTab({ path: route.path, query: route.query });
    updateTabTitle(activeTabId.value, 'Home');
  } else if (route.name === 'McpServerDetail' || route.name === 'OedpPluginDetail') {
    // Detail页面 - 只有当页签ID匹配时才更新路由信息
    // 从路径中提取 tag 和 key
    const pathParts = route.path.split('/').filter(p => p);
    if (pathParts.length >= 2) {
      const tag = pathParts[0];
      const key = pathParts[1];
      const expectedTabId = `${tag}-${key}`;
      
      // 只有当前页签ID匹配时才更新路由信息
      if (currentTabId === expectedTabId) {
        updateCurrentTab({ path: route.path, query: route.query });
      }
    }
  }
}, { immediate: true });



// 点击右上角同步，更新同步时间
const handleSync = async () => {
  try {
    const res: SyncResponse = await syncData();
    if (res && res.is_success) {
      // 显示更新时间
      updateTime.value = res.time || '';
      // 提示更新成功
      ElMessage({
        type: 'success',
        message: t('message.syncSuc'),
        duration: MESSAGE_DURATION,
        showClose: true,
      });
      // 发送同步成功事件，触发Home页面立即刷新
      eventBus.emit(EVENT_TYPES.SYNC_SUCCESS);
    } else if (res) {
      // 提示更新失败
      ElMessage({
        type: 'warning',
        message: t('message.syncFail'),
        duration: MESSAGE_DURATION,
        showClose: true,
      });
      console.log(res.message);
    }
  } catch (e) {
    console.error('sync', e);
    // 添加异常情况的消息提示
    ElMessage({
      type: 'error',
      message: '同步过程中出现错误',
      duration: MESSAGE_DURATION,
      showClose: true,
    });
  }
};

// 同步函数
const sync = async () => {
  try {
    const res: SyncResponse = await syncData();
    if (res && res.is_success) {
      updateTime.value = res.time || '';
      // 发送同步成功事件，触发Home页面立即刷新
      eventBus.emit(EVENT_TYPES.SYNC_SUCCESS);
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error('sync', e);
  }
};

// 打开链接的公共方法
const openLink = (url: string) => {
  window.open(url, '_blank');
};

onMounted(async () => {
  // 首次打开，同步数据
  await sync();
});
</script>

<style lang="scss" scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-image: url("@/assets/img/background.svg");
  background-size: cover;
  background-repeat: no-repeat;
  background-position: center center;
  background-attachment: fixed;

  .titlebar {
    -webkit-app-region: drag;
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 40px;
    background-color: rgba(255, 255, 255, 0.95);
    border-bottom: 1px solid var(--o-background-color-quaternary-light);
    padding: 0 8px;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;

    .titlebar-left {
      display: flex;
      align-items: center;
      flex: 1;
      overflow: hidden;
      -webkit-app-region: drag;
      
      .app-title {
        -webkit-app-region: drag;
        font-size: 14px;
        font-weight: 600;
        padding: 0 12px;
        color: var(--o-text-color-primary);
      }

      .tabs-container {
        display: flex;
        align-items: center;
        gap: 4px;
        overflow-x: auto;
        flex: 1;
        -webkit-app-region: drag;

        &::-webkit-scrollbar {
          height: 4px;
        }

        .tab {
          -webkit-app-region: no-drag;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border-radius: 4px;
          background-color: transparent;
          cursor: pointer;
          white-space: nowrap;
          transition: background-color 0.2s;

          &:hover {
            background-color: var(--o-background-color-tertiary-light);
          }

          &.active {
            background-color: var(--o-background-color-quaternary-light);
          }

          .tab-title {
            font-size: 13px;
            color: var(--o-text-color-primary);
          }

          .tab-close {
            font-size: 14px;
            &:hover {
              color: var(--o-theme-color-primary-blue);
            }
          }
        }
      }
    }

    .titlebar-right {
      -webkit-app-region: no-drag;
      display: flex;
      align-items: center;

      .window-control {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        cursor: pointer;
        transition: background-color 0.2s;

        &:hover {
          background-color: rgba(0, 0, 0, 0.05);
        }

        &.close-btn:hover {
          background-color: #e81123;
          color: white;
        }

        .el-icon {
          font-size: 16px;
        }
      }
    }
  }

  .layout {
    padding: 40px 24px 0;
    width: 100%;
    position: relative;
    min-width: 940px;
    max-width: 1440px;
    height: 100%;
    display: flex;
    flex-direction: column;
    margin: 0 auto;

    .navbar {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;

      .navbar-menu {
        flex: 1;
        height: 56px;
        border: none;
        background-color: transparent;
        li {
          font-size: 14px;
          color: var(--o-text-color-primary);
        }
        .el-menu-item {
          cursor: pointer;
          &:hover {
            color: var(--o-theme-color-primary-blue);
          }
        }
      }

      .update-time {
        height: 56px;
        line-height: 56px;
        color: var(--o-text-color-tertiary);
        display: flex;
        align-items: center;
        flex-shrink: 0;
        white-space: nowrap;
        padding-left: 16px;
        .sync, .sync > svg{
          width: 24px;
          height: 24px;
          cursor: pointer;
        }
        .sync {
          margin-left: 8px;
        }
      }
    }
  }
}
</style>

<style lang="scss">
/* 代码仓库菜单样式 */
.code-repository {
  & > .el-sub-menu__title {
    font-size: 14px;
    color: var(--o-text-color-primary) !important;
  }
  .el-menu-item {
    font-size: 14px !important;
    color: var(--o-text-color-primary) !important;
    cursor: pointer !important;
    transition: color 0.3s ease !important;
    
    &:hover {
      color: var(--o-theme-color-primary-blue) !important;
    }
    
    &:focus {
      outline: none !important;
      color: var(--o-theme-color-primary-blue) !important;
    }
    
    &:active {
      color: var(--o-theme-color-primary-blue) !important;
    }
  }
}

/* Element UI 下拉菜单通用样式 */
.el-sub-menu .el-menu,
.el-sub-menu__drop-down,
.el-menu--vertical,
.el-popper .el-menu,
body .el-popper[data-popper-placement^="bottom"],
body .el-popper[data-popper-placement^="bottom"] .el-menu {
  background-color: var(--o-background-color-tertiary-light) !important;
  border: 2px solid var(--o-background-color-quaternary-light) !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

.el-sub-menu .el-menu .el-menu-item,
.el-sub-menu__drop-down .el-menu-item,
.el-menu--vertical .el-menu-item,
.el-popper .el-menu .el-menu-item,
body .el-popper[data-popper-placement^="bottom"] .el-menu-item {
  background-color: transparent !important;
  
  &:hover {
    background-color: var(--o-background-color-quaternary-light) !important;
  }
}


</style>
