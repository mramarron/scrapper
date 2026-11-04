<template>
  <AuthenticatedLayout>
    <DashboardView />
  </AuthenticatedLayout>
</template>

<script setup lang="ts">
import AuthenticatedLayout from './components/AuthenticatedLayout.vue'
import DashboardView from './views/DashboardView.vue'
</script>
