<template>
  <main class="dashboard">
    <header class="page-header">
      <div>
        <p class="eyebrow">MALAWI BUSINESS DIRECTORY</p>
        <h1>Local marketplace</h1>
        <p class="intro">Recent listings and businesses collected from local directories.</p>
      </div>
      <button class="refresh-button" type="button" :disabled="loading" @click="loadData">
        {{ loading ? 'Loading…' : 'Refresh data' }}
      </button>
    </header>

    <p v-if="error" class="notice error-notice" role="alert">{{ error }}</p>
    <p v-else-if="loading" class="notice" role="status">Loading marketplace data…</p>

    <div v-else class="content">
      <section class="data-section" aria-labelledby="listings-heading">
        <div class="section-heading">
          <div>
            <p class="eyebrow">CLASSIFIEDS</p>
            <h2 id="listings-heading">Marketplace listings</h2>
          </div>
          <span class="count">{{ listings.length }}</span>
        </div>

        <p v-if="listings.length === 0" class="empty-state">No marketplace listings have been collected yet.</p>
        <div v-else class="card-grid">
          <article v-for="listing in listings" :key="listing.id" class="data-card">
            <div class="card-topline">
              <span v-if="listing.category" class="tag">{{ listing.category }}</span>
              <span class="source">{{ listing.source_platform }}</span>
            </div>
            <h3>{{ listing.listing_title }}</h3>
            <p class="price">{{ formatPrice(listing.item_price) }}</p>
            <p class="muted">{{ listing.vendor_name }}</p>
            <p v-if="listing.location_district" class="muted">{{ listing.location_district }}</p>
            <a class="card-link" :href="listing.listing_url" target="_blank" rel="noopener noreferrer">
              View listing <span aria-hidden="true">→</span>
            </a>
          </article>
        </div>
      </section>

      <section class="data-section" aria-labelledby="businesses-heading">
        <div class="section-heading">
          <div>
            <p class="eyebrow">DIRECTORY</p>
            <h2 id="businesses-heading">Mthandizi businesses</h2>
          </div>
          <span class="count">{{ businesses.length }}</span>
        </div>

        <p v-if="businesses.length === 0" class="empty-state">No businesses have been collected yet.</p>
        <div v-else class="card-grid">
          <article v-for="business in businesses" :key="business.id" class="data-card">
            <div class="card-topline">
              <span v-if="business.category" class="tag">{{ business.category }}</span>
              <span v-else class="tag">Business</span>
            </div>
            <h3>{{ business.business_name }}</h3>
            <p v-if="business.location" class="muted">{{ business.location }}</p>
            <a v-if="business.phone_number" class="contact-link" :href="`tel:${business.phone_number}`">
              {{ business.phone_number }}
            </a>
            <a v-if="business.email" class="contact-link" :href="`mailto:${business.email}`">
              {{ business.email }}
            </a>
            <a class="card-link" :href="business.profile_url" target="_blank" rel="noopener noreferrer">
              View business <span aria-hidden="true">→</span>
            </a>
          </article>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api, { type BusinessLead, type ScrapedListing } from './services/api'

const listings = ref<ScrapedListing[]>([])
const businesses = ref<BusinessLead[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

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
  } catch (cause) {
    console.error('Failed to load marketplace data from Django.', cause)
    error.value = 'Could not load directory data. Check that the Django server is running and try again.'
  } finally {
    loading.value = false
  }
}

function formatPrice(price: string | null): string {
  if (!price) return 'Price not listed'
  const amount = Number(price)
  return Number.isFinite(amount) ? `MK ${amount.toLocaleString('en-MW')}` : price
}

onMounted(loadData)
</script>

<style scoped>
.dashboard {
  width: min(1120px, 100%);
  margin: 0 auto;
  padding: 48px 28px 72px;
}

.page-header,
.section-heading,
.card-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.page-header {
  margin-bottom: 48px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #43856b;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.12em;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 8px;
  color: #182b25;
  font-size: clamp(2rem, 5vw, 3rem);
  letter-spacing: -0.045em;
}

.intro,
.muted,
.source {
  color: #6b7771;
}

.intro {
  margin-bottom: 0;
}

.refresh-button {
  flex: 0 0 auto;
  border: 0;
  border-radius: 8px;
  padding: 11px 16px;
  color: #fff;
  background: #256c50;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.refresh-button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.data-section + .data-section {
  margin-top: 48px;
}

.section-heading {
  margin-bottom: 18px;
}

.section-heading .eyebrow {
  margin-bottom: 3px;
}

h2 {
  margin-bottom: 0;
  color: #20352d;
  font-size: 1.5rem;
  letter-spacing: -0.025em;
}

.count {
  display: grid;
  min-width: 36px;
  height: 36px;
  place-items: center;
  border-radius: 50%;
  color: #256c50;
  background: #e7f2eb;
  font-weight: 700;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr));
  gap: 16px;
}

.data-card {
  display: flex;
  min-height: 210px;
  flex-direction: column;
  align-items: flex-start;
  border: 1px solid #e3eae5;
  border-radius: 12px;
  padding: 20px;
  background: #fff;
  box-shadow: 0 4px 16px rgb(27 55 42 / 4%);
}

.card-topline {
  width: 100%;
  margin-bottom: 14px;
}

.tag {
  border-radius: 20px;
  padding: 4px 9px;
  color: #286748;
  background: #e7f2eb;
  font-size: 0.75rem;
  font-weight: 600;
}

.source {
  font-size: 0.75rem;
}

h3 {
  margin-bottom: 8px;
  color: #20352d;
  font-size: 1.1rem;
}

.price {
  margin-bottom: 8px;
  color: #256c50;
  font-size: 1.15rem;
  font-weight: 700;
}

.muted {
  margin-bottom: 5px;
  font-size: 0.9rem;
}

.contact-link,
.card-link {
  color: #256c50;
  overflow-wrap: anywhere;
}

.contact-link {
  margin-top: 5px;
  font-size: 0.9rem;
}

.card-link {
  margin-top: auto;
  padding-top: 18px;
  font-size: 0.9rem;
  font-weight: 700;
  text-decoration: none;
}

.card-link:hover {
  text-decoration: underline;
}

.empty-state,
.notice {
  border: 1px solid #e3eae5;
  border-radius: 10px;
  padding: 18px;
  color: #6b7771;
  background: #fff;
}

.error-notice {
  border-color: #e8c4bd;
  color: #8b3022;
  background: #fff8f6;
}

@media (max-width: 600px) {
  .dashboard {
    padding: 32px 18px 48px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
    margin-bottom: 36px;
  }
}
</style>
