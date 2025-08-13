<!-- Copyright (c) 2025 Huawei Technologies Co., Ltd. -->
<!-- oeDeploy is licensed under the Mulan PSL v2 .-->
<!-- You can use this software according to the terms and conditions of the Mulan PSL v2. -->
<!-- You may obtain a copy of Mulan PSL v2 at: -->
<!--   http://license.coscl.org.cn/MulanPSL2 -->
<!-- THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR -->
<!-- IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR -->
<!-- PURPOSE. -->
<!-- See the Mulan PSL v2 for more details. -->
<!-- Create: 2025-08-01 -->
<!-- =================================================================================================================== -->

<template>
  <div class="oedp-quick">
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-line" />
      <div class="step-num">2</div>
    </div>
    <!-- 高级设置 -->
    <div class="deploy">
      <!-- 步骤 1 -->
      <div class="step-1">
        <div class="deploy-title">{{ t('detail.downloadPlugin', [props.name]) }}</div>
        <el-button v-if="props.downloadStatus === 'not yet'" type="primary" class="undeployed-btn" @click="throttledDownload">
          {{ t('detail.download') }}
        </el-button>
        <el-button v-else-if="props.downloadStatus === 'in process'" type="primary" class="deploying-btn">
          <img :src="loading" class="loading-icon">
          <div>{{ t('detail.downloading') }}</div>
        </el-button>
        <div v-else-if="props.downloadStatus === 'success'" class="deployed-tip">
          <img :src="success" class="success-icon">
          <span>{{ t('detail.downloaded') }}</span>
        </div>
      </div>
      <!-- 步骤 2 -->
      <div class="step-2">
        <!-- 步骤 2：禁用 -->
        <div v-if="props.downloadStatus !== 'success'" class="step-2-disabled">
          <div class="deploy-title-disabled">
            {{ t('detail.localDeploy') }}
            <div class="deploy-log">
              <el-icon class="view-log-icon"><IconFileText /></el-icon>
              <div>{{ t('detail.viewLogs') }}</div>
            </div>
          </div>
          <div class="tip">{{ t('detail.localDeployTip') }}</div>
        </div>

        <!-- 步骤 2：启用 -->
        <div v-else-if="props.downloadStatus === 'success'" class="step-2-enabled">
          <div class="deploy-title">
            {{ t('detail.localDeploy') }}
            <div class="deploy-log" @click="isLogVisible = true">
              <el-icon class="view-log-icon"><IconFileText /></el-icon>
              <div class="view-log-title">{{ t('detail.viewLogs') }}</div>
            </div>
          </div>
          <div class="tip">{{ t('detail.localDeployTip') }}</div>
          <!-- 部署按钮 -->
          <deploy-button
              v-for="btn in actionList"
              :key="btn.name"
              :title="btn.title"
              :desc="btn.description"
              :is-executing="btn.status"
              :is-allowed="isAllowed"
              :execute-action="throttledExecution" />
          <el-collapse v-model="activeNames" expand-icon-position="left" class="collapse-enabled">
            <el-collapse-item :title="t('detail.advancedConfig')" :icon="CaretRight" name="config">
              <!-- 代码编辑器 -->
              <yaml-editor :key-value="keyValue" class="config-editor" />
            </el-collapse-item>
          </el-collapse>
          <el-button class="delete-btn" @click="isTipVisible = true">{{ t('detail.uninstall') }}</el-button>
        </div>
      </div>
    </div>

    <!-- 日志 dialog -->
    <log-dialog v-if="isLogVisible" v-model="isLogVisible" :type="props.keyValue" />

    <!-- 确认删除 dialog -->
    <el-dialog v-model="isTipVisible" :title="t('tip.tip')" class="delete-dialog-unscoped">
      <el-icon class="delete-icon"><IconAlarm /></el-icon>
      <div class="delete-text">{{ t('tip.confirmDelete') }}</div>
      <template #footer>
        <div class="delete-dialog-footer">
          <el-button @click="throttledDeletion">{{ t('btn.confirm') }}</el-button>
          <el-button type="primary" @click="isTipVisible = false">{{ t('btn.cancel') }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { throttle } from 'underscore';
import { CaretRight } from '@element-plus/icons-vue';
import { IconAlarm, IconFileText } from '@computing/opendesign-icons';
import DeployButton from '@/views/components/DeployButton.vue';
import LogDialog from '@/views/components/LogDialog.vue';
import YamlEditor from '@/views/components/YamlEditor.vue';
import { getPlugin, removePlugin, issueAction } from '@/api/index.ts';
import loading from '@/assets/img/loading.svg';
import success from '@/assets/img/success.svg';

const {t} = useI18n();

const props = withDefaults(
  defineProps<{
    name: string;
    keyValue: string;
    downloadStatus: 'not yet' | 'in process' | 'success' | 'fail';
    actionList: [] | {'name': string; 'title': string; 'description': string; 'status': 'not yet' | 'in process' | 'success' | 'fail';}[],
    getDetail: Function;
  }>(),
  {
    name: 'oedp',
    keyValue: 'oedp',
    downloadStatus: 'not yet',
    actionList: () => [],
  }
);

// 高级配置默认折叠，只有用户手动点击时才展开
const activeNames = ref([]);

// 检查 actionList 中是否至少有一个 action 正在进行，如果有的话，所有按钮都不允许执行
const isAllowed = computed(() => !props.actionList.some(item => item?.status === 'in process'));

// 下载插件
const downloadPlugin = async () => {
  try {
    const res = await getPlugin({key: props.keyValue});
    if (res && res.is_success) {
      props.getDetail();
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error(e);
  }
};

// 添加节流：下载插件
const throttledDownload = throttle(downloadPlugin, 1000);

// 确认 dialog
const isTipVisible = ref<boolean>(false);

// 删除插件
const confirmDeletePlugin = async () => {
  try {
    const res = await removePlugin({key: props.keyValue});
    if (res && res.is_success) {
      isTipVisible.value = false;
      props.getDetail();
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error(e);
  }
};

// 添加节流：删除插件
const throttledDeletion = throttle(confirmDeletePlugin, 1000);

// 执行部署动作
const executeAction = async (action: string) => {
  if (isAllowed.value) {
    try {
      const res = await issueAction({key: props.keyValue, action_name: action});
      if (res && res.is_success) {
        props.getDetail();
      } else if (res) {
        console.log(res.message);
      }
    } catch (e) {
      console.error(e);
    }
  }
};

// 添加节流：执行部署动作
const throttledExecution = throttle((action: string) => {
  executeAction(action)
}, 1000)

// 日志 dialog
const isLogVisible = ref<boolean>(false);
</script>

<style scoped lang="scss">
.oedp-quick {
  display: flex;
  .step {
    width: 20px;
    margin-top: 2px;
    display: flex;
    flex-direction: column;
    align-items: center;
    .step-num {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background-color: var(--o-background-color-quaternary-light);
      font-size: 12px;
      line-height: 20px;
      text-align: center;
      font-weight: 500;
    }
    .step-line {
      width: 1px;
      height: 58px;
      margin: 3px 0 7px;
      background-color: var(--o-background-color-quaternary-light);
    }
  }
  .deploy {
    padding-left: 16px;
    width: calc(100% - 20px);
    .deploy-title, .deploy-title-disabled {
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      font-size: 16px;
      line-height: 24px;
      font-weight: 500;
    }
    .step-1 {
      margin-bottom: 24px;
      .undeployed-btn, .deploying-btn {
        width: 100%;
        height: 32px;
        border-radius: 4px;
      }
      @keyframes rotate-ing {
        from {
          transform: rotate(0);
        }
        to {
          transform: rotate(360deg);
        }
      }
      .deploying-btn {
        cursor: not-allowed;
        line-height: 16px;
        .loading-icon {
          animation: rotate-ing 0.9s infinite linear;
          margin-right: 6px;
        }
      }
      :deep(.el-button--primary).deploying-btn > span {
        display: flex;
      }
      :deep(.el-button--primary).deploying-btn:hover {
        background-color: var(--o-button-bg-color_primary);
        color: var(--o-button-color_primary);
        border-color: var(--o-button-border-color_primary);
      }
      .deployed-tip {
        display: flex;
        align-items: center;
        height: 32px;
        padding: 8px 16px;
        background: var(--o-background-color-green);
        border-radius: 4px;
        img {
          margin-right: 9px;
        }
        span {
          font-size: 12px;
          line-height: 16px;
        }
      }
    }
    .step-2 {
      .deploy-log {
        display: flex;
        align-items: center;
        .view-log-icon {
          width: 16px;
          height: 16px;
          margin-right: 4px;
        }
        .view-log-title {
          font-size: 12px;
          line-height: 16px;
        }
      }
      .tip {
        margin-bottom: 8px;
        font-size: 12px;
        color: var(--o-placeholder-color);
      }
      .step-2-disabled {
        .deploy-title-disabled {
          color: var(--o-placeholder-color);
        }
      }
      .step-2-enabled {
        .deploy-title .deploy-log {
          cursor: pointer;
          .view-log-icon {
            color: var(--o-input-icon-color);
          }
          .view-log-title {
            color: var(--o-text-color-secondary);
          }
        }
        .deploy-title .deploy-log:hover {
          color: var(--o-theme-color-primary-blue);
          .view-log-title {
            color: var(--o-theme-color-primary-blue);
          }
        }
        .collapse-enabled {
          :deep(.el-collapse-item__header) {
            height: 22px;
            margin-top: 16px;
            padding: 0;
            span {
              font-size: 14px;
              line-height: 22px;
              color: var(--o-text-color-primary);
            }
            i {
              margin: 0;
            }
            svg {
              width: 14px;
              height: 14px;
              color: var(--o-text-color-primary);
            }
          }
          :deep(.el-collapse-item__content) {
            padding: 0 !important;
            margin: 0 !important;
            border: 1px solid var(--o-background-color-quaternary-light);
            border-radius: 4px;
          }
          :deep(.el-collapse-item__wrap) {
            padding: 0 !important;
            margin: 0 !important;
          }
        }
        .delete-btn {
          width: 100%;
          margin-top: 8px;
          margin-bottom: 16px;
        }
      }
    }
  }
}
.config-editor {
  height: 300px;
  max-height: 50vh;
  width: 100%;
  overflow: hidden;
}
</style>

<style lang="scss">
.editor-dialog-unscoped {
  width: 1000px;
  max-height: 968px;
  border: 1px solid var(--o-background-color-quaternary-light);
  border-radius: 4px;
  .el-dialog__header {
    padding: 0 16px 0 0;
    border: none;
    display: flex;
    justify-content: space-between;
    .gutter {
      width: 46px;
      height: 48px;
      border-top-left-radius: 4px;
      border-right: 1px solid var(--o-background-color-quaternary-light);
      background-color: var(--o-background-color-tertiary-light);
    }
    .editor-btns {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      span {
        margin-left: 8px;
        padding: 16px 0 16px;
        font-size: 12px;
        line-height: 16px;
        color: var(--o-theme-color-secondary-blue);
        cursor: pointer;
      }
    }
  }
  .el-dialog__body {
    padding: 0;
  }
}

.delete-dialog-unscoped {
  width: 432px;
  border-radius: 8px;
  .el-dialog__body {
    display: flex;
    align-items: center;
    .delete-icon {
      width: 24px;
      height: 24px;
      margin-right: 16px;
      svg {
        width: 24px;
        height: 24px;
      }
    }
    .delete-text {
      font-size: 12px;
      line-height: 16px;
    }
  }
  .el-dialog__footer {
    .tip-dialog-footer {
      button {
        margin: 0 4px 0;
      }
    }
  }
}
</style>