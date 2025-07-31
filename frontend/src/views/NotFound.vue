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
  <div class="not-found">
    <!-- 提示页面不存在 -->
    <h1>{{ t('page.pageNotExist') }}</h1>
    <!-- 返回首页 -->
    <router-link to="/">{{ t('page.backToHomepage') }}</router-link>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
const {t} = useI18n();
</script>