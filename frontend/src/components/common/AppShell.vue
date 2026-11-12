<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ROLE_LABELS, ROLE_SCOPE } from '@/constants/roles';

const auth = useAuthStore();
const router = useRouter();

const pages = [
  { num: 'I', label: '维度设计', path: '/dimensions' },
  { num: 'II', label: '构建运行', path: '/builds' },
  { num: 'III', label: '当前维度', path: '/dims/current' },
  { num: 'IV', label: '时点回溯', path: '/dims/as-of' },
  { num: 'V', label: '冲突裁决', path: '/conflicts' },
];

function logout() {
  auth.logout();
  router.push('/login');
}
</script>

<template>
  <div class="shell">
    <aside class="rail">
      <div class="rail__brand">
        <span class="rail__brand-mark">SCD Chain</span>
        <span class="rail__brand-sub">嘉禾保险 · 客户维度年鉴 MMXXVI</span>
      </div>
      <div class="rail__rule" />
      <div>
        <p class="rail__contents-label">Contents · 目录</p>
        <nav class="rail__nav">
          <RouterLink
            v-for="page in pages"
            :key="page.path"
            :to="page.path"
            class="rail__link"
            active-class="is-active"
          >
            <span class="rail__link-num">{{ page.num }}</span>
            <span class="rail__link-label">{{ page.label }}</span>
          </RouterLink>
        </nav>
      </div>
      <div class="rail__foot">
        <p v-if="auth.user">{{ auth.user.display_name }} · {{ ROLE_LABELS[auth.role] }}</p>
        <p v-if="auth.user">{{ ROLE_SCOPE[auth.role] }}</p>
        <p v-if="auth.user">{{ auth.user.email }}</p>
        <button class="rail__logout" type="button" @click="logout">退出登录</button>
      </div>
    </aside>
    <main class="page">
      <slot />
    </main>
  </div>
</template>
