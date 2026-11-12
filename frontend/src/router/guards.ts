import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

let hydrated = false;

export async function authGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
): Promise<void> {
  const auth = useAuthStore();
  if (!hydrated) {
    hydrated = true;
    await auth.hydrate();
  }
  const isPublic = Boolean(to.meta.public);
  if (isPublic) {
    if (auth.isAuthenticated) next({ path: '/dims/current' });
    else next();
    return;
  }
  if (!auth.isAuthenticated) {
    next({ path: '/login', query: { next: to.fullPath } });
    return;
  }
  next();
}
