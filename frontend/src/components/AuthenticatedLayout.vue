<template>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Main sidebar">
      <RouterLink class="brand" to="/overview" aria-label="Directory home">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M4 20V9.5L12 4l8 5.5V20h-5.5v-6h-5v6H4Z" />
            <path d="M8 10h.01M12 10h.01M16 10h.01" />
          </svg>
        </span>
        <span class="brand-copy">
          <strong>Market<span>base</span></strong>
          <small>BUSINESS DIRECTORY</small>
        </span>
      </RouterLink>

      <p class="nav-label">WORKSPACE</p>
      <nav class="primary-nav" aria-label="Workspace navigation">
        <RouterLink class="nav-link" to="/overview">
          <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.5" /></svg>
          Overview
        </RouterLink>
        <RouterLink class="nav-link" to="/marketplace">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5h16M4 12h16M4 18.5h16" /><circle cx="7" cy="5.5" r="1" /><circle cx="7" cy="12" r="1" /><circle cx="7" cy="18.5" r="1" /></svg>
          Marketplace
        </RouterLink>
        <RouterLink class="nav-link" to="/businesses">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 20.5h17M5.5 20.5v-11l6.5-5 6.5 5v11M9 20.5v-5h6v5M9 11h.01M15 11h.01" /></svg>
          Businesses
        </RouterLink>
        <RouterLink class="nav-link" to="/settings">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" /><path d="m19.4 15 .1.1a1.7 1.7 0 0 1-2.4 2.4l-.1-.1a1.7 1.7 0 0 0-2.9 1.2v.2a1.7 1.7 0 0 1-3.4 0v-.2a1.7 1.7 0 0 0-2.9-1.2l-.1.1a1.7 1.7 0 0 1-2.4-2.4l.1-.1a1.7 1.7 0 0 0-1.2-2.9H4a1.7 1.7 0 0 1 0-3.4h.2a1.7 1.7 0 0 0 1.2-2.9l-.1-.1a1.7 1.7 0 0 1 2.4-2.4l.1.1a1.7 1.7 0 0 0 2.9-1.2V2a1.7 1.7 0 0 1 3.4 0v.2a1.7 1.7 0 0 0 2.9 1.2l.1-.1a1.7 1.7 0 0 1 2.4 2.4l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.2a1.7 1.7 0 0 1 0 3.4h-.2a1.7 1.7 0 0 0-1.2 2.9Z" /></svg>
          Settings
        </RouterLink>
      </nav>

      <div class="sidebar-bottom">
        <div class="workspace-card">
          <span class="workspace-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M4 19.5h16M6 16V9m4 7V5m4 11v-4m4 4V7" /></svg>
          </span>
          <span><strong>Malawi market</strong><small>Directory workspace</small></span>
          <span class="status-dot" aria-label="Workspace active"></span>
        </div>
        <div class="profile">
          <span class="profile-avatar" aria-hidden="true">M</span>
          <span class="profile-copy"><strong>Market team</strong><small>Workspace account</small></span>
          <span class="profile-menu" aria-hidden="true">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /></svg>
          </span>
        </div>
      </div>
    </aside>

    <div class="main-shell">
      <header class="topbar">
        <div class="breadcrumb"><span>Workspace</span><span class="breadcrumb-divider">/</span><strong>{{ pageTitle }}</strong></div>
        <div class="topbar-meta">
          <span class="live-indicator"><span></span> DIRECTORY DATA</span>
          <span class="topbar-divider"></span>
          <span class="topbar-region">Malawi</span>
        </div>
      </header>
      <main class="page-content">
        <RouterView v-slot="{ Component, route }">
          <Transition name="page" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </RouterView>
        <footer class="app-footer">
          <span>Marketbase <span aria-hidden="true">·</span> Malawi business directory</span>
          <span>Built for better local connections</span>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const pageTitle = computed(() => String(route.meta.title ?? 'Overview'))
</script>
