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
  <div class="mcp-cli">
    <!-- 左侧数字 -->
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-line" />
      <div class="step-num">2</div>
    </div>
    <!-- 右侧内容 -->
    <div class="cmd">
      <!-- 步骤 1 -->
      <div class="cmd-title">{{ t('detail.installMcpPackage') }}</div>
      <copy-input :cmd="props.cmdList[0]" />
      <!-- 步骤 2 -->
      <div class="cmd-title">{{ t('detail.addMcpToAgent') }}</div>
      <div class="cmd-config">
        <el-icon class="copy-icon" @click="copyToClipboard">
          <IconWindowing />
        </el-icon>
        {{ props.mcpJson }}
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import { IconWindowing } from '@computing/opendesign-icons';
import CopyInput from '@/views/components/CopyInput.vue';

const {t} = useI18n();

const props = withDefaults(
  defineProps<{
    status: 'not yet' | 'in process' | 'success';
    cmdList: string[];
    mcpJson: string;
  }>(),
  {
    status: 'not yet',
    cmdList: () => [],
    mcpJson: '',
  }
);

// 复制到剪切板
const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.mcpJson);
  } catch (err) {
    console.error('复制失败:', err);
  }
};
</script>

<style scoped lang="scss">
.mcp-cli {
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
  .cmd {
    padding-left: 16px;
    width: calc(100% - 20px);
    .cmd-title {
      margin-bottom: 8px;
      font-size: 16px;
      line-height: 24px;
      font-weight: 500;
    }
    .cmd-config {
      position: relative;
      line-height: 20px;
      max-height: 100%;
      white-space: pre;
      background: var(--o-background-color-tertiary-light);
      border-radius: 4px;
      font-weight: 400;
      padding: 16px;
      font-family: monospace;
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
}
</style>