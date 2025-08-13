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
  <div class="yaml-editor">
    <div class="editor-top">
      <div class="editor-btns">
        <span class="editor-btn-save" @click="saveConfigYaml()">{{ t('btn.save') }}</span>
        <span class="editor-btn-restore" @click="resetConfig">{{ t('btn.restore') }}</span>
        <span class="editor-btn-full" @click="isEditorVisible = true">{{ t('btn.fullScreen') }}</span>
      </div>
    </div>
    <codemirror
        v-model="config"
        placeholder="Code goes here..."
        :autofocus="true"
        :indent-with-tab="true"
        :tab-size="2"
        :extensions="extensions" />
  </div>

  <!-- 全屏dialog -->
  <el-dialog
      v-model="isEditorVisible"
      destroy-on-close
      :show-close="false"
      :close-on-click-modal="false"
      class="editor-dialog-unscoped">
    <template #header>
      <div class="editor-btns">
        <span class="editor-btn-save" @click="saveConfigYaml()">{{ t('btn.save') }}</span>
        <span class="editor-btn-restore" @click="resetConfig">{{ t('btn.restore') }}</span>
        <span class="editor-btn-full" @click="isEditorVisible = false">{{ t('btn.exitFullScreen') }}</span>
      </div>
    </template>
    <codemirror
        v-model="config"
        placeholder="Code goes here..."
        :autofocus="true"
        :indent-with-tab="true"
        :tab-size="2"
        :extensions="extensions" />
  </el-dialog>

  <!-- 提示 dialog -->
  <el-dialog v-model="isTipVisible" :title="t('tip.tip')" class="tip-dialog-unscoped">
    <el-icon class="tip-icon"><IconAlarm /></el-icon>
    <div class="tip-text">{{ t('tip.confirmReset') }}</div>
    <template #footer>
      <div class="tip-dialog-footer">
        <el-button @click="confirmReset">{{ t('btn.confirm') }}</el-button>
        <el-button type="primary" @click="isTipVisible = false">{{ t('btn.cancel') }}</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { Codemirror } from 'vue-codemirror';
import { yaml } from '@codemirror/lang-yaml';
import {IconAlarm} from '@computing/opendesign-icons';
import { operateYaml } from '@/api/index.ts';

const {t} = useI18n();

const props = withDefaults(
  defineProps<{
    keyValue: string;
  }>(),
  {
    keyValue: 'oedp',
  }
);

// 编辑器内容
const config = ref('');

// 高级配置 dialog
const isEditorVisible = ref<boolean>(false);

// 提示 dialog
const isTipVisible = ref<boolean>(false);

// 编辑器配置
const extensions = computed(() => [
  yaml(),
]);

// 保存 YAML
const getConfigYaml = async () => {
  try {
    const res = await operateYaml({key: props.keyValue, operation: 'get', config_text: ''});
    if (res && res.is_success) {
      config.value = res.config_text;
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error('getConfigYaml', e);
  }
};

// 修改 config
const saveConfigYaml = async () => {
  isTipVisible.value = false;
  try {
    const res = await operateYaml({key: props.keyValue, operation: 'set', config_text: config.value});
    if (res && res.is_success) {
      await getConfigYaml();
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error('saveConfigYaml', e);
  }
};

// 还原 config，出现确认弹窗
const resetConfig = () => {
  isTipVisible.value = true;
};

// 确认还原 config
const confirmReset = async () => {
  isTipVisible.value = false;
  try {
    const res = await operateYaml({key: props.keyValue, operation: 'reset', config_text: ''});
    if (res && res.is_success) {
      config.value = res.config_text;
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error('confirmReset', e);
  }
};

onMounted(async () => {
  await getConfigYaml();
});
</script>

<style scoped lang="scss">
.editor-top {
  display: flex;
  justify-content: flex-end;
  .gutter {
    width: 35px;
    height: 32px;
    border-top-left-radius: 4px;
    border-right: 1px solid var(--o-background-color-quaternary-light);
    background-color: var(--o-background-color-tertiary-light);
  }
  .editor-btns {
    height: 32px;
    padding: 8px 16px 8px 0;
    span {
      margin-left: 8px;
      font-size: 12px;
      line-height: 16px;
      color: var(--o-theme-color-secondary-blue);
      cursor: pointer;
    }
  }
}

.editor {
  height: 100%;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}
</style>

<style lang="scss">
.cm-editor {
  outline: none !important;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'Courier New', Courier, monospace !important;
  background-color: var(--o-background-color-light-blue) !important;
  .cm-gutters {
    background-color: var(--o-background-color-tertiary-light);
    div {
      color: var(--o-text-color-secondary);
    }
  }
  .cm-content {
    font-size: 12px !important;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'Courier New', Courier, monospace !important;
    background-color: var(--o-background-color-light-blue) !important;
    div, span {
      color: var(--o-text-color-primary);
      font-size: 12px !important;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'Courier New', Courier, monospace !important;
    }
    .cm-line {
      font-size: 12px !important;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'Courier New', Courier, monospace !important;
    }
  }
  .cm-scroller {
    background-color: var(--o-background-color-light-blue) !important;
  }
  .cm-activeLine {
    background-color: var(--o-background-color-active-line-blue) !important;
  }
  .cm-focused .cm-activeLine {
    background-color: var(--o-background-color-active-line-blue) !important;
  }
  .cm-selectionBackground, .cm-content ::selection {
    background-color: var(--o-background-color-selection-blue) !important;
  }
  .cm-focused .cm-selectionBackground {
    background-color: var(--o-background-color-selection-blue) !important;
  }
  div, span {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'Courier New', Courier, monospace !important;
  }
}

.editor-dialog-unscoped {
  .el-dialog__header {
    justify-content: flex-end !important;
  }
}

.tip-dialog-unscoped {
  width: 432px;
  border-radius: 8px;
  .el-dialog__body {
    display: flex;
    align-items: center;
    .tip-icon {
      width: 24px;
      height: 24px;
      margin-right: 16px;
      svg {
        width: 24px;
        height: 24px;
      }
    }
    .tip-text {
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