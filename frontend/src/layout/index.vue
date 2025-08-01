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
import { IconLoad } from '@computing/opendesign-icons';
import LogDialog from '@/views/components/LogDialog.vue';
import { syncData } from '@/api/index.ts';

const {t} = useI18n();
const isLogVisible = ref<boolean>(false);
const MESSAGE_DURATION = 3000;

const updateTime = ref<string>('2025');
// 点击右上角同步，更新同步时间
const handleSync = async () => {
  try {
    const res = await syncData();
    if (res && res.is_success) {
      // 显示更新时间
      updateTime.value = res.time;
      // 提示更新成功
      ElMessage.success({
        message: t('message.syncSuc'),
        duration: MESSAGE_DURATION,
        showClose: true,
      });
    } else if (res) {
      // 提示更新失败
      ElMessage.warning({
        message: t('message.syncFail'),
        duration: MESSAGE_DURATION,
        showClose: true,
      });
      console.log(res.message);
    }
  } catch (e) {
    console.error('sync', e);
  }
};

// 同步函数
const sync = async () => {
  try {
    const res = await syncData();
    if (res && res.is_success) {
      updateTime.value = res.time;
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
  height: 100%;
  display: flex;
  justify-content: center;
  background-color: rgba(245, 246, 249, 1);
  background-image: url("@/assets/img/background.svg");
  background-size: 100%;
  background-repeat: no-repeat;

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
          font-size: 16px;
          color: var(--o-text-color-primary);
        }
        .dev-store {
          font-weight: 600;
          font-size: 18px;
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
.code-repository {
  i {
    display: none;
  }
  div {
    color: white;
  }
}
</style>