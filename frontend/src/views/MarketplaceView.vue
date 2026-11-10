<template>
  <section aria-labelledby="page-title">
    <div class="page-heading">
      <div>
        <p class="eyebrow"><span class="eyebrow-line"></span> MARKETPLACE</p>
        <h1 id="page-title">Marketplace <span>listings.</span></h1>
        <p class="page-description">Browse recent items and offers collected from local marketplaces.</p>
      </div>
      <button class="button button-primary refresh-button" type="button" :disabled="loading" @click="loadListings">
        <svg :class="{ 'is-spinning': loading }" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8 8 0 0 0-14.7-3L4 10m0 0V5m0 5h5m-5 2a8 8 0 0 0 14.7 3L20 14m0 0v5m0-5h-5" /></svg>
        {{ loading ? 'Refreshing' : 'Refresh data' }}
      </button>
    </div>

    <div v-if="error" class="notice notice-error" role="alert">
      <span class="notice-icon" aria-hidden="true">!</span><span>{{ error }}</span>
      <button class="notice-action" type="button" @click="loadListings">Try again</button>
    </div>

    <section class="directory-panel directory-page-panel" aria-labelledby="listings-title">
      <div class="panel-toolbar">
        <div class="panel-tabs"><span class="panel-tab is-selected">All listings <span>{{ filteredListings.length }}</span></span></div>
        <label class="search-field">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></svg>
          <span class="sr-only">Search marketplace listings</span>
          <input v-model="searchQuery" type="search" placeholder="Search listings..." />
        </label>
      </div>
      <div class="directory-section">
        <div class="section-heading">
          <div><p class="section-kicker">LATEST FROM THE MARKET</p><h2 id="listings-title">Recent listings <span class="section-count">{{ filteredListings.length }}</span></h2></div>
          <span class="source-label"><span class="source-mark">M</span> Marketplace</span>
        </div>
        <div v-if="loading && !hasLoaded" class="loading-state" role="status"><span class="spinner"></span> Loading marketplace listings…</div>
        <div v-else-if="error && !hasLoaded" class="empty-state">Listings are unavailable until the directory connection is restored.</div>
        <div v-else-if="filteredListings.length" class="record-list">
          <article v-for="listing in filteredListings" :key="listing.id" class="record-row">
            <span class="record-avatar listing-avatar" aria-hidden="true">{{ getInitials(listing.listing_title) }}</span>
            <div class="record-main">
              <div class="record-title-line"><h3>{{ listing.listing_title }}</h3><span v-if="listing.category" class="category-pill">{{ listing.category }}</span></div>
              <p>{{ listing.vendor_name || 'Independent seller' }}<span class="detail-separator">·</span>{{ listing.location_district || 'Malawi' }}</p>
            </div>
            <div class="record-price">{{ formatPrice(listing.item_price) }}</div>
            <a class="record-link" :href="listing.listing_url" target="_blank" rel="noopener noreferrer" :aria-label="`View ${listing.listing_title} on ${listing.source_platform}`">
              <span>{{ listing.source_platform || 'View listing' }}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9" /></svg>
            </a>
          </article>
        </div>
        <div v-else class="empty-state">{{ searchQuery ? `No listings match “${searchQuery}”. Try another search.` : 'No marketplace listings have been collected yet.' }}</div>
        <p v-if="hasLoaded && listings.length" class="results-note">Showing the latest {{ listings.length }} listings returned by the directory.</p>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api, { type ScrapedListing } from '../services/api'

const listings = ref<ScrapedListing[]>([])
const loading = ref(true)
const hasLoaded = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const filteredListings = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase()
  if (!query) return listings.value
  return listings.value.filter((listing) =>
    [listing.listing_title, listing.vendor_name, listing.phone_number, listing.category, listing.location_district, listing.source_platform]
      .some((value) => value?.toLocaleLowerCase().includes(query)),
  )
})

async function loadListings() {
  loading.value = true
  error.value = null
  try {
    const response = await api.get<ScrapedListing[]>('/marketplace-listings/')
    listings.value = response.data
    hasLoaded.value = true
  } catch (cause) {
    console.error('Failed to load marketplace listings from FastAPI.', cause)
    error.value = 'We could not load marketplace listings. Check your connection and try again.'
  } finally {
    loading.value = false
  }
}

function formatPrice(price: string | null): string {
  if (!price) return 'Price not listed'
  const amount = Number(price)
  return Number.isFinite(amount) ? `MK ${amount.toLocaleString('en-MW')}` : price
}

function getInitials(name: string): string {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part.charAt(0)).join('').toLocaleUpperCase()
}

onMounted(loadListings)
</script>
