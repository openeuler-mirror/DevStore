/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-07-30
 * =================================================================================================================== */

import { createApp } from 'vue';
import App from './App.vue';
import i18n from './lang/i18n';
import router from './router';
import '@/assets/style/normalize.css';
import '@/assets/style/reset.scss';
import '@/assets/style/variable.scss';
import 'element-plus/es/components/message/style/css';

const app = createApp(App);
app.use(router);
app.use(i18n as any);
app.mount('#app');
