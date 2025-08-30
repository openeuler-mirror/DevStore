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
  <!-- 首页 -->
  <div class="home">
    <!-- 顶部数据展示 -->
    <div class="statics">
      <div class="left-div">{{ t('home.mcpServer') }}<div class="server-num">{{ mcpCount }}</div></div>
      <div>{{ t('home.oeDeployPlugin') }}<div class="plugin-num">{{ oedpCount }}</div></div>
    </div>
    <!-- 顶部搜索框 -->
    <div class="search-section">
      <el-input
          v-model="searchInput"
          :placeholder="t('home.placeholder')"
          clearable
          class="search-input"
          @clear="handleClear"
          @keyup.enter="throttledSearch">
        <template #append>
          <el-icon class="search-icon" @click="throttledSearch"><Search /></el-icon>
        </template>
      </el-input>
    </div>
    <!-- 中间数据 -->
    <div class="display-section">
      <!-- 右侧 tab：推荐插件 / 最新发布 -->
      <div class="filter">
        <el-tabs v-model="activeSortTab" class="right-tab" @tab-change="handleSortTabChange">
          <el-tab-pane
              v-for="tab in sortTabs"
              :key="tab.name"
              :label="tab.label"
              :name="tab.name" />
        </el-tabs>
      </div>
      <!-- 左侧 tab：mcp / oedp -->
      <el-tabs v-model="activeTab" class="left-tab" @tab-change="handleTabChange">
        <el-tab-pane
            v-for="tab in tabs"
            :key="tab.name"
            :label="tab.label"
            :name="tab.name">
          <!-- tab label：名称 + 数量 -->
          <template #label>
            {{ tab.label }}
            <!-- 非搜索条件下，展示总数 -->
            <div v-if="searchValue === ''" class="label-sum">{{ tab.count }}</div>
            <!-- 搜索条件下，仅在当前展示 tab 显示搜索结果数 -->
            <div v-else-if="searchValue !== '' && activeTab === tab.name" class="label-sum">{{ count }}</div>
          </template>
          <!-- 子组件：卡片列表 -->
            <grid-display :tag="tab.name as Tag" :item-list="itemList" />
        </el-tab-pane>
      </el-tabs>
      <!-- 分页 -->
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" class="pagination"
                     :page-sizes="[10, 20, 30]" :total="count"
                     layout="total, sizes, prev, pager, next, jumper"
                     @size-change="handleSizeChange" @current-change="handleCurrentChange" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted, onUnmounted, computed, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { throttle } from 'underscore';
import GridDisplay from '@/views/components/GridDisplay.vue';
import { queryList, Tag, type QueryListResponse } from '@/api/index.ts';
import { eventBus, EVENT_TYPES } from '@/utils/eventBus';
import { updateRouteQuery } from '@/utils/index';
import { Search } from '@element-plus/icons-vue';

const route = useRoute();
const showList = ref(true);
const router = useRouter();
const {t} = useI18n();

// 从路由获取当前 tag
const tag = computed(() => route.query.tag ?? 'mcp');

// 搜索框里显示的值 - 从URL参数初始化
const searchInput = ref((route.query.searchValue as string) || '');
// 查询时实际使用的搜索值 - 从URL参数初始化
const searchValue = ref((route.query.searchValue as string) || '');
// 搜索结果个数
const count = ref<number>(0);

// 个数
const mcpCount = ref<number>(0);
const oedpCount = ref<number>(0);

// 查询首页列表信息
const itemList = ref([]);
// 分页 - 从URL参数初始化
const currentPage = ref(parseInt(route.query.curPage as string) || 1);
const pageSize = ref(parseInt(route.query.pageSize as string) || 10);
// 右侧 tab - 从URL参数初始化
const activeSortTab = ref((route.query.sort as string) || 'rec');

const getList = async () => {
  try {
    const res: QueryListResponse = await queryList({
      tag: tag.value as Tag,
      pageSize: pageSize.value,
      curPage: currentPage.value,
      searchValue: searchValue.value,
      sort: activeSortTab.value as 'recommended' | 'newest',
    });
    
    if (res && res.is_success && res.data) {
      itemList.value = res.data.results;
      mcpCount.value = res.data.mcp_count;
      oedpCount.value = res.data.oedp_count;
      
      // 添加：正确更新count变量
      count.value = searchValue.value && searchValue.value.trim() !== ''
        ? res.data.search_count || 0
        : tag.value === 'mcp' ? res.data.mcp_count : res.data.oedp_count;
        
    } else if (res) {
      console.log(res.message);
    }
  } catch (e) {
    console.error('queryList', e);
  }
};

// 改变当前页面展示个数
const handleSizeChange = async (val: number) => {
  currentPage.value = 1;
  pageSize.value = val;
  // 更新URL参数
  await updateRouteQuery(router, route, {
    pageSize: val,
    curPage: 1
  });
  await getList();
};
// 改变当前页码
const handleCurrentChange = async (val: number) => {
  currentPage.value = val;
  // 更新URL参数
  await updateRouteQuery(router, route, {
    curPage: val
  });
  await getList();
};

// 仅在 搜索 且 有搜索值 时，更新 searchValue，并查询
const handleSearch = async () => {
  searchInput.value = searchInput.value.trim();
  if (searchInput.value !== '') {
    searchValue.value = searchInput.value;
    currentPage.value = 1; // 搜索时重置到第一页
    // 更新URL参数
    await updateRouteQuery(router, route, {
      searchValue: searchInput.value,
      curPage: 1
    });
    await getList();
  }
  else {
    // 添加：处理清空搜索的情况
    searchValue.value = '';
    currentPage.value = 1;
    await updateRouteQuery(router, route, {
      searchValue: undefined, // 移除搜索参数
      curPage: 1
    });
    await getList();
  }
};

// 添加节流：搜索
const throttledSearch = throttle(handleSearch, 1000);

// 仅在 有搜索值 时，重置才重新查询
const handleClear = async () => {
  if (searchInput.value.trim() !== '') {
    searchValue.value = '';
    searchInput.value = '';
    // 更新URL参数
    await updateRouteQuery(router, route, {
      searchValue: ''
    });
    await getList();
  }
  searchInput.value = '';
};

// 左侧 tab 切换：mcp / oedp
const activeTab = ref(tag.value || 'mcp');
const tabs = computed(() => [
  { label: t('home.mcpServer'), name: 'mcp', count: mcpCount.value },
  { label: t('home.oeDeployPlugin'), name: 'oedp', count: oedpCount.value }
]);
// 切换左侧 tab 时，重新查询
const handleTabChange = async (tabName: Tag) => {
  currentPage.value = 1;
  // 更新 URL 参数（保留其他已有参数）
  await updateRouteQuery(router, route, {
    tag: tabName as string,
    curPage: 1
  });
  await getList();
};

// 右侧 tab 切换：推荐插件 / 最新发布
const sortTabs = [
  { label: t('home.recommended'), name: 'rec' },
  { label: t('home.newest'), name: 'new' }
];
// 切换右侧 tab 时，重新查询
const handleSortTabChange = async () => {
  // 更新URL参数
  await updateRouteQuery(router, route, {
    sort: activeSortTab.value
  });
  await getList();
};

// 监听 url 中的 tag 变化
watch(
  () => route.query.tag,
  (nv) => {
    if (nv) {
      // 更新激活的 Tab
      activeTab.value = nv;
      // 重新获取数据
    } else {
      // 如果 URL 中没有 type 参数，跳转到默认值
      router.replace({ query: { ...route.query, tag: 'mcp' } });
    }
  },
  { immediate: true }
);

// 轮询
let intervalId: NodeJS.Timeout | null = null;
const getAndCheck = async () => {
  await getList();
  // 判断停止轮询的逻辑加在这里
};

// 监听同步成功事件的处理函数
const handleSyncSuccess = async () => {
  // 立即刷新数据
  await getAndCheck();
};

// 轮询时机
onMounted(async () => {
  // 检查并设置所有必要的URL参数
  const currentQuery = { ...route.query };
  let needsUpdate = false;

  if (!currentQuery.tag) {
    currentQuery.tag = 'mcp';
    needsUpdate = true;
  }
  if (!currentQuery.pageSize) {
    currentQuery.pageSize = pageSize.value.toString();
    needsUpdate = true;
  }
  if (!currentQuery.curPage) {
    currentQuery.curPage = currentPage.value.toString();
    needsUpdate = true;
  }
  if (!currentQuery.sort) {
    currentQuery.sort = activeSortTab.value;
    needsUpdate = true;
  }
  if (!currentQuery.searchValue) {
    currentQuery.searchValue = searchValue.value;
    needsUpdate = true;
  }

  if (needsUpdate) {
    router.replace({ query: currentQuery });
  }
  
  // 立即执行一次
  await getAndCheck();

  // 启动轮询
  intervalId = setInterval(() => {
    getAndCheck();
  }, 10000);

  // 监听同步成功事件
  eventBus.on(EVENT_TYPES.SYNC_SUCCESS, handleSyncSuccess);
});

// 保存当前页面状态到sessionStorage
const savePageState = () => {
  const state = {
    pageSize: pageSize.value,
    curPage: currentPage.value,
    searchValue: searchValue.value,
    sort: activeSortTab.value,
    tag: tag.value
  };
  sessionStorage.setItem('homePageState', JSON.stringify(state));
};

// 在状态变化时保存
watch([pageSize, currentPage, searchValue, activeSortTab, tag], () => {
  savePageState();
});

// 页面卸载时清除定时器和事件监听器
onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
  // 移除事件监听器
  eventBus.off(EVENT_TYPES.SYNC_SUCCESS, handleSyncSuccess);
  // 保存状态
  savePageState();
});

// 页面离开前保存状态
onBeforeUnmount(() => {
  savePageState();
});
</script>

<style lang="scss" scoped>
.home {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  .statics {
    display: flex;
    margin: 32px 0 24px;
    .left-div {
      margin-right: 24px;
    }
    div {
      font-size: 16px;
      line-height: 24px;
      color: var(--o-text-color-secondary);
      display: flex;
      align-items: center;
      .server-num, .plugin-num {
        height: 32px;
        font-size: 24px;
        font-weight: 600;
        line-height: 32px;
        margin-left: 8px;
        padding: 0 12px;
        border-radius: 100px;
      }
      .server-num {
        color: rgba(0, 119, 255, 1);
        background: rgba(0, 119, 255, 0.2);
      }
      .plugin-num {
        color: rgba(45, 180, 124, 1);
        background: rgba(45, 180, 124, 0.2);
      }
    }
  }
  .search-section, .search-section:hover {
    margin-bottom: 24px;
    background: rgba(255, 255, 255, 1);
    border-radius: 100px;
    .search-input {
      width: 440px;
      height: 40px;
      :deep(.el-input__wrapper), :deep(.el-input-group__append) {
        box-shadow: none;
        border-radius: 100px;
        padding-left: 24px;
      }
      :deep(.el-input-group__append) {
        padding: 0 24px 0 0;
      }
      .search-icon {
        color: var(--o-text-color-tertiary);
        :hover {
          cursor: pointer;
        }
      }
    }
  }
  .display-section {
    width: 100%;
    position: relative;
    flex: 1;
    .filter {
      display: flex;
      position: absolute;
      right: 0;
      div {
        margin: 5px 0 5px 16px;
        line-height: 22px;
        color: var(--o-text-color-secondary);
      }
    }
    :deep(.el-tabs) {
      --o-tabs-item-max-width: none;

    }
    :deep(.el-tabs), :deep(.el-tabs__content), :deep(.el-tab-pane) {
      height: 100%;
    }
    :deep(.product-list-container) {
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      .mcp-list-blank {
        flex: 1;
      }
    }
    :deep(.el-tabs__item) {
      height: 32px;
      font-size: 14px;
      line-height: 32px;
      margin-right: 32px;
      padding: 0;
      .label-sum {
        height: 16px;
        font-size: 12px;
        line-height: 16px;
        color: var(--o-text-color-primary);
        font-weight: 700;
        background: var(--o-background-color-tertiary-light);
        margin-left: 8px;
        padding: 0 8px;
        border-radius: 100px;
      }
    }
  }
}
</style>