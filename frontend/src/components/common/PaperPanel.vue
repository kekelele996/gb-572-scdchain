<script setup lang="ts">
defineProps<{ title?: string; kicker?: string; hint?: string; flush?: boolean }>();
</script>

<template>
  <section class="panel" :class="{ 'panel--flush': flush }">
    <header v-if="title || $slots.actions" class="panel__head">
      <div>
        <p v-if="kicker" class="eyebrow">{{ kicker }}</p>
        <h2 v-if="title" class="panel__title">{{ title }}</h2>
        <p v-if="hint" class="panel__hint">{{ hint }}</p>
      </div>
      <div class="row">
        <slot name="actions" />
      </div>
    </header>
    <slot />
  </section>
</template>
