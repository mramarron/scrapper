<template>
  <div id="overview">
    <section class="page-heading" aria-labelledby="page-title">
      <div>
        <p class="eyebrow"><span class="eyebrow-line"></span> MARKET INTELLIGENCE</p>
        <h1 id="page-title">Your directory, <span>at a glance.</span></h1>
        <p class="page-description">Explore the latest marketplace listings and local businesses in Malawi.</p>
      </div>
      <button class="button button-primary refresh-button" type="button" :disabled="loading" @click="loadData">
        <svg :class="{ 'is-spinning': loading }" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8 8 0 0 0-14.7-3L4 10m0 0V5m0 5h5m-5 2a8 8 0 0 0 14.7 3L20 14m0 0v5m0-5h-5" /></svg>
        {{ loading ? 'Refreshing' : 'Refresh data' }}
      </button>
    </section>

    <div v-if="error" class="notice notice-error" role="alert">
      <span class="notice-icon" aria-hidden="true">!</span>
      <span>{{ error }}</span>
      <button class="notice-action" type="button" @click="loadData">Try again</button>
    </div>

    <section class="stats-grid" aria-label="Directory summary">
      <article class="stat-card">
        <div class="stat-heading"><span>Marketplace listings</span><span class="stat-icon icon-mint"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7.5h16l-1.5 13h-13L4 7.5ZM8 8V6a4 4 0 0 1 8 0v2" /></svg></span></div>
        <div class="stat-value">{{ loading && !hasLoaded ? '—' : listings.length }}</div>
        <p><span class="stat-dot"></span> Listings collected</p>
      </article>
      <article class="stat-card">
        <div class="stat-heading"><span>Local businesses</span><span class="stat-icon icon-lilac"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 20.5h17M5.5 20.5v-11l6.5-5 6.5 5v11M9 20.5v-5h6v5M9 11h.01M15 11h.01" /></svg></span></div>
        <div class="stat-value">{{ loading && !hasLoaded ? '—' : businesses.length }}</div>
        <p><span class="stat-dot dot-lilac"></span> Businesses in directory</p>
      </article>
      <article class="stat-card stat-card-highlight">
        <div class="stat-heading"><span>Total records</span><span class="stat-icon icon-peach"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4.5h14v15H5zM8 8h8M8 12h8M8 16h4" /></svg></span></div>
        <div class="stat-value">{{ loading && !hasLoaded ? '—' : listings.length + businesses.length }}</div>
        <p><span class="stat-dot dot-peach"></span> Across both sources</p>
      </article>
      <article class="stat-card">
        <div class="stat-heading"><span>Last updated</span><span class="stat-icon icon-blue"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3.5 2" /></svg></span></div>
        <div class="stat-value stat-value-date">{{ latestUpdated }}</div>
        <p><span class="stat-dot dot-blue"></span> Most recent collection</p>
      </article>
    </section>

    <section class="directory-panel" aria-label="Directory records">
      <div class="panel-toolbar">
        <div class="panel-tabs" aria-label="Directory sections">
          <a class="panel-tab" :class="{ 'is-selected': activeDirectory === '#listings' }" href="#listings" :aria-current="activeDirectory === '#listings' ? 'page' : undefined">Marketplace <span>{{ listings.length }}</span></a>
          <a class="panel-tab" :class="{ 'is-selected': activeDirectory === '#businesses' }" href="#businesses" :aria-current="activeDirectory === '#businesses' ? 'page' : undefined">Businesses <span>{{ businesses.length }}</span></a>
        </div>
        <label class="search-field">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></svg>
          <span class="sr-only">Search listings and businesses</span>
          <input v-model="searchQuery" type="search" placeholder="Search directory..." />
        </label>
      </div>

      <section id="listings" class="directory-section" aria-labelledby="listings-title">
        <div class="section-heading">
          <div>
            <p class="section-kicker">FROM THE MARKETPLACE</p>
            <h2 id="listings-title">Recent listings <span class="section-count">{{ filteredListings.length }}</span></h2>
          </div>
          <span class="source-label"><span class="source-mark">M</span> Marketplace</span>
        </div>

        <div v-if="loading && !hasLoaded" class="loading-state" role="status">
          <span class="spinner"></span> Loading marketplace listings…
        </div>
        <div v-else-if="error && !hasLoaded" class="empty-state">Listings are unavailable until the directory connection is restored.</div>
        <div v-else-if="filteredListings.length" class="record-list">
          <article v-for="listing in filteredListings" :key="listing.id" class="record-row">
            <span class="record-avatar listing-avatar" aria-hidden="true">{{ getInitials(listing.listing_title) }}</span>
            <div class="record-main">
              <div class="record-title-line">
                <h3>{{ listing.listing_title }}</h3>
                <span v-if="listing.category" class="category-pill">{{ listing.category }}</span>
              </div>
              <p>{{ listing.vendor_name || 'Independent seller' }}<span class="detail-separator">·</span>{{ listing.location_district || 'Malawi' }}</p>
            </div>
            <div class="record-price">{{ formatPrice(listing.item_price) }}</div>
            <a class="record-link" :href="listing.listing_url" target="_blank" rel="noopener noreferrer" :aria-label="`View ${listing.listing_title} on ${listing.source_platform}`">
              <span>{{ listing.source_platform || 'View listing' }}</span>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9" /></svg>
            </a>
          </article>
        </div>
        <div v-else-if="searchQuery" class="empty-state">No listings match “{{ searchQuery }}”. Try another search.</div>
        <div v-else class="empty-state">No marketplace listings have been collected yet.</div>
      </section>

      <section id="businesses" class="directory-section business-section" aria-labelledby="businesses-title">
        <div class="section-heading">
          <div>
            <p class="section-kicker">LOCAL DIRECTORY</p>
            <h2 id="businesses-title">Businesses to discover <span class="section-count">{{ filteredBusinesses.length }}</span></h2>
          </div>
          <span class="source-label"><span class="source-mark source-mark-business">B</span> Mthandizi</span>
        </div>

        <div v-if="loading && !hasLoaded" class="loading-state" role="status">
          <span class="spinner"></span> Loading businesses…
        </div>
        <div v-else-if="error && !hasLoaded" class="empty-state">Businesses are unavailable until the directory connection is restored.</div>
        <div v-else-if="filteredBusinesses.length" class="business-grid">
          <article v-for="business in filteredBusinesses" :key="business.id" class="business-card">
            <div class="business-card-top">
              <span class="record-avatar business-avatar" aria-hidden="true">{{ getInitials(business.business_name) }}</span>
              <span class="verified-badge"><span aria-hidden="true">✓</span> Listed</span>
            </div>
            <p class="business-category">{{ business.category || 'Local business' }}</p>
            <h3>{{ business.business_name }}</h3>
            <p class="business-location">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" /><circle cx="12" cy="10" r="2" /></svg>
              {{ business.location || 'Malawi' }}
            </p>
            <div class="business-card-footer">
              <a v-if="business.phone_number" :href="`tel:${business.phone_number}`">{{ business.phone_number }}</a>
              <span v-else class="no-contact">Contact details unavailable</span>
              <a class="business-external" :href="business.profile_url" target="_blank" rel="noopener noreferrer" :aria-label="`View ${business.business_name} profile`">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9" /></svg>
              </a>
            </div>
          </article>
        </div>
        <div v-else-if="searchQuery" class="empty-state">No businesses match “{{ searchQuery }}”. Try another search.</div>
        <div v-else class="empty-state">No businesses have been collected yet.</div>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import api, { type BusinessLead, type ScrapedListing } from '../services/api'

const listings = ref<ScrapedListing[]>([])
const businesses = ref<BusinessLead[]>([])
const loading = ref(true)
const hasLoaded = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const activeDirectory = ref('#listings')

const normalizedQuery = computed(() => searchQuery.value.trim().toLocaleLowerCase())

const filteredListings = computed(() => {
  if (!normalizedQuery.value) return listings.value
  return listings.value.filter((listing) =>
    [listing.listing_title, listing.vendor_name, listing.phone_number, listing.category, listing.location_district, listing.source_platform]
      .some((value) => value?.toLocaleLowerCase().includes(normalizedQuery.value)),
  )
})

const filteredBusinesses = computed(() => {
  if (!normalizedQuery.value) return businesses.value
  return businesses.value.filter((business) =>
    [business.business_name, business.category, business.location, business.phone_number, business.email]
      .some((value) => value?.toLocaleLowerCase().includes(normalizedQuery.value)),
  )
})

const latestUpdated = computed(() => {
  const timestamps = [
    ...listings.value.map((listing) => listing.scraped_at),
    ...businesses.value.map((business) => business.scraped_at),
  ]
    .map((timestamp) => new Date(timestamp))
    .filter((date) => !Number.isNaN(date.getTime()))

  if (!timestamps.length) return hasLoaded.value ? 'No data yet' : '—'
  const latest = new Date(Math.max(...timestamps.map((date) => date.getTime())))
  return new Intl.DateTimeFormat('en-MW', { day: 'numeric', month: 'short', year: 'numeric' }).format(latest)
})

async function loadData() {
  loading.value = true
  error.value = null

  try {
    const [listingResponse, businessResponse] = await Promise.all([
      api.get<ScrapedListing[]>('/marketplace-listings/'),
      api.get<BusinessLead[]>('/businesses/'),
    ])
    listings.value = listingResponse.data
    businesses.value = businessResponse.data
    hasLoaded.value = true
  } catch (cause) {
    console.error('Failed to load directory data from Django.', cause)
    error.value = 'We could not load the latest directory data. Check your connection and try again.'
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
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0))
    .join('')
    .toLocaleUpperCase()
}

function syncActiveDirectory() {
  activeDirectory.value = window.location.hash === '#businesses' ? '#businesses' : '#listings'
}

onMounted(() => {
  syncActiveDirectory()
  window.addEventListener('hashchange', syncActiveDirectory)
  loadData()
})

onUnmounted(() => {
  window.removeEventListener('hashchange', syncActiveDirectory)
})
</script>
