import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/overview',
    },
    {
      path: '/overview',
      name: 'overview',
      component: () => import('./views/DashboardView.vue'),
      meta: { title: 'Overview' },
    },
    {
      path: '/marketplace',
      name: 'marketplace',
      component: () => import('./views/MarketplaceView.vue'),
      meta: { title: 'Marketplace' },
    },
    {
      path: '/businesses',
      name: 'businesses',
      component: () => import('./views/BusinessesView.vue'),
      meta: { title: 'Businesses' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('./views/SettingsView.vue'),
      meta: { title: 'Settings' },
    },
    {
      path: '/fastAPI',
      name: 'fastAPI',
      component: () => import('./views/FastAPIView.vue'),
      meta: { title: 'FastAPI' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/overview',
    },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
