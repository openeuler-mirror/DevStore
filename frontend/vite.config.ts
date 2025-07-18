/* Copyright (c) 2025 Huawei Technologies Co., Ltd.
 * oeDeploy is licensed under the Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *     http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
 * PURPOSE.
 * See the Mulan PSL v2 for more details.
 * Create: 2025-07-18
 * =================================================================================================================== */

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { viteMockServe } from 'vite-plugin-mock';
import monacoEditorPlugin from 'vite-plugin-monaco-editor';
import AutoImport from 'unplugin-auto-import/vite';
import Components from 'unplugin-vue-components/vite';
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers';
import { OpenDesignResolver } from '@computing/opendesign2/themes/plugins/resolver';
import { fileURLToPath, URL } from 'url';

export default defineConfig({
  base: './',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  plugins: [
    vue(),
    monacoEditorPlugin({
      customWorkers: [
        {
          label: 'yaml',
          entry: 'monaco-editor/esm/vs/language/yaml/yaml.worker'
        },
        // 添加其他需要的 worker
        {
          label: 'editor',
          entry: 'monaco-editor/esm/vs/editor/editor.worker'
        }
      ],
    }),
    AutoImport({
      resolvers: [
        OpenDesignResolver(ElementPlusResolver, { importStyle: 'sass' })
      ],
      imports: [
        'vue'
      ]
    }),
    Components({
      resolvers: [OpenDesignResolver(ElementPlusResolver, { importStyle: 'sass' })]
    }),
    viteMockServe({
      mockPath: 'mock',
      enable: true,
      watchFiles: true
    })
  ],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'esnext',
    rollupOptions: {
      plugins: [
        {
          name: 'disable-crypto',
          resolveId(source) {
            if (source === 'crypto') {
              return false
            }
          }
        }
      ]
    }
  },
  server: {
    port: 5173,
    strictPort: true,
    hmr: {
      protocol: 'ws',
      host: 'localhost'
    }
  },
  define: {
    'process.env': {},
    global: {}
  }
})
