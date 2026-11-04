<template>
  <section aria-labelledby="page-title">
    <div class="page-heading">
      <div>
        <p class="eyebrow"><span class="eyebrow-line"></span> LOCAL DIRECTORY</p>
        <h1 id="page-title">Local <span>businesses.</span></h1>
        <p class="page-description">Discover businesses and service providers from the Malawi directory.</p>
      </div>
      <button class="button button-primary refresh-button" type="button" :disabled="loading" @click="loadBusinesses">
        <svg :class="{ 'is-spinning': loading }" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8 8 0 0 0-14.7-3L4 10m0 0V5m0 5h5m-5 2a8 8 0 0 0 14.7 3L20 14m0 0v5m0-5h-5" /></svg>
        {{ loading ? 'Refreshing' : 'Refresh data' }}
      </button>
    </div>

    <div v-if="error" class="notice notice-error" role="alert">
      <span class="notice-icon" aria-hidden="true">!</span><span>{{ error }}</span>
      <button class="notice-action" type="button" @click="loadBusinesses">Try again</button>
    </div>

    <section class="directory-panel directory-page-panel" aria-labelledby="businesses-title">
      <div class="panel-toolbar">
        <div class="panel-tabs"><span class="panel-tab is-selected">All businesses <span>{{ filteredBusinesses.length }}</span></span></div>
        <label class="search-field">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></svg>
          <span class="sr-only">Search local businesses</span>
          <input v-model="searchQuery" type="search" placeholder="Search businesses..." />
        </label>
      </div>
      <div class="directory-section">
        <div class="section-heading">
          <div><p class="section-kicker">BUSINESSES TO DISCOVER</p><h2 id="businesses-title">Local directory <span class="section-count">{{ filteredBusinesses.length }}</span></h2></div>
          <span class="source-label"><span class="source-mark source-mark-business">B</span> Mthandizi</span>
        </div>
        <div v-if="loading && !hasLoaded" class="loading-state" role="status"><span class="spinner"></span> Loading businesses…</div>
        <div v-else-if="error && !hasLoaded" class="empty-state">Businesses are unavailable until the directory connection is restored.</div>
        <div v-else-if="filteredBusinesses.length" class="business-grid">
          <article v-for="business in filteredBusinesses" :key="business.id" class="business-card">
            <div class="business-card-top">
              <span class="record-avatar business-avatar" aria-hidden="true">{{ getInitials(business.business_name) }}</span>
              <span class="verified-badge"><span aria-hidden="true">✓</span> Listed</span>
            </div>
            <p class="business-category">{{ business.category || 'Local business' }}</p>
            <h3>{{ business.business_name }}</h3>
            <p class="business-location"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" /><circle cx="12" cy="10" r="2" /></svg>{{ business.location || 'Malawi' }}</p>
            <div class="business-card-footer">
              <a v-if="business.phone_number" :href="`tel:${business.phone_number}`">{{ business.phone_number }}</a>
              <span v-else class="no-contact">Contact details unavailable</span>
              <a v-if="business.email" class="business-email" :href="`mailto:${business.email}`" :aria-label="`Email ${business.business_name}`">Email</a>
              <a class="business-external" :href="business.profile_url" target="_blank" rel="noopener noreferrer" :aria-label="`View ${business.business_name} profile`"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9" /></svg></a>
            </div>
          </article>
        </div>
        <div v-else class="empty-state">{{ searchQuery ? `No businesses match “${searchQuery}”. Try another search.` : 'No businesses have been collected yet.' }}</div>
        <p v-if="hasLoaded && businesses.length" class="results-note">Showing the latest {{ businesses.length }} businesses returned by the directory.</p>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api, { type BusinessLead } from '../services/api'

const businesses = ref<BusinessLead[]>([])
const loading = ref(true)
const hasLoaded = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const filteredBusinesses = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase()
  if (!query) return businesses.value
  return businesses.value.filter((business) =>
    [business.business_name, business.category, business.location, business.phone_number, business.email]
      .some((value) => value?.toLocaleLowerCase().includes(query)),
  )
})

async function loadBusinesses() {
  loading.value = true
  error.value = null
  try {
    const response = await api.get<BusinessLead[]>('/businesses/')
    businesses.value = response.data
    hasLoaded.value = true
  } catch (cause) {
    console.error('Failed to load local businesses from Django.', cause)
    error.value = 'We could not load local businesses. Check your connection and try again.'
  } finally {
    loading.value = false
  }
}

function getInitials(name: string): string {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part.charAt(0)).join('').toLocaleUpperCase()
}

onMounted(loadBusinesses)
</script>
