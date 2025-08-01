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
  <el-input
      v-model="cmdDisplay"
      readonly
      class="copy-input">
    <template #append>
      <el-button
          class="copy-button"
          @click="copyToClipboard">
        <el-icon><IconWindowing /></el-icon>
      </el-button>
    </template>
  </el-input>
</template>

<script lang="ts" setup>
import { computed } from 'vue';
import { IconWindowing } from '@computing/opendesign-icons';

const props = withDefaults(
  defineProps<{
    cmd: string;
  }>(),
  {
    cmd: '',
  }
);

const cmdDisplay = computed(() => props.cmd);

// 复制到剪切板
const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.cmd);
  } catch (err) {
    console.error('复制失败:', err);
  }
};
</script>

<style scoped lang="scss">
.copy-input {
  height: 32px;
  margin-bottom: 24px;
  border-radius: 4px;
  :deep(.el-input__wrapper), :deep(.el-input-group__append) {
    box-shadow: none;
    background: var(--o-background-color-tertiary-light);
  }
  :deep(.el-input__wrapper) {
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
    padding-right: 0;
    input {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-family: monospace;
    }
  }
  :deep(.el-input-group__append) {
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    .copy-button {
      width: 48px;
      border: none;
      span {
        min-width: 16px;
      }
    }
  }
}
</style>