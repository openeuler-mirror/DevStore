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
  <div class="oedp-cli">
    <!-- 左侧数字 -->
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-line" />
      <div class="step-num">2</div>
      <div class="step-line" />
      <div class="step-num">3</div>
    </div>
    <!-- 右侧内容 -->
    <div class="cmd">
      <div class="cmd-title">{{ t('detail.initToLocal') }}</div>
      <copy-input :cmd="props.cmdList[0]" />

      <div class="cmd-title">{{ t('detail.modifyDeployParam') }}</div>
      <copy-input :cmd="props.cmdList[1]" />

      <div class="cmd-title">{{ t('detail.triggerDeploy') }}</div>
      <copy-input :cmd="props.cmdList[2]" />

      <div class="cmd-tip">{{ t('detail.deployCliTip') }}</div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import CopyInput from '@/views/components/CopyInput.vue';

const {t} = useI18n();

const props = withDefaults(
  defineProps<{
    cmdList: string[];
  }>(),
  {
    cmdList: () => [],
  }
);
</script>

<style scoped lang="scss">
.oedp-cli {
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
    .cmd-tip {
      color: var(--o-text-color-tertiary);
      margin-top: -16px;
    }
    .cmd-config {
      max-height: 100%;
      white-space: pre;
      background: var(--o-background-color-tertiary-light);
      border-radius: 4px;
      font-weight: 400;
      padding: 16px;
      font-family: monospace;
      overflow: auto;
    }
  }
}
</style>