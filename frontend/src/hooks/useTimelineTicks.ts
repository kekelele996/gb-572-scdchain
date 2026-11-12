import { computed, type Ref } from 'vue';

export interface Tick {
  index: number;
  x: number;
  label: string;
  date: string;
}

export function useTimelineTicks(dates: Ref<string[]>, width = 720, padding = 30) {
  const ticks = computed<Tick[]>(() => {
    const list = dates.value;
    if (!list.length) return [];
    const span = width - padding * 2;
    const step = list.length > 1 ? span / (list.length - 1) : 0;
    return list.map((date, index) => ({
      index,
      x: padding + index * step,
      label: date.slice(5).replace('-', '.'),
      date,
    }));
  });

  return { ticks, width, padding };
}
