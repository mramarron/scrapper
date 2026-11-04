<template>
  <main class="mx-auto w-full max-w-6xl px-5 py-8 sm:px-7 sm:py-12">
    <header class="mb-9 flex flex-col items-start justify-between gap-5 sm:mb-12 sm:flex-row sm:items-center">
      <div>
        <p class="mb-2 text-xs font-bold tracking-[0.12em] text-emerald-700">MALAWI BUSINESS DIRECTORY</p>
        <h1 class="mb-2 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">Local marketplace</h1>
        <p class="mb-0 text-slate-500">Recent listings and businesses collected from local directories.</p>
      </div>
      <button
        class="shrink-0 rounded-lg bg-emerald-800 px-4 py-3 font-semibold text-white transition-colors hover:bg-emerald-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800 disabled:cursor-wait disabled:opacity-65"
        type="button"
        :disabled="loading"
        @click="loadData"
      >
        {{ loading ? 'Loading…' : 'Refresh data' }}
      </button>
    </header>

    <p v-if="error" class="rounded-xl border border-red-200 bg-red-50 p-5 text-red-900" role="alert">{{ error }}</p>
    <p v-else-if="loading" class="rounded-xl border border-slate-200 bg-white p-5 text-slate-500" role="status">
      Loading marketplace data…
    </p>

    <div v-else>
      <section class="mb-12" aria-labelledby="listings-heading">
        <div class="mb-5 flex items-center justify-between gap-5">
          <div>
            <p class="mb-1 text-xs font-bold tracking-[0.12em] text-emerald-700">CLASSIFIEDS</p>
            <h2 id="listings-heading" class="mb-0 text-2xl font-semibold tracking-tight text-slate-800">
              Marketplace listings
            </h2>
          </div>
          <span class="grid size-9 place-items-center rounded-full bg-emerald-100 font-bold text-emerald-800">
            {{ listings.length }}
          </span>
        </div>

        <p v-if="listings.length === 0" class="rounded-xl border border-slate-200 bg-white p-5 text-slate-500">
          No marketplace listings have been collected yet.
        </p>
        <div v-else class="grid grid-cols-[repeat(auto-fill,minmax(min(100%,260px),1fr))] gap-4">
          <article
            v-for="listing in listings"
            :key="listing.id"
            class="flex min-h-[210px] flex-col items-start rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div class="mb-4 flex w-full items-center justify-between gap-5">
              <span v-if="listing.category" class="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                {{ listing.category }}
              </span>
              <span class="text-xs text-slate-500">{{ listing.source_platform }}</span>
            </div>
            <h3 class="mb-2 text-lg font-semibold text-slate-800">{{ listing.listing_title }}</h3>
            <p class="mb-2 text-lg font-bold text-emerald-800">{{ formatPrice(listing.item_price) }}</p>
            <p class="mb-1 text-sm text-slate-500">{{ listing.vendor_name }}</p>
            <p v-if="listing.location_district" class="mb-1 text-sm text-slate-500">{{ listing.location_district }}</p>
            <a
              class="mt-auto pt-5 text-sm font-bold text-emerald-800 hover:underline focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
              :href="listing.listing_url"
              target="_blank"
              rel="noopener noreferrer"
            >
              View listing <span aria-hidden="true">→</span>
            </a>
          </article>
        </div>
      </section>

      <section aria-labelledby="businesses-heading">
        <div class="mb-5 flex items-center justify-between gap-5">
          <div>
            <p class="mb-1 text-xs font-bold tracking-[0.12em] text-emerald-700">DIRECTORY</p>
            <h2 id="businesses-heading" class="mb-0 text-2xl font-semibold tracking-tight text-slate-800">
              Mthandizi businesses
            </h2>
          </div>
          <span class="grid size-9 place-items-center rounded-full bg-emerald-100 font-bold text-emerald-800">
            {{ businesses.length }}
          </span>
        </div>

        <p v-if="businesses.length === 0" class="rounded-xl border border-slate-200 bg-white p-5 text-slate-500">
          No businesses have been collected yet.
        </p>
        <div v-else class="grid grid-cols-[repeat(auto-fill,minmax(min(100%,260px),1fr))] gap-4">
          <article
            v-for="business in businesses"
            :key="business.id"
            class="flex min-h-[210px] flex-col items-start rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div class="mb-4 flex w-full items-center justify-between gap-5">
              <span class="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                {{ business.category || 'Business' }}
              </span>
            </div>
            <h3 class="mb-2 text-lg font-semibold text-slate-800">{{ business.business_name }}</h3>
            <p v-if="business.location" class="mb-1 text-sm text-slate-500">{{ business.location }}</p>
            <a
              v-if="business.phone_number"
              class="mt-1 break-all text-sm text-emerald-800 hover:underline"
              :href="`tel:${business.phone_number}`"
            >
              {{ business.phone_number }}
            </a>
            <a
              v-if="business.email"
              class="mt-1 break-all text-sm text-emerald-800 hover:underline"
              :href="`mailto:${business.email}`"
            >
              {{ business.email }}
            </a>
            <a
              class="mt-auto pt-5 text-sm font-bold text-emerald-800 hover:underline focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-800"
              :href="business.profile_url"
              target="_blank"
              rel="noopener noreferrer"
            >
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
