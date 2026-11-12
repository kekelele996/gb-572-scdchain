import { createRouter, createWebHistory } from 'vue-router';
import { authGuard } from './guards';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dims/current' },
    { path: '/login', name: 'login', component: () => import('@/pages/LoginPage.vue'), meta: { public: true } },
    { path: '/dimensions', name: 'dimensions', component: () => import('@/pages/DimensionDesignPage.vue') },
    { path: '/builds', name: 'builds', component: () => import('@/pages/BuildRunsPage.vue') },
    { path: '/dims/current', name: 'current', component: () => import('@/pages/CurrentDimPage.vue') },
    { path: '/dims/as-of', name: 'as-of', component: () => import('@/pages/AsOfPage.vue') },
    { path: '/conflicts', name: 'conflicts', component: () => import('@/pages/ConflictsPage.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/dims/current' },
  ],
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach(authGuard);

export default router;
