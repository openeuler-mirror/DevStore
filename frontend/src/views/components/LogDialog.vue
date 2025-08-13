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
    <div ref="logContent" class="log-content" @scroll="scrollFunc">
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
import { fetchLog } from '@/api/index';

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

const log = ref<string>('');
// 获取 log
const getLog = async () => {
  try {
    const res = await fetchLog({key: props.type});
    if (res && res.is_success && res.log) {
      log.value = res.log || '';
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error('getLog', e);
  }
};

// 轮询 log
let intervalId: NodeJS.Timeout | null = null;
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

// 自动滚动逻辑
const logContent = ref<HTMLElement>();
let isAutoScrollEnabled = true; // 是否启用自动滚动到底部
let lastScrollTop = 0;

// 检查是否滚动到底部
const isScrolledToBottom = (element: HTMLElement): boolean => {
  const { scrollTop, scrollHeight, clientHeight } = element;
  // 允许1px的误差
  return Math.abs(scrollHeight - clientHeight - scrollTop) <= 1;
};

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (logContent.value) {
      const element = logContent.value;
      element.scrollTop = element.scrollHeight;
    }
  });
};

// 滚动事件处理
const scrollFunc = (e: Event) => {
  const target = e.target as HTMLElement;
  const { scrollTop } = target;
  
  // 如果向上滚动，停止自动滚动
  if (scrollTop < lastScrollTop) {
    isAutoScrollEnabled = false;
  } 
  // 如果滚动到底部，恢复自动滚动
  else if (isScrolledToBottom(target)) {
    isAutoScrollEnabled = true;
  }
  
  lastScrollTop = scrollTop;
};

// 监听日志内容变化，自动滚动到底部（仅当启用自动滚动时）
watch(() => log.value, (newValue, oldValue) => {
  if (isAutoScrollEnabled) {
    scrollToBottom();
  }
  
  // 首次加载日志内容时，确保滚动到底部
  if (props.modelValue && oldValue === '' && newValue) {
    nextTick(() => {
      setTimeout(() => {
        scrollToBottom();
      }, 50);
    });
  }
});

// 对话框打开时重置自动滚动状态
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    isAutoScrollEnabled = true;
    
    // 多次尝试滚动到底部，确保成功
    const tryScrollToBottom = (attempts = 0) => {
      if (attempts >= 10) return; // 最多尝试10次
      
      nextTick(() => {
        setTimeout(() => {
          if (logContent.value && log.value) {
            scrollToBottom();
          } else {
            tryScrollToBottom(attempts + 1);
          }
        }, 100 * (attempts + 1)); // 递增延时
      });
    };
    
    tryScrollToBottom();
  }
});
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
    white-space: pre-wrap;
    overflow: hidden; /* 确保外层没有滚动条 */
    
    .log-content {
      font-family: monospace;
      border: 1px solid #dcdfe6;
      padding: 12px;
      background-color: #f5f7fa;
      height: 400px;
      overflow-y: auto;
      box-sizing: border-box;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }
  .el-button {
    width: 64px;
    height: 24px;
  }
}
</style>