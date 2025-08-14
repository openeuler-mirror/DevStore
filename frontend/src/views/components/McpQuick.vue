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
  <div class="mcp-quick">
    <!-- 左侧数字 -->
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-line" />
      <div class="step-num">2</div>
    </div>
    <!-- 右侧内容 -->
    <div class="install">
      <!-- 步骤 1 -->
      <div class="step-1">
        <div class="install-title">{{ t('detail.installPackage', [props.name]) }}</div>
        <el-button v-if="props.installStatus === 'not yet'" type="primary" class="uninstalled-btn" @click="installPackage">
          {{ t('detail.install') }}
        </el-button>
        <el-button v-else-if="props.installStatus === 'in process'" type="primary" class="installing-btn">
          <img :src="loading" class="loading-icon">
          <div>{{ t('detail.installing') }}</div>
        </el-button>
        <div v-else-if="props.installStatus === 'success'" class="installed-tip">
          <img :src="success" class="success-icon">
          <span>{{ t('detail.installed') }}</span>
        </div>
      </div>
      <!-- 步骤 2 -->
      <div class="step-2">
        <!-- 步骤 2：禁用 -->
        <div v-if="props.installStatus !== 'success'" class="step-2-disabled">
          <div class="install-title-disabled">{{ t('detail.addToAgent', [props.name]) }}</div>
          <div class="select-btn-disabled">
            <el-select :placeholder="t('detail.selectApp')" disabled class="select-disabled" />
            <el-button type="primary" disabled class="btn-disabled">{{ t('detail.add') }}</el-button>
          </div>
          <el-collapse expand-icon-position="left" class="collapse-disabled">
            <el-collapse-item title="MCP Server Config" :icon="CaretRight" disabled />
          </el-collapse>
        </div>

        <!-- 步骤 2：启用 -->
        <div v-else-if="props.installStatus === 'success'" class="step-2-enabled">
          <div class="install-title">{{ t('detail.addToAgent', [props.name]) }}</div>
          <!-- 下拉框：添加智能体应用 -->
          <div class="select-btn-enabled">
            <el-select v-model="value" :placeholder="t('detail.selectApp')" class="select-enabled">
            <el-option
                v-for="item in props.appList"
                :key="item.name"
                :label="item.name"
                :value="item.name" />
            </el-select>
            <el-button type="primary" class="btn-enabled" @click="addAppChild(value)">{{ t('detail.add') }}</el-button>
          </div>
          <!-- 已添加的 agent -->
          <div v-if="addedList.length !== 0" class="added-title">{{ t('detail.added') }}</div>
          <div v-for="item in appList" :key="item.name">
            <div v-if="item.status === 'added'" class="added-agent">
              {{ item.name }}
              <el-icon class="delete-icon" @click="deleteAppChild(item.name)">
                <IconDelete />
              </el-icon>
            </div>
          </div>
          <!-- config 折叠 -->
          <el-collapse v-model="activeNames" expand-icon-position="left" class="collapse-enabled">
            <el-collapse-item title="MCP Server Config" :icon="CaretRight" name="config">
              <div class="config-tip">{{ t('detail.configTip') }}</div>
              <div class="cmd-config">
                <el-icon class="copy-icon" @click="copyToClipboard">
                  <IconWindowing />
                </el-icon>
                {{ props.mcpJson }}
              </div>
            </el-collapse-item>
          </el-collapse>

          <!-- 卸载按钮 -->
          <el-button class="uninstall-btn" @click="isTipVisible = true">{{ t('detail.uninstall') }}</el-button>
        </div>
      </div>
    </div>
  </div>

  <!-- 确认卸载 dialog -->
  <el-dialog v-model="isTipVisible" :title="t('tip.tip')" class="uninstall-dialog-unscoped">
    <el-icon class="uninstall-icon"><IconAlarm /></el-icon>
    <div class="uninstall-text">{{ t('tip.confirmUninstall', [props.name]) }}</div>
    <template #footer>
      <div class="uninstall-dialog-footer">
        <el-button @click="confirmUninstallPackage">{{ t('btn.confirm') }}</el-button>
        <el-button type="primary" @click="isTipVisible = false">{{ t('btn.cancel') }}</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { CaretRight } from '@element-plus/icons-vue';
import { IconWindowing, IconDelete, IconAlarm } from '@computing/opendesign-icons';
import loading from '@/assets/img/loading.svg';
import success from '@/assets/img/success.svg';

const {t} = useI18n();

const props = withDefaults(
  defineProps<{
    name: string;
    installStatus: 'not yet' | 'in process' | 'success';
    appList: [] | {'name': string; 'status': 'added' | 'removed';}[];
    mcpJson: string;
    addApp: Function;
    deleteApp: Function;
    installPackage: Function;
    uninstallPackage: Function;
  }>(),
  {
    name: 'mcp',
    installStatus: 'not yet',
    appList: () => [],
    mcpJson: '',
  }
);

// 选择的 app
const value = ref('');

// 已添加的 app
const addedList = computed(() => props.appList.filter(app => app.status === 'added').map(app => app.name));

const activeNames = ref(['config']);

// 复制到剪切板
const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.mcpJson);
  } catch (err) {
    console.error('复制失败:', err);
  }
};

// 下载软件包
const installPackage = async () => {
  props.installPackage();
};

// 确认 dialog
const isTipVisible = ref<boolean>(false);

// 确认卸载软件包
const confirmUninstallPackage = () => {
  isTipVisible.value = false;
  props.uninstallPackage();
};

// 只允许添加尚未添加的 app
const addAppChild = (name: string) => {
  if (!addedList.value.includes(name)) {
    props.addApp(name);
  }
};

// 删除 app
const deleteAppChild = (name: string) => {
  props.deleteApp(name);
};
</script>

<style scoped lang="scss">
.mcp-quick {
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
  .install {
    padding-left: 16px;
    width: calc(100% - 20px);
    .install-title, .install-title-disabled {
      margin-bottom: 8px;
      font-size: 16px;
      line-height: 24px;
      font-weight: 500;
    }
    .install-config {
      max-height: 100%;
      white-space: pre;
      background: var(--o-background-color-tertiary-light);
      border-radius: 4px;
      font-weight: 400;
      padding: 16px;
      font-family: monospace;
      overflow: auto;
    }
    .step-1 {
      margin-bottom: 24px;
      .uninstalled-btn, .installing-btn {
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
      .installing-btn {
        cursor: not-allowed;
        line-height: 16px;
        .loading-icon {
          animation: rotate-ing 0.9s infinite linear;
          margin-right: 6px;
        }
      }
      :deep(.el-button--primary).installing-btn > span {
        display: flex;
      }
      :deep(.el-button--primary).installing-btn:hover {
        background-color: var(--o-button-bg-color_primary);
        color: var(--o-button-color_primary);
        border-color: var(--o-button-border-color_primary);
      }
      .installed-tip {
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
      .step-2-disabled {
        .install-title-disabled {
          color: var(--o-placeholder-color);
        }
        .select-btn-disabled {
          margin-bottom: 16px;
          display: flex;
          align-items: center;
          .select-disabled {
            height: 32px;
            flex: 1;
            :deep(.el-select__placeholder) {
              font-size: 12px;
            }
          }
          .btn-disabled {
            margin-left: 8px;
          }
        }
        .collapse-disabled :deep(.el-collapse-item__header) {
          height: 22px;
          padding: 0;
          span {
            font-size: 14px;
            line-height: 22px;
            color: var(--o-placeholder-color);
          }
          i {
            margin: 0;
          }
          svg {
            width: 14px;
            height: 14px;
            color: var(--o-placeholder-color);
          }
        }
      }
      .step-2-enabled {
        .select-btn-enabled {
          margin-bottom: 8px;
          display: flex;
          align-items: center;
          .select-enabled {
            height: 32px;
            flex: 1;
            :deep(.el-select__placeholder) {
              font-size: 12px;
            }
          }
          .btn-enabled {
            margin-left: 8px;
          }
        }
        .added-title {
          margin-bottom: 8px;
          font-size: 12px;
          line-height: 16px;
        }
        .added-agent {
          width: 100%;
          height: 32px;
          margin-bottom: 8px;
          padding: 8px 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-radius: 4px;
          background: var(--o-background-color-tertiary-light);
          color: var(--o-text-color-primary);
          font-size: 12px;
          line-height: 16px;
          .delete-icon {
            width: 20px;
            height: 20px;
            cursor: pointer;
            color: var(--o-text-color-tertiary);
          }
        }
        .collapse-enabled :deep(.el-collapse-item__header) {
          height: 22px;
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
        .collapse-enabled{
          margin-top: 16px;
          :deep(.el-collapse-item__content) {
            margin: 0;
          }
          .config-tip {
            margin: 4px 0 8px;
            font-size: 12px;
            line-height: 16px;
            color: var(--o-text-color-tertiary);
          }
          .cmd-config {
            position: relative;
            line-height: 16px;
            max-height: 100%;
            white-space: pre;
            color: var(--o-text-color-primary);
            background: var(--o-background-color-tertiary-light);
            border-radius: 4px;
            font-weight: 400;
            padding: 12px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'Courier New', Courier, monospace;
            font-size: 12px;
            overflow: auto;
            .copy-icon {
              width: 20px;
              height: 20px;
              padding: 2px;
              color: var(--o-text-color-tertiary);
              position: absolute;
              cursor: pointer;
              top: 14px;
              right: 14px;
              :hover {
                color: var(--o-theme-color-primary-blue);
              }
              svg {
                width: 16px;
                height: 16px;
              }
            }
          }
        }
        .uninstall-btn {
          width: 100%;
          margin-top: 8px;
        }
      }
    }
  }
}
</style>

<style lang="scss">
.uninstall-dialog-unscoped {
  width: 432px;
  border-radius: 8px;
  .el-dialog__body {
    display: flex;
    align-items: center;
    .uninstall-icon {
      width: 24px;
      height: 24px;
      margin-right: 16px;
      svg {
        width: 24px;
        height: 24px;
      }
    }
    .uninstall-text {
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