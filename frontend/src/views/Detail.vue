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
              <div class="display-card-tag">{{ itemDetail.tag?.toUpperCase() }}</div>
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
                :mcp-json="itemDetail.mcp_config"
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
import { ElMessage } from 'element-plus';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import {
  queryDetail,
  getPackage,
  deletePackage,
  mcpAgent,
  ServerAndPluginInfoObj,
  Tag,
} from '@/api/index.ts';
import { generateIconBgColor, getCurrentUsername } from '@/utils/index.ts';
import { createStatusWatcher } from '@/utils/statusWatcher';

import McpQuick from '@/views/components/McpQuick.vue';
import McpCli from '@/views/components/McpCli.vue';
import OedpQuick from '@/views/components/OedpQuick.vue';
import OedpCli from '@/views/components/OedpCli.vue';

// 当前页面 url 里，包含了 tag + key
const route = useRoute();
const router = useRouter();
const {t} = useI18n();

const tag = ref<Tag>(route.name === 'McpServerDetail' ? 'mcp' : 'oedp');
const key = ref<string>(Array.isArray(route.params.key) ? route.params.key[0] : route.params.key || '');

// 是否支持 OEDP 快捷部署
const supportOedpQuick = ref<boolean>(false);

// 点击 crumbs 回到首页
const toHomePage = () => {
  // 从当前路由或者sessionStorage中恢复Home页面的状态
  const homeState = sessionStorage.getItem('homePageState');
  let homeQuery: any = { tag: tag.value };
  
  if (homeState) {
    try {
      const parsedState = JSON.parse(homeState);
      homeQuery = {
        tag: tag.value,
        pageSize: parsedState.pageSize || '10',
        curPage: parsedState.curPage || '1',
        searchValue: parsedState.searchValue || '',
        sort: parsedState.sort || 'rec'
      };
    } catch (e) {
      console.error('Failed to parse home page state:', e);
    }
  }
  
  router.push({
    path: '/',
    query: homeQuery
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
const itemDetail = ref<Partial<ServerAndPluginInfoObj>>({});
// 提示 message 持续时间
const MESSAGE_DURATION = 3000;

// 获取详情页信息
const getDetail = async () => {
  try {
    const username = await getCurrentUsername();
    const res = await queryDetail({tag: tag.value, key: key.value, user_name: username});
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
const addApp = async (appName: string) => {
  try {
    const username = await getCurrentUsername();
    const res = await mcpAgent({ 
      action: 'add', 
      package_name: itemDetail.value.package_name || '', 
      app_name: appName,
      user_name: username
    });
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
const deleteApp = async (appName: string) => {
  try {
    const username = await getCurrentUsername();
    const res = await mcpAgent({ 
      action: 'delete', 
      package_name: itemDetail.value.package_name || '', 
      app_name: appName,  
      user_name: username
    });
    if (res && res.is_success) {
      await getDetail();
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error(e);
  }
};

let intervalId: NodeJS.Timeout | null = null;

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
createStatusWatcher(
  () => itemDetail.value.download_status,
  {
    successMessage: 'message.downloadSuc',
    removeMessage: 'message.deleteSuc', 
    failMessage: 'message.downloadFail'
  },
  t,
  { duration: MESSAGE_DURATION, showClose: true }
);

// 监听 installed_status 变化
createStatusWatcher(
  () => itemDetail.value.installed_status,
  {
    successMessage: 'message.installSuc',
    removeMessage: 'message.uninstallSuc',
    failMessage: 'message.installFail'
  },
  t,
  { duration: MESSAGE_DURATION, showClose: true }
);

// 监听 action_list 中任意项的 status 变化
watch(
  () => itemDetail.value?.action_list?.map(item => item.status) ?? [],
  (newVal, oldVal) => {
    newVal.forEach((status, index) => {
      if (status !== oldVal[index] && typeof oldVal[index] !== 'undefined') {
        if ((oldVal[index] === 'not yet' || oldVal[index] === 'in process') && status === 'success') {
          // 执行成功
          ElMessage({
            type: 'success',
            message: t('message.executeSuc'),
            duration: MESSAGE_DURATION,
            showClose: true,
          });
        } else if ((oldVal[index] === 'not yet' || oldVal[index] === 'in process') && status === 'fail') {
          // 执行失败
          ElMessage({
            type: 'warning',
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
          font-size: 24px;
          font-weight: 700;
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
    /* 添加文本换行和溢出处理 */
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
    overflow-x: auto;
    min-width: 0; /* 允许flex item收缩到内容尺寸以下 */
    h1, h2, h3, h4, h5, h6, ol, ul, li, span, div, p {
      margin-bottom: 8px;
    }
  }
  .detail-deploy {
    flex: 1;
    position: sticky;
    top: 0;
    min-width: 300px;
    max-width: 472px;
    max-height: 100vh;
    padding: 8px 16px 16px;
    border-radius: 8px;
    background-color: var(--o-background-color-secondary-light);
    display: flex;
    flex-direction: column;
    :deep(.el-tabs__item) {
      font-size: 14px;
      height: 32px;
    }
    :deep(.el-tab-pane) {
      padding-top: 16px;
    }
    :deep(.el-tabs) {
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    :deep(.el-tabs__content) {
      flex: 1;
      overflow-y: auto;
      min-height: 0;
    }
    :deep(.el-tab-pane) {
      height: auto;
      min-height: 100%;
    }
    .mcp-click, .mcp-cli, .oedp-click, .oedp-cli {
      height: auto;
      min-height: 100%;
    }
  }
}
</style>

<style lang="scss">
.detail-lower > .detail-doc {
  /* GitHub Markdown 样式移植 */
  color-scheme: light;
  -ms-text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
  font-family: -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji";
  font-size: 16px;
  line-height: 1.5;
  word-wrap: break-word;

  /* 基础排版 */
  h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    margin-left: -16px;
    font-weight: 600;
    line-height: 1.25;
  }

  h1 {
    margin: .67em 0;
    font-weight: 600;
    padding-bottom: .3em;
    font-size: 2em;
    border-bottom: 1px solid #d1d9e0b3;
  }

  h2 {
    font-weight: 600;
    padding-bottom: .3em;
    font-size: 1.5em;
    border-bottom: 1px solid #d1d9e0b3;
  }

  h3 {
    font-weight: 600;
    font-size: 1.25em;
  }

  h4 {
    font-weight: 600;
    font-size: 1em;
  }

  h5 {
    font-weight: 600;
    font-size: .875em;
  }

  h6 {
    font-weight: 600;
    font-size: .85em;
    color: #59636e;
  }

  p {
    margin-top: 0;
    margin-bottom: 1rem;
  }

  /* 链接样式 */
  a {
    background-color: transparent;
    color: #0969da;
    text-decoration: none;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  a:hover {
    text-decoration: underline;
  }

  /* 文本格式化 */
  b, strong {
    font-weight: 600;
  }

  mark {
    background-color: #fff8c5;
    color: #1f2328;
  }

  small {
    font-size: 90%;
  }

  /* 引用块 */
  blockquote {
    margin: 0 0 1rem 0;
    padding: 0 1em;
    color: #59636e;
    border-left: .25em solid #d1d9e0;
  }

  blockquote>:first-child {
    margin-top: 0;
  }

  blockquote>:last-child {
    margin-bottom: 0;
  }

  /* 列表样式 */
  ul, ol {
    margin-top: 0;
    margin-bottom: 1rem;
    padding-left: 2em;
  }

  ol ol, ul ol {
    list-style-type: lower-roman;
  }

  ul ul ol, ul ol ol, ol ul ol, ol ol ol {
    list-style-type: lower-alpha;
  }

  li>p {
    margin-top: 1rem;
  }

  li+li {
    margin-top: .25em;
  }

  /* 代码样式 */
  code, tt {
    padding: .2em .4em;
    margin: 0;
    font-size: 85%;
    white-space: break-spaces;
    background-color: #818b981f;
    border-radius: 6px;
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
  }

  code br, tt br {
    display: none;
  }

  pre {
    margin-top: 0;
    margin-bottom: 1rem;
    padding: 1rem;
    overflow: auto;
    font-size: 85%;
    line-height: 1.45;
    color: #1f2328;
    background-color: #f6f8fa;
    border-radius: 6px;
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
    word-wrap: normal;
  }

  pre code, pre tt {
    display: inline;
    max-width: auto;
    padding: 0;
    margin: 0;
    overflow: visible;
    line-height: inherit;
    word-wrap: normal;
    background-color: transparent;
    border: 0;
    font-size: 100%;
  }

  /* 键盘输入样式 */
  kbd {
    display: inline-block;
    padding: 0.25rem;
    font: 11px ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
    line-height: 10px;
    color: #1f2328;
    vertical-align: middle;
    background-color: #f6f8fa;
    border: solid 1px #d1d9e0b3;
    border-bottom-color: #d1d9e0b3;
    border-radius: 6px;
    box-shadow: inset 0 -1px 0 #d1d9e0b3;
  }

  /* 表格样式 */
  table {
    border-spacing: 0;
    border-collapse: collapse;
    display: block;
    width: max-content;
    max-width: 100%;
    overflow: auto;
    font-variant: tabular-nums;
    margin-bottom: 1rem;
  }

  table th {
    font-weight: 600;
  }

  table th, table td {
    padding: 6px 13px;
    border: 1px solid #d1d9e0;
  }

  table td>:last-child {
    margin-bottom: 0;
  }

  table tr {
    background-color: #ffffff;
    border-top: 1px solid #d1d9e0b3;
  }

  table tr:nth-child(2n) {
    background-color: #f6f8fa;
  }

  table img {
    background-color: transparent;
  }

  /* 分隔线 */
  hr {
    box-sizing: content-box;
    overflow: hidden;
    background: transparent;
    border-bottom: 1px solid #d1d9e0b3;
    height: .25em;
    padding: 0;
    margin: 1.5rem 0;
    background-color: #d1d9e0;
    border: 0;
  }

  hr::before {
    display: table;
    content: "";
  }

  hr::after {
    display: table;
    clear: both;
    content: "";
  }

  /* 图片样式 */
  img {
    border-style: none;
    max-width: 100%;
    height: auto;
    box-sizing: content-box;
  }

  img[align=right] {
    padding-left: 20px;
  }

  img[align=left] {
    padding-right: 20px;
  }

  /* 定义列表 */
  dl {
    padding: 0;
    margin-bottom: 1rem;
  }

  dl dt {
    padding: 0;
    margin-top: 1rem;
    font-size: 1em;
    font-style: italic;
    font-weight: 600;
  }

  dl dd {
    padding: 0 1rem;
    margin-bottom: 1rem;
    margin-left: 0;
  }

  /* 任务列表 */
  .task-list-item {
    list-style-type: none;
  }

  .task-list-item label {
    font-weight: 400;
  }

  .task-list-item.enabled label {
    cursor: pointer;
  }

  .task-list-item+.task-list-item {
    margin-top: 0.25rem;
  }

  .task-list-item-checkbox {
    margin: 0 .2em .25em -1.4em;
    vertical-align: middle;
  }

  /* 警告框样式 */
  .markdown-alert {
    padding: 0.5rem 1rem;
    margin-bottom: 1rem;
    color: inherit;
    border-left: .25em solid #d1d9e0;
  }

  .markdown-alert>:first-child {
    margin-top: 0;
  }

  .markdown-alert>:last-child {
    margin-bottom: 0;
  }

  .markdown-alert .markdown-alert-title {
    display: flex;
    font-weight: 500;
    align-items: center;
    line-height: 1;
  }

  .markdown-alert.markdown-alert-note {
    border-left-color: #0969da;
  }

  .markdown-alert.markdown-alert-note .markdown-alert-title {
    color: #0969da;
  }

  .markdown-alert.markdown-alert-important {
    border-left-color: #8250df;
  }

  .markdown-alert.markdown-alert-important .markdown-alert-title {
    color: #8250df;
  }

  .markdown-alert.markdown-alert-warning {
    border-left-color: #9a6700;
  }

  .markdown-alert.markdown-alert-warning .markdown-alert-title {
    color: #9a6700;
  }

  .markdown-alert.markdown-alert-tip {
    border-left-color: #1a7f37;
  }

  .markdown-alert.markdown-alert-tip .markdown-alert-title {
    color: #1a7f37;
  }

  .markdown-alert.markdown-alert-caution {
    border-left-color: #cf222e;
  }

  .markdown-alert.markdown-alert-caution .markdown-alert-title {
    color: #d1242f;
  }

  /* 清除第一个和最后一个元素的外边距 */
  >*:first-child {
    margin-top: 0 !important;
  }

  >*:last-child {
    margin-bottom: 0 !important;
  }
}
</style>
