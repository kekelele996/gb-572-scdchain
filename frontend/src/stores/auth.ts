import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { User } from '@/types/api';
import * as authApi from '@/api/auth';
import { clearToken, getToken, setToken } from '@/utils/request';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string>(getToken());
  const loading = ref(false);
  const error = ref('');

  const isAuthenticated = computed(() => Boolean(token.value && user.value));
  const role = computed(() => user.value?.role || 'auditor');
  const canEditRules = computed(() => role.value === 'admin');
  const canRunBuild = computed(() => role.value === 'admin' || role.value === 'modeler');
  const canResolve = computed(() => role.value === 'admin' || role.value === 'modeler');

  async function login(email: string, password: string): Promise<void> {
    loading.value = true;
    error.value = '';
    try {
      const result = await authApi.login(email, password);
      token.value = result.access_token;
      setToken(result.access_token);
      user.value = result.user;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '登录失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function hydrate(): Promise<void> {
    if (!getToken()) return;
    try {
      user.value = await authApi.me();
    } catch {
      logout();
    }
  }

  function logout(): void {
    user.value = null;
    token.value = '';
    clearToken();
  }

  return { user, token, loading, error, isAuthenticated, role, canEditRules, canRunBuild, canResolve, login, hydrate, logout };
});
