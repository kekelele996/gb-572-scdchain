<script setup lang="ts">
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const email = ref('admin@scdchain.io');
const password = ref('Demo@2026');
const error = ref('');

const demoAccounts = [
  { email: 'admin@scdchain.io', role: '建模负责人 · 规则与发布' },
  { email: 'modeler@scdchain.io', role: '建模工程师 · 构建与裁决' },
  { email: 'auditor@scdchain.io', role: '审计只读 · 回溯与导出' },
];

async function submit() {
  error.value = '';
  try {
    await auth.login(email.value.trim(), password.value);
    const next = typeof route.query.next === 'string' ? route.query.next : '/dims/current';
    router.push(next);
  } catch (err) {
    error.value = err instanceof Error ? err.message : '登录失败';
  }
}

function fillDemo(target: string) {
  email.value = target;
  password.value = 'Demo@2026';
}
</script>

<template>
  <div class="login">
    <section class="login__cover">
      <p class="login__year">MMXXVI · 嘉禾保险数据仓库建模组</p>
      <h1 class="login__title">客户维度<br />编年年鉴</h1>
      <p class="login__lede">
        三个核心系统每日全量快照汇入，按业务键拉出 SCD2 链；
        任何一天当时的客户等级、归属机构，都能在时间轴上翻回原页。
      </p>
      <div class="login__ledger">
        <div><strong>3</strong> 个上游源系统 · 核心保单 / 会员中心 / 客服工单</div>
        <div><strong>180</strong> 个客户业务键 · <strong>900</strong> 行每日快照</div>
        <div><strong>210</strong> 条基线拉链 · 每键唯一当前链</div>
        <div><strong>24</strong> 条跨源冲突候选 · 归一化裁决 + 人工留痕</div>
      </div>
      <p class="small" style="color: oklch(74% 0.03 88)">
        监管报送要「当时等级」；BI 只认「当前链」。这本年鉴让两边看到同一页。
      </p>
    </section>

    <section class="login__form">
      <div>
        <p class="eyebrow">Sign in · 进入档案室</p>
        <h2 class="login__form-title">查验身份</h2>
        <p class="small muted" style="margin-top: 8px">
          审计同事用 auditor 账号只读回溯；规则与发布仅 admin 可改。
        </p>
      </div>

      <form class="stack" @submit.prevent="submit">
        <div class="form-row">
          <label for="email">邮箱</label>
          <input id="email" v-model="email" class="input" type="email" autocomplete="username" required />
        </div>
        <div class="form-row">
          <label for="password">密码</label>
          <input id="password" v-model="password" class="input" type="password" autocomplete="current-password" required />
        </div>
        <p v-if="error" class="form-error">{{ error }}</p>
        <button class="btn btn--primary" type="submit" :disabled="auth.loading">
          {{ auth.loading ? '核对中…' : '进入年鉴' }}
        </button>
      </form>

      <div class="login__hint">
        <p style="margin-bottom: 6px">演示账号（密码统一 <code>Demo@2026</code>）</p>
        <div class="stack" style="gap: 6px">
          <button
            v-for="account in demoAccounts"
            :key="account.email"
            type="button"
            class="btn btn--ghost btn--small"
            style="justify-content: space-between"
            @click="fillDemo(account.email)"
          >
            <span>{{ account.email }}</span>
            <span class="small muted">{{ account.role }}</span>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
