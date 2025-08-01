/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-07-31
 * =================================================================================================================== */

import { createRouter, createWebHashHistory } from 'vue-router';
import Layout from '@/layout/index.vue';
import Home from '@/views/Home.vue';
import Detail from '@/views/Detail.vue';
import NotFound from '@/views/NotFound.vue';

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      component: Layout,
      children: [
        {
          path: '',
          name: 'Home', // 首页
          component: Home,
        },
        {
          path: 'mcp/:key', // 详情页：MCP
          name: 'McpServerDetail',
          component: Detail,
        },
        {
          path: 'oedp/:key', // 详情页：OEDP
          name: 'OedpPluginDetail',
          component: Detail,
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*', // 404 页面
      name: 'NotFound',
      component: NotFound
    }
  ]
});

export default router;