<script setup lang="ts">
import type { DimRow } from '@/types/dim';
import { formatDate } from '@/utils/formatDate';

defineProps<{ versions: DimRow[] }>();
</script>

<template>
  <div class="chain">
    <div v-for="row in versions" :key="row.version" class="chain__row">
      <span class="chain__index">{{ row.version }}</span>
      <div
        class="chain__card"
        :class="{
          'chain__card--current': row.is_current,
          'chain__card--manual': row.version_source === 'manual',
        }"
      >
        <div class="spread">
          <span class="chain__range">
            {{ formatDate(row.valid_from) }} → {{ row.valid_to ? formatDate(row.valid_to) : '至今' }}
          </span>
          <span class="small muted">
            {{ row.is_current ? '当前链' : '已关链' }}
            <template v-if="row.version_source === 'manual'"> · 人工覆盖</template>
          </span>
        </div>
        <div class="chain__attrs">
          <span>等级 <strong>{{ row.customer_level }}</strong></span>
          <span>机构 {{ row.org_code }}</span>
          <span>姓名 {{ row.full_name }}</span>
          <span v-if="row.change_fields.length">变更字段：{{ row.change_fields.join(' / ') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
