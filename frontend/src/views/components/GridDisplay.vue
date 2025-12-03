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
  <div class="display-list-container">
    <!-- 有数据 -->
    <div class="display-list">
      <!-- 展示 -->
      <div v-show="itemList.length > 0" class="display-list-content">
        <div v-for="item in itemList" :key="`${item.name}-${item.version}`" class="display-card" @click="goToDetail(item.key)">
          <div class="display-card-top">
            <!-- 上：图标 -->
            <div class="display-card-icon">
              <!-- 图片 -->
              <img v-if="item.icon" :src="'data:image/png;base64,' + item.icon" :alt="item.name">
              <!-- 首 2 字母生成 -->
              <div
                  v-else
                  :style="{
                    backgroundColor: generateIconBgColor(item.name),
                  }">
                {{ item.name.slice(0, 2).toUpperCase() }}
              </div>
            </div>
            <div class="display-card-top-info">
              <!-- 名称 -->
              <div class="display-card-id">{{ item.name }}</div>
              <div class="display-card-tag-version">
                <!-- 分类 -->
                <div class="display-card-tag">{{ item.tag.toUpperCase() }}</div>
                <!-- 版本 -->
                <div class="display-card-version">{{ item.version }}</div>
              </div>
            </div>
          </div>

          <!-- 中：描述 -->
          <div class="display-card-desc">
            <el-text line-clamp="2">
              {{ item.description?.zh || item.description?.en || item.description?.default || t('home.noDesc') }}
            </el-text>
          </div>

          <!-- 下：作者 + 时间 -->
          <div class="display-card-author-time">
            <div class="display-card-author">{{ item.author ? `@${item.author}` : '' }}</div>
            <div class="display-card-time">{{ item.updated_at }}</div>
          </div>
        </div>
      </div>
    </div>
    <!-- 无数据 -->
    <div v-show="itemList.count === 0" class="display-list-blank">
      {{ t('home.noResult') }}
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { Tag } from '@/api/index.ts';
import { generateIconBgColor } from '@/utils/index.ts';
import { useTabStore } from '@/stores/tabStore';

const router = useRouter();
const {t} = useI18n();
const { addTab } = useTabStore();

const props = withDefaults(
  defineProps<{
    tag: Tag;
    itemList: {}[];
  }>(),
  {
    tag: 'mcp',
    itemList: () => [],
  }
);

// 跳转至详情页 tag, key - 新增页签
const goToDetail = (key: string) => {
  const item = props.itemList.find((i: any) => i.key === key);
  const detailPath = `/${props.tag}/${key}`;
  
  // 添加新页签
  addTab({
    id: `${props.tag}-${key}`,
    title: item?.name || key,
    route: { path: detailPath }
  });
  
  // 跳转到详情页
  router.push(detailPath);
};

</script>

<style scoped lang="scss">
.display-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0 24px;
  .display-list {
    flex: 1;
    .display-list-content {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;

      .display-card {
        max-width: 275px;
        height: 160px;
        padding: 16px;
        border-radius: 8px;
        overflow: hidden;
        background-color: var(--el-bg-color);

        &:hover {
          cursor: pointer;
        }

        .display-card-top {
          display: flex;
          margin-bottom: 4px;
          .display-card-icon {
            width: 48px;
            height: 48px;
            margin-right: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            img {
              max-width: 48px;
              max-height: 48px;
              width: auto;
              height: auto;
              border-radius: 50%;
            }
            div {
              width: 48px;
              height: 48px;
              border-radius: 50%;
              line-height: 48px;
              text-align: center;
              font-size: 24px;
              font-weight: 700;
              color: var(--o-background-color-primary-light);
            }
          }
          .display-card-top-info {
            max-width: calc(100% - 64px);

            .display-card-id {
              height: 24px;
              font-size: 16px;
              line-height: 24px;
              font-weight: 700;
              margin-bottom: 4px;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }
            .display-card-tag-version {
              display: flex;
              .display-card-tag, .display-card-version {
                font-size: 12px;
                font-weight: 500;
                line-height: 16px;
                padding: 0 4px;
                border-radius: 2px;
              }
              .display-card-tag {
                color: rgba(0, 119, 255, 1);
                background: rgba(0, 119, 255, 0.2);
              }
              .display-card-version {
                color: var(--o-text-color-secondary);
                background: var(--o-background-color-tertiary-light);
                margin-left: 8px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
              }
            }
          }
        }

        .display-card-desc {
          height: 44px;
          margin-bottom: 16px;
          > span {
            font-size: 13px;
            line-height: 18px;
            margin-bottom: 16px;
          }
        }

        .display-card-author-time {
          display: flex;
          justify-content: space-between;
          color: var(--o-text-color-tertiary);
          .display-card-author {
            margin-right: 8px;
          }
          div {
            height: 16px;
            line-height: 16px;
            font-size: 12px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }
      }
    }
  }

  .display-list-blank {
    width: 100%;
    height: 196px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: var(--el-color-info);
  }
}

@media only screen and (min-width: 857px) {
  .display-list-container .display-list .display-list-content {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media only screen and (min-width: 1148px) {
  .display-list-container .display-list .display-list-content {
    grid-template-columns: repeat(5, 1fr);
  }
}

</style>