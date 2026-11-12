<script setup lang="ts">
import type { DimRow } from '@/types/dim';
import { formatDate } from '@/utils/formatDate';
import { LEVEL_TONE } from '@/constants/customerLevel';
import StatusSeal from './StatusSeal.vue';

withDefaults(defineProps<{ rows: DimRow[]; selectedKey?: string; showRange?: boolean; compact?: boolean }>(), {
  selectedKey: '',
  showRange: true,
  compact: false,
});
defineEmits<{ select: [row: DimRow] }>();
</script>

<template>
  <div class="ledger-wrap">
    <table class="ledger" :class="{ 'ledger--compact': compact }">
      <thead>
        <tr>
          <th>业务键</th>
          <th>姓名</th>
          <th>等级</th>
          <th>归属机构</th>
          <th v-if="!compact">手机号</th>
          <th v-if="showRange !== false">生效区间</th>
          <th>版本</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in rows"
          :key="`${row.business_key}-${row.version}`"
          class="is-clickable"
          :class="{ 'is-selected': selectedKey === row.business_key }"
          @click="$emit('select', row)"
        >
          <td class="ledger__key">{{ row.business_key }}</td>
          <td>{{ row.full_name }}</td>
          <td>
            <StatusSeal :label="row.customer_level" :tone="LEVEL_TONE[row.customer_level] || 'seal--neutral'" />
          </td>
          <td class="mono">{{ row.org_code }}</td>
          <td v-if="!compact" class="mono">{{ row.mobile }}</td>
          <td v-if="showRange !== false" class="mono small">
            {{ formatDate(row.valid_from) }} → {{ row.valid_to ? formatDate(row.valid_to) : '至今' }}
          </td>
          <td class="numeral">
            v{{ row.version }}
            <span v-if="row.version_source === 'manual'" class="small" style="color: var(--rust)">人工</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
