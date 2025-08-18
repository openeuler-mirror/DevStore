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
    <div class="layout">
      <!-- 导航栏 -->
      <div class="navbar">
        <el-menu
            class="navbar-menu"
            mode="horizontal">
          <el-menu-item index="1" class="dev-store">DevStore</el-menu-item>
          <el-menu-item index="2">{{ t('nav.userDoc') }}</el-menu-item>
          <el-menu-item index="3">{{ t('nav.devDoc') }}</el-menu-item>
          <el-sub-menu index="4" class="code-repository">
            <template #title>{{ t('nav.codeRepository') }}</template>
            <el-menu-item index="4-1"><a href="https://gitee.com/openeuler/mcp-servers">mcp-servers</a></el-menu-item>
            <el-menu-item index="4-2"><a href="https://gitee.com/openeuler/oeDeploy">oeDeploy</a></el-menu-item>
          </el-sub-menu>
          <el-menu-item index="5">{{ t('nav.feedback') }}</el-menu-item>
          <el-menu-item index="6" @click="isLogVisible = true">{{ t('nav.log') }}</el-menu-item>
        </el-menu>
      </div>

      <!-- 右侧更新时间 + 按钮 -->
      <div class="update-time">
        {{ t('nav.updateTime') }}{{ updateTime }}
        <el-icon class="sync"><IconLoad @click="handleSync" /></el-icon>
      </div>

      <!--  日志弹窗 -->
      <log-dialog v-if="isLogVisible" v-model="isLogVisible" type="DevStore" />

      <!-- 下方 slot -->
      <div class="main-slot">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { IconLoad } from '@computing/opendesign-icons';
import LogDialog from '@/views/components/LogDialog.vue';
import { syncData, type SyncResponse } from '@/api/index';
import { eventBus, EVENT_TYPES } from '@/utils/eventBus';

const {t} = useI18n();
const isLogVisible = ref<boolean>(false);
const MESSAGE_DURATION = 3000;

const updateTime = ref<string>('2025');
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
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error('sync', e);
  }
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
  justify-content: center;
  background-image: url("@/assets/img/background.svg");
  background-size: 100% auto;
  background-repeat: no-repeat;
  background-position: center top;
  background-attachment: fixed;

  .layout {
    padding: 0 24px;
    width: 100%;
    position: relative;
    min-width: 940px;
    max-width: 1440px;
    height: 100%;
    display: flex;
    flex-direction: column;

    .navbar {
      width: 100%;
      display: flex;
      justify-content: space-around;

      .navbar-menu {
        width: 100%;
        height: 56px;
        border: none;
        background-color: transparent;
        li {
          font-size: 14px;
          color: var(--o-text-color-primary);
        }
        .dev-store {
          font-weight: 600;
          font-size: 18px;
        }
        .el-menu-item a {
          color: var(--o-text-color-primary);
          text-decoration: none;
          font-size: 16px;
          &:hover {
            color: var(--o-text-color-primary);
          }
        }
      }
    }

    .update-time {
      margin-right: 8px;
      height: 56px;
      line-height: 56px;
      position: absolute;
      top: 0;
      right: 0;
      color: var(--o-text-color-tertiary);
      display: flex;
      align-items: center;
      .sync, .sync > svg{
        width: 24px;
        height: 24px;
        cursor: pointer;
      }
      .sync {
        margin-left: 8px;
      }
    }

    .main-slot {
      //flex: 1;
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
    &:hover {
      color: var(--o-text-color-primary) !important;
    }
    
    a {
      color: var(--o-text-color-primary) !important;
      text-decoration: none !important;
      font-size: 14px !important;
      display: block !important;
      width: 100% !important;
      padding: 0 20px !important;
      transition: color 0.3s ease !important;
      
      &:hover {
        color: var(--o-theme-color-primary-blue) !important;
      }
      
      &:visited {
        color: var(--o-text-color-primary) !important;
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

/* 链接通用样式 */
.el-sub-menu__title, .el-menu-item {
  a {
    color: var(--o-text-color-primary) !important;
    text-decoration: none !important;
    
    &:link, &:visited {
      color: var(--o-text-color-primary) !important;
      text-decoration: none !important;
    }
    
    &:hover, &:focus {
      color: var(--o-theme-color-primary-blue) !important;
      text-decoration: none !important;
    }
  }
}
</style>
