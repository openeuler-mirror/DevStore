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
  <div class="detail-page">
    <div class="detail-upper">
      <!-- crumb: 点击 crumbs 回到首页（server / plugin） -->
      <el-breadcrumb class="upper-crumbs" separator="/">
        <!-- MCP Server / oeDeploy 插件 -->
        <el-breadcrumb-item class="tag" @click="toHomePage">{{ tag === 'mcp' ? t('home.mcpServer') : t('home.oeDeployPlugin') }}</el-breadcrumb-item>
        <el-breadcrumb-item class="name">{{ itemDetail.name }}</el-breadcrumb-item>
      </el-breadcrumb>
      <!-- 上方 信息 -->
      <div class="display-card">
        <div class="display-card-top">
          <!-- 图标 -->
          <div class="display-card-icon">
            <img v-if="itemDetail.icon" :src="'data:image/png;base64,' + itemDetail.icon" :alt="itemDetail.name">
            <div v-else
                :style="{ backgroundColor: itemDetail.name ? generateIconBgColor(itemDetail.name) : 'rgb(125, 125, 125)'}">
              {{ itemDetail.name ? itemDetail.name.slice(0, 2).toUpperCase() : 'icon' }}
            </div>
          </div>
          <div class="display-card-top-info">
            <!-- 名称 -->
            <div class="display-card-id">{{ itemDetail.name }}</div>
            <div class="display-card-tag-version">
              <!-- 分类 -->
              <div class="display-card-tag">{{ itemDetail.tag }}</div>
              <!-- 版本 -->
              <div class="display-card-version">{{ itemDetail.version }}</div>
            </div>
          </div>
        </div>
        <!-- 描述 -->
        <div class="display-card-desc">
          {{ itemDetail.description?.zh || itemDetail.description?.en || itemDetail.description?.default || t('home.noDesc') }}
        </div>
        <div class="display-card-author-time">
          <!-- 作者 -->
          <div v-if="itemDetail.author" class="display-card-author">{{ itemDetail.author ? `@${itemDetail.author}` : '' }}</div>
          <!-- 时间 -->
          <div class="display-card-time">{{ itemDetail.updated_at }}</div>
        </div>
      </div>
    </div>

    <!-- 下方 使用说明 + 安装/部署 -->
    <div class="detail-lower">
      <!-- 下左 使用说明 -->
      <div class="detail-doc" v-html="compiledMarkdown"></div>
      <!-- 下右 安装/部署 -->
      <div class="detail-deploy">
        <el-tabs v-model="activeName" class="demo-tabs">
          <el-tab-pane
              v-for="(tab, index) in tabs"
              :key="index"
              :label="tab.label"
              :name="tab.name">
            <component
                :is="tab.component"
                :name="itemDetail.name"
                :key-value="key"
                :install-status="itemDetail.installed_status"
                :app-list="itemDetail.app_list"
                :cmd-list="itemDetail.cmd_list"
                :mcp-json="itemDetail.mcp_json"
                :download-status="itemDetail.download_status"
                :action-list="itemDetail.action_list"
                :install-package="installPackage"
                :uninstall-package="uninstallPackage"
                :add-app="addApp"
                :delete-app="deleteApp"
                :get-detail="getDetail" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import {
  queryDetail,
  getPackage,
  deletePackage,
  addAgent,
  deleteAgent,
  ServerAndPluginInfoObj,
  Tag,
} from '@/api/index.ts';

import McpQuick from '@/views/components/McpQuick.vue';
import McpCli from '@/views/components/McpCli.vue';
import OedpQuick from '@/views/components/OedpQuick.vue';
import OedpCli from '@/views/components/OedpCli.vue';

// 当前页面 url 里，包含了 tag + key
const route = useRoute();
const router = useRouter();
const {t} = useI18n();

const tag = ref<Tag>(route.name === 'McpServerDetail' ? 'mcp' : 'oedp');
const key = ref<string>(route.params.key);

// 是否支持 OEDP 快捷部署
const supportOedpQuick = ref<boolean>(false);

// 点击 crumbs 回到首页
const toHomePage = () => {
  router.push({
    path: '/',
    query: {
      tag: tag.value
    }
  });
};

// 根据当前 tag，判断下右显示 安装/部署
const tabs = computed(() => {
  // OEDP 仅显示 命令行部署
  if (supportOedpQuick.value === false) {
    return [
      { label: t('detail.cliDeploy'), name: 'oedp-cli', component: OedpCli }
    ];
  }
  return tag.value === 'mcp' ?
    // MCP 快捷安装 + 命令行安装
    [
      { label: t('detail.quickInstall'), name: 'mcp-click', component: McpQuick },
      { label: t('detail.cliInstall'), name: 'mcp-cli', component: McpCli }
    ] :
    // OEDP 快捷部署 + 命令行部署
    [
      { label: t('detail.quickDeploy'), name: 'oedp-click', component: OedpQuick },
      { label: t('detail.cliDeploy'), name: 'oedp-cli', component: OedpCli }
    ];
});

// 下右当前显示的 tab
const activeName = ref('');
watch(tabs, (newTabs) => {
  activeName.value = newTabs[0].name;
}, { immediate: true });

// markdown
const compiledMarkdown = ref('');
// 当前页面承接信息的变量
const itemDetail = ref<ServerAndPluginInfoObj>({});
// 提示 message 持续时间
const MESSAGE_DURATION = 3000;

// 获取详情页信息
const getDetail = async () => {
  try {
    const res = await queryDetail({tag: tag.value, key: key.value});
    if (res && res.is_success) {
      itemDetail.value = res.data;
      // 处理 md
      const dirtyHtml = marked.parse(itemDetail.value.readme);
      compiledMarkdown.value = DOMPurify.sanitize(dirtyHtml);
      // 判断是否支持 oedp 快捷部署
      supportOedpQuick.value = itemDetail.value.localhost_available;
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error(e);
  }
};

// 如果没有 icon 图片，生成背景色
function generateIconBgColor(inputString: string): string {
  let hash = 0;
  for (let i = 0; i < inputString.length; i++) {
    hash = ((hash << 5) - hash) + inputString.charCodeAt(i);
    hash |= 0;
  }
  hash = Math.abs(hash);
  const r = (hash % 128) + 1;
  const g = ((hash >> 8) % 128) + 1;
  const b = (((hash >> 16) ^ inputString.length) % 128) + 1;
  return `rgb(${r}, ${g}, ${b})`;
}

// MCP
// 下载软件包
const installPackage = async () => {
  try {
    const res = await getPackage({ tag: tag.value, key: key.value });
    if (res && res.is_success) {
      await getDetail();
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error(e);
  }
};

// 卸载软件包
const uninstallPackage = async () => {
  try {
    const res = await deletePackage({ tag: tag.value, key: key.value });
    if (res && res.is_success) {
      await getDetail();
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error(e);
  }
};

// 添加到智能体应用
const addApp = async (name: string) => {
  try {
    const res = await addAgent({ tag: tag.value, key: key.value, agent: name });
    if (res && res.is_success) {
      await getDetail();
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error(e);
  }
};

// 删除智能体应用
const deleteApp = async (name: string) => {
  try {
    const res = await deleteAgent({ tag: tag.value, key: key.value, agent: name });
    if (res && res.is_success) {
      await getDetail();
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error(e);
  }
};

let intervalId = null;

// 轮询
onMounted(async () => {
  // 立即执行一次
  await getDetail();

  // 启动轮询
  intervalId = setInterval(async () => {
    await getDetail();
  }, 2000);
});

// 监听 download_status 变化
watch(
  () => itemDetail.value.download_status,
  (newVal, oldVal) => {
    if (newVal !== oldVal && typeof oldVal !== 'undefined') {
      if ((oldVal === 'not yet' || oldVal === 'in process') && newVal === 'success') {
        // 下载成功
        ElMessage.success({
          message: t('message.downloadSuc'),
          duration: MESSAGE_DURATION,
          showClose: true,
        });
      } else if (oldVal === 'success' && newVal === 'not yet') {
        // 删除成功
        ElMessage.success({
          message: t('message.deleteSuc'),
          duration: MESSAGE_DURATION,
          showClose: true,
        });
      } else if ((oldVal === 'not yet' || oldVal === 'in process') && newVal === 'fail') {
        // 下载失败
        ElMessage.warning({
          message: t('message.downloadFail'),
          duration: MESSAGE_DURATION,
          showClose: true,
        });
      }
    }
  }
);

// 监听 action_list 中任意项的 status 变化
watch(
  () => itemDetail.value?.action_list?.map(item => item.status) ?? [],
  (newVal, oldVal) => {
    newVal.forEach((status, index) => {
      if (status !== oldVal[index] && typeof oldVal[index] !== 'undefined') {
        if ((oldVal[index] === 'not yet' || oldVal[index] === 'in process') && status === 'success') {
          // 执行成功
          ElMessage.success({
            message: t('message.executeSuc'),
            duration: MESSAGE_DURATION,
            showClose: true,
          });
        } else if ((oldVal[index] === 'not yet' || oldVal[index] === 'in process') && status === 'fail') {
          // 执行失败
          ElMessage.warning({
            message: t('message.executeFail'),
            duration: MESSAGE_DURATION,
            showClose: true,
          });
        }
      }
    });
  }
);

// 页面卸载时清除定时器
onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
});
</script>

<style scoped lang="scss">
.detail-page {
  height: 100%;
  padding: 16px 0 24px;
  display: flex;
  flex-direction: column;
  .upper-crumbs {
    .name {
      :deep(.el-breadcrumb__inner) {
        font-weight: 700;
      }
    }
    margin-bottom: 16px;
  }

  .display-card {
    margin-bottom: 16px;
    padding: 16px;
    border-radius: 8px;
    background-color: var(--o-background-color-secondary-light);
    .display-card-top {
      display: flex;
      margin-bottom: 16px;
      .display-card-icon {
        width: 48px;
        height: 48px;
        margin-right: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        img {
          max-width: 48px;
          max-height: 48px;
          width: auto;
          height: auto;
          border-radius: 50%;
        }
        div {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          line-height: 48px;
          text-align: center;
          font-size: 16px;
          color: var(--o-background-color-primary-light);
        }
      }
      .display-card-top-info {
        .display-card-id {
          height: 32px;
          font-size: 24px;
          line-height: 32px;
          font-weight: 700;
          margin-bottom: 8px;
        }
        .display-card-tag-version {
          display: flex;
          .display-card-tag, .display-card-version {
            font-size: 12px;
            font-weight: 500;
            line-height: 16px;
            padding: 0 4px;
            border-radius: 2px;
          }
          .display-card-tag {
            color: rgba(0, 119, 255, 1);
            background: rgba(0, 119, 255, 0.2);
          }
          .display-card-version {
            color: var(--o-text-color-secondary);
            background: var(--o-background-color-tertiary-light);
            margin-left: 8px;
          }
        }
      }
    }

    .display-card-desc {
      line-height: 22px;
      margin-bottom: 16px;
      color: var(--o-text-color-secondary);
    }

    .display-card-author-time {
      display: flex;
      color: var(--o-text-color-tertiary);
      div {
        height: 16px;
        line-height: 16px;
        font-size: 12px;
        margin-right: 8px;
      }
    }
  }
}

.detail-lower {
  flex: 1;
  display: flex;
  .detail-doc {
    flex: 2;
    margin-right: 16px;
    padding: 16px 16px 16px 40px;
    border-radius: 8px;
    background-color: var(--o-background-color-secondary-light);
    font-size: 14px;
    line-height: 22px;
    h1, h2, h3, h4, h5, h6, ol, ul, li, span, div, p {
      margin-bottom: 8px;
    }
  }
  .detail-deploy {
    height: 100%;
    flex: 1;
    position: sticky;
    top: 0;
    min-width: 300px;
    max-width: 472px;
    max-height: 100vh;
    padding: 8px 16px 16px;
    border-radius: 8px;
    background-color: var(--o-background-color-secondary-light);
    :deep(.el-tabs__item) {
      font-size: 14px;
      height: 32px;
    }
    :deep(.el-tab-pane) {
      padding-top: 16px;
    }
    :deep(.el-tabs), :deep(.el-tabs__content), :deep(.el-tab-pane), .mcp-click, .mcp-cli, .oedp-click, .oedp-cli {
      height: 100%;
    }
  }
}
</style>

<style lang="scss">
.detail-lower > .detail-doc {
  h1, h2, h3, h4, h5, h6, ol, ul, li, span, div, p, code, tt, table, th, td, tr, thead, blockquote, hr, img {
    margin-bottom: 8px;
  }
  h1, h2, h3, h4, h5, h6 {
    margin-left: -16px;
    font-weight: 700;
  }
  h1 {
    font-size: 18px;
    line-height: 24px;
  }
  code {
    font-family: monospace;
  }
  a {
    color: var(--o-theme-color-primary-blue);
  }
}
</style>