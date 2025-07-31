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
  <div class="deploy-button">
    <div class="deploy-title-desc">
      <div class="deploy-title">{{ props.title }}</div>
      <div class="deploy-desc">{{ props.desc }}</div>
    </div>
    <el-button v-if="props.isExecuting !== 'in process'" type="primary" :class="['deploy-btn-execute', { 'not-allowed': !isAllowed }]" @click="executeAction(props.title)">
      {{ t('btn.execute') }}
    </el-button>
    <el-button v-else-if="props.isExecuting === 'in process'" type="primary" class="deploy-btn-executing">
      <img :src="loading" class="loading-icon">
      <div>{{ t('btn.executing') }}</div>
    </el-button>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import loading from '@/assets/img/loading.svg';

const {t} = useI18n();

const props = withDefaults(
  defineProps<{
    title: string;
    desc: string;
    isExecuting: 'not yet' | 'in process' | 'success' | 'fail';
    isAllowed: boolean;
    executeAction: Function;
  }>(),
  {
    title: '',
    desc: '',
    isExecuting: 'not yet',
    isAllowed: true,
  }
);
</script>

<style scoped lang="scss">
.deploy-button {
  width: 100%;
  min-height: 56px;
  margin-bottom: 8px;
  padding: 8px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--o-background-color-tertiary-light);
  .deploy-title-desc {
    .deploy-title {
      margin-bottom: 2px;
      font-size: 14px;
      line-height: 22px;
      font-weight: 500;
      color: var(--o-text-color-primary);
    }
    .deploy-desc {
      font-size: 12px;
      line-height: 16px;
      color: var(--o-text-color-tertiary);
    }
  }
  .deploy-btn-execute, .deploy-btn-executing {
    margin-left: 8px;
    height: 24px;
  }
  .deploy-btn-execute {
    width: 64px;
  }
  .not-allowed {
    cursor: not-allowed;
  }
  .deploy-btn-executing {
    width: 72px;
    padding: 4px 8px;
    cursor: not-allowed;
    @keyframes rotate-ing {
      from {
        transform: rotate(0);
      }
      to {
        transform: rotate(360deg);
      }
    }
    .loading-icon {
      animation: rotate-ing 0.9s infinite linear;
      margin-right: 6px;
    }
    div {
      font-size: 12px;
      line-height: 16px;
    }
  }
  :deep(.el-button--primary).deploy-btn-executing > span {
    display: flex;
  }
}
</style>