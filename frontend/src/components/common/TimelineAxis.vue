<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  dates: string[];
  active?: string;
  markers?: { date: string; label: string; tone?: 'warn' | 'ok' }[];
  clickable?: boolean;
}>();
const emit = defineEmits<{ pick: [date: string] }>();

const width = 900;
const padding = 54;

const ticks = computed(() => {
  const list = props.dates;
  if (!list.length) return [] as { x: number; label: string; date: string; active: boolean }[];
  const span = width - padding * 2;
  const step = list.length > 1 ? span / (list.length - 1) : 0;
  return list.map((date, index) => ({
    x: padding + index * step,
    label: date.slice(5).replace('-', '.'),
    date,
    active: date === props.active,
  }));
});

const markerPoints = computed(() =>
  (props.markers || []).map((marker) => {
    const tick = ticks.value.find((item) => item.date === marker.date);
    return tick ? { ...marker, x: tick.x } : null;
  }).filter((item): item is NonNullable<typeof item> => Boolean(item)),
);
</script>

<template>
  <div class="timeline">
    <svg :viewBox="`0 0 ${width} 118`" role="img" aria-label="快照日期时间轴">
      <line :x1="padding" :x2="width - padding" y1="66" y2="66" stroke="oklch(52% 0.028 252)" stroke-width="1" />
      <g v-for="tick in ticks" :key="tick.date" @click="clickable && emit('pick', tick.date)">
        <line
          :x1="tick.x"
          :x2="tick.x"
          y1="58"
          :y2="tick.active ? 42 : 48"
          :stroke="tick.active ? 'oklch(53% 0.112 43)' : 'oklch(64% 0.02 250)'"
          stroke-width="1.5"
        />
        <circle
          :cx="tick.x"
          cy="66"
          :r="tick.active ? 5.5 : 3.5"
          :fill="tick.active ? 'oklch(53% 0.112 43)' : 'oklch(95.6% 0.017 86)'"
          stroke="oklch(38% 0.035 256)"
          stroke-width="1.2"
        />
        <text
          :x="tick.x"
          y="88"
          text-anchor="middle"
          font-family="'Libre Baskerville', Georgia, serif"
          font-size="11"
          :fill="tick.active ? 'oklch(44% 0.1 40)' : 'oklch(52% 0.028 252)'"
        >
          {{ tick.label }}
        </text>
        <text :x="tick.x" y="104" text-anchor="middle" font-size="9" fill="oklch(64% 0.02 250)">2026</text>
      </g>
      <g v-for="marker in markerPoints" :key="`m-${marker.date}-${marker.label}`">
        <line
          :x1="marker.x"
          :x2="marker.x"
          y1="66"
          y2="26"
          :stroke="marker.tone === 'warn' ? 'oklch(53% 0.112 43)' : 'oklch(50% 0.055 152)'"
          stroke-dasharray="3 3"
          stroke-width="1"
        />
        <text
          :x="marker.x"
          y="20"
          text-anchor="middle"
          font-size="9.5"
          :fill="marker.tone === 'warn' ? 'oklch(44% 0.1 40)' : 'oklch(50% 0.055 152)'"
        >
          {{ marker.label }}
        </text>
      </g>
    </svg>
    <div class="timeline__caption">
      <span>2026 年 11 月 · 每日全量快照</span>
      <span>横向时间轴 · 点击刻度切换回溯日期</span>
    </div>
  </div>
</template>
