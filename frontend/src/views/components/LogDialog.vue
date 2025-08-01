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
  <el-dialog
      :model-value="modelValue"
      destroy-on-close
      :title="title"
      :close-on-click-modal="false"
      class="log-dialog-unscoped"
      @close="close">
    <div ref="logContent" @scroll="scrollFunc">
      {{ log }}
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="close">
          {{ t('btn.close') }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { fetchLog } from '@/api/index.ts';

import { HOME_LOG } from '../../../public/mock/mock.ts';

const {t} = useI18n();

const props = withDefaults(
  defineProps<{
    modelValue: boolean;
    type: string;
  }>(),
  {
    modelValue: false,
    type: 'DevStore',
  }
);

// 判断标题显示
const title = computed(() => props.type === 'DevStore' ?
  t('nav.runningLog') :
  t('detail.executionLog', [props.type]));

const emit = defineEmits(['update:modelValue']);
// 关闭 dialog
const close = () => {
  emit('update:modelValue', false);
};

const log = ref<string>(HOME_LOG);
// 获取 log
const getLog = async () => {
  try {
    const res = await fetchLog({type: props.type});
    if (res && res.is_success) {
      log.value = res.data.log;
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error('getLog', e);
  }
};

// 轮询 log
let intervalId = null;
onMounted(async () => {
  await getLog();

  // 启动轮询
  intervalId = setInterval(() => {
    getLog();
  }, 2000);
});

// 清除定时器
onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
});

// hl: 待验证，自动滚动
const logContent = ref<any>('logContent');
let lastScrollTop = 0;
let isStopped = false;

const scrollFunc = (e) => {
  const { scrollTop, scrollHeight, clientHeight } = e.target;
  if (scrollTop < lastScrollTop) {
    isStopped = true;
  } else if (scrollTop === scrollHeight - clientHeight) {
    isStopped = false;
  }
  lastScrollTop = scrollTop;
};

const setScrollTop = () => {
  nextTick(() => {
    if (logContent.value && !isStopped) {
      const scrollTop = (logContent.value?.scrollHeight as number) - (logContent.value?.clientHeight as number);
      logContent.value.scrollTop = scrollTop;
    }
  });
};
watch(() => log.value, setScrollTop);

onMounted(setScrollTop);
</script>

<style lang="scss">
.log-dialog-unscoped {
  width: 1000px;
  max-height: 632px;
  border-radius: 8px;

  .el-dialog__header {
    font-size: 16px;
    line-height: 24px;
    font-weight: 700;
    font-family: monospace;
  }
  .el-dialog__body {
    margin: 24px 0 24px 24px;
    padding: 0 24px 0 0;
    font-size: 12px;
    line-height: 20px;
    white-space: pre;
    div {
      font-family: monospace;
    }
  }
  .el-button {
    width: 64px;
    height: 24px;
  }
}
</style>