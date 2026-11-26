<template>
  <section aria-labelledby="page-title">
    <div class="page-heading">
      <div>
        <p class="eyebrow"><span class="eyebrow-line"></span> BUSINESS PROFILE</p>
        <h1 id="page-title">{{ business?.business_name ?? 'Business details' }}</h1>
        <p class="page-description">Full directory and taxpayer verification details.</p>
      </div>
      <RouterLink class="button button-primary" to="/businesses">Back to businesses</RouterLink>
    </div>

    <div v-if="loading" class="loading-state" role="status">
      <span class="spinner"></span> Loading business details…
    </div>
    <div v-else-if="error" class="notice notice-error" role="alert">
      <span class="notice-icon" aria-hidden="true">!</span>
      <span>{{ error }}</span>
      <button class="notice-action" type="button" @click="loadBusiness">Try again</button>
    </div>
    <div v-else-if="!business" class="empty-state business-detail-empty">
      This business could not be found in the directory.
    </div>

    <div v-else class="business-detail-layout">
      <section class="directory-panel business-detail-panel" aria-labelledby="business-information-title">
        <div class="business-detail-profile">
          <span class="business-detail-avatar" aria-hidden="true">{{ getInitials(business.business_name) }}</span>
          <div class="business-detail-identity">
            <p class="section-kicker">BUSINESS INFORMATION</p>
            <h2 id="business-information-title">{{ business.business_name }}</h2>
            <p>{{ business.category || 'Local business' }}</p>
          </div>
          <span class="business-verification-badge" :class="verificationClass">
            {{ verificationLabel }}
          </span>
        </div>

        <dl class="business-detail-list">
          <div class="business-detail-item">
            <dt>Category</dt>
            <dd>{{ business.category || 'Not provided' }}</dd>
          </div>
          <div class="business-detail-item">
            <dt>Location</dt>
            <dd>{{ business.location || 'Not provided' }}</dd>
          </div>
          <div class="business-detail-item">
            <dt>Phone</dt>
            <dd>
              <a v-if="business.phone_number" :href="`tel:${business.phone_number}`">{{ business.phone_number }}</a>
              <span v-else>Not provided</span>
            </dd>
          </div>
          <div class="business-detail-item">
            <dt>Email</dt>
            <dd>
              <a v-if="business.email" :href="`mailto:${business.email}`">{{ business.email }}</a>
              <span v-else>Not provided</span>
            </dd>
          </div>
          <div class="business-detail-item">
            <dt>Taxpayer identification number</dt>
            <dd>{{ business.matched_tin || 'No approved TIN' }}</dd>
          </div>
          <div class="business-detail-item">
            <dt>Verification check</dt>
            <dd>{{ business.is_checked ? 'Checked against taxpayer records' : 'Not checked yet' }}</dd>
          </div>
          <div class="business-detail-item">
            <dt>Added to directory</dt>
            <dd><time :datetime="business.scraped_at">{{ formattedScrapedAt }}</time></dd>
          </div>
          <div class="business-detail-item">
            <dt>Directory profile</dt>
            <dd>
              <a
                v-if="business.profile_url"
                :href="business.profile_url"
                target="_blank"
                rel="noopener noreferrer"
              >Open original profile</a>
              <span v-else>Not available</span>
            </dd>
          </div>
        </dl>
      </section>

      <section class="directory-panel business-detail-panel" aria-labelledby="taxpayer-matches-title">
        <div class="business-matches-heading">
          <div>
            <p class="section-kicker">TAXPAYER VERIFICATION</p>
            <h2 id="taxpayer-matches-title">Potential matches</h2>
          </div>
          <span class="section-count">{{ business.taxpayer_matches.length }}</span>
        </div>

        <ul v-if="business.taxpayer_matches.length" class="business-match-list">
          <li
            v-for="match in business.taxpayer_matches"
            :key="match.id"
            class="business-match-row"
          >
            <div>
              <strong>{{ match.taxpayer_business_name }}</strong>
              <small>Taxpayer record candidate</small>
            </div>
            <span class="business-match-status" :class="`is-${match.status}`">
              {{ match.status }}
            </span>
          </li>
        </ul>
        <p v-else class="business-no-matches">
          {{ business.is_checked ? 'No matching taxpayer records were found.' : 'No taxpayer search has been run for this business.' }}
        </p>
      </section>

      <section class="directory-panel business-detail-panel business-listing-chart-panel" aria-labelledby="listing-activity-title">
        <div class="business-matches-heading">
          <div>
            <p class="section-kicker">MARKETPLACE ACTIVITY</p>
            <h2 id="listing-activity-title">Listings over the last 14 days</h2>
          </div>
          <span class="business-listing-total">{{ matchingListings.length }} matched</span>
        </div>

        <p v-if="listingLoading" class="chart-message" role="status">Loading marketplace listing activity…</p>
        <div v-else-if="listingError" class="business-listing-chart-error" role="alert">
          <span>{{ listingError }}</span>
          <button class="notice-action" type="button" @click="loadMarketplaceListings">Try again</button>
        </div>
        <p v-else-if="!hasListingActivity" class="chart-message">
          No matching listings were found in the last 14 days.
        </p>
        <ChartContainer
          v-else
          :config="listingActivityChartConfig"
          class="business-listing-chart-canvas"
          role="img"
          :aria-label="listingActivityChartLabel"
        >
          <VisXYContainer :data="listingActivity" :margin="{ top: 16, right: 8, bottom: 22, left: 8 }">
            <VisLine
              :x="listingActivityX"
              :y="listingActivityY"
              :color="[listingActivityChartConfig.count.color]"
              :line-width="3"
            />
            <VisAxis
              type="x"
              :x="listingActivityX"
              :tick-values="listingActivity.map((day) => day.timestamp)"
              :tick-format="activityTickFormat"
              :tick-line="false"
              :domain-line="false"
              :grid-line="false"
            />
            <VisAxis
              type="y"
              :tick-format="(count: number) => String(count)"
              :tick-line="false"
              :domain-line="false"
              :grid-line="true"
            />
            <ChartTooltip />
            <ChartCrosshair
              :x="listingActivityX"
              :y="listingActivityY"
              :template="listingActivityTooltipTemplate"
              :color="[listingActivityChartConfig.count.color]"
            />
          </VisXYContainer>
        </ChartContainer>
        <p class="chart-footnote">
          Vendor names are matched to this business name. Results use the latest 50 marketplace listings and may not include every item.
        </p>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { VisAxis, VisLine, VisXYContainer } from '@unovis/vue'
import { useRoute } from 'vue-router'
import type { ChartConfig } from '@/components/ui/chart'
import {
  ChartContainer,
  ChartCrosshair,
  ChartTooltip,
  ChartTooltipContent,
  componentToString,
} from '@/components/ui/chart'
import api, { type BusinessLead, type ScrapedListing } from '../services/api'

interface ListingActivityDay {
  dateLabel: string
  timestamp: number
  count: number
}

const route = useRoute()
const business = ref<BusinessLead | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const marketplaceListings = ref<ScrapedListing[]>([])
const listingLoading = ref(false)
const listingError = ref<string | null>(null)

const listingActivityChartConfig = {
  count: {
    label: 'Listings',
    color: '#56a176',
  },
} satisfies ChartConfig

const verificationLabel = computed(() => {
  if (!business.value) return ''
  if (business.value.matched_tin) return 'Verified'
  if (
    !business.value.is_checked
    || business.value.taxpayer_matches.some((match) => match.status === 'pending')
  ) {
    return 'Pending'
  }
  return 'Not found'
})
const verificationClass = computed(() => `is-${verificationLabel.value.toLocaleLowerCase().replaceAll(' ', '-')}`)
const formattedScrapedAt = computed(() => {
  const date = new Date(business.value?.scraped_at ?? '')
  if (Number.isNaN(date.getTime())) return 'Not available'
  return new Intl.DateTimeFormat('en-MW', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
})
const matchingListings = computed(() => {
  const businessName = normalizeName(business.value?.business_name ?? '')
  if (!businessName) return []
  return marketplaceListings.value.filter(
    (listing) => normalizeName(listing.vendor_name) === businessName,
  )
})
const listingActivity = computed<ListingActivityDay[]>(() => {
  const today = new Date()
  const days = Array.from({ length: 14 }, (_, index) => {
    const date = new Date(today)
    date.setHours(0, 0, 0, 0)
    date.setDate(today.getDate() - (13 - index))
    return {
      dateLabel: new Intl.DateTimeFormat('en-MW', { day: 'numeric', month: 'short' }).format(date),
      timestamp: date.getTime(),
      count: 0,
    }
  })
  const counts = new Map(days.map((day) => [dateKey(new Date(day.timestamp)), day]))

  for (const listing of matchingListings.value) {
    const date = new Date(listing.scraped_at)
    if (Number.isNaN(date.getTime())) continue
    const day = counts.get(dateKey(date))
    if (day) day.count += 1
  }

  return days
})
const hasListingActivity = computed(() => listingActivity.value.some((day) => day.count > 0))
const listingActivityChartLabel = computed(() =>
  `Marketplace listings matching ${business.value?.business_name ?? 'this business'} over the last fourteen days: ${listingActivity.value.map((day) => `${day.dateLabel}, ${day.count}`).join('; ')}`,
)
const listingActivityTooltipTemplate = componentToString(
  listingActivityChartConfig,
  ChartTooltipContent,
  {
    labelFormatter: (timestamp) =>
      new Intl.DateTimeFormat('en-MW', { day: 'numeric', month: 'short' }).format(
        timestamp instanceof Date ? timestamp : new Date(timestamp),
      ),
  },
)
const listingActivityX = (day: ListingActivityDay) => day.timestamp
const listingActivityY = (day: ListingActivityDay) => day.count
const activityTickFormat = (timestamp: number) => String(new Date(timestamp).getDate())

async function loadBusiness() {
  loading.value = true
  error.value = null
  business.value = null

  const id = Number(route.params.id)
  if (!Number.isSafeInteger(id) || id < 1) {
    loading.value = false
    return
  }

  try {
    const response = await api.get<BusinessLead[]>('/businesses/')
    business.value = response.data.find((entry) => entry.id === id) ?? null
    if (business.value) void loadMarketplaceListings()
  } catch (cause) {
    console.error('Failed to load business details from FastAPI.', cause)
    error.value = 'We could not load this business. Check your connection and try again.'
  } finally {
    loading.value = false
  }
}

async function loadMarketplaceListings() {
  listingLoading.value = true
  listingError.value = null
  try {
    const response = await api.get<ScrapedListing[]>('/marketplace-listings/')
    marketplaceListings.value = response.data
  } catch (cause) {
    console.error('Failed to load marketplace listings for the business profile.', cause)
    listingError.value = 'Marketplace listing activity could not be loaded.'
  } finally {
    listingLoading.value = false
  }
}

function normalizeName(name: string): string {
  return name.trim().replace(/\s+/g, ' ').toLocaleLowerCase()
}

function dateKey(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

function getInitials(name: string): string {
  return name
    .trim()
    .split(/[\s_]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0))
    .join('')
    .toLocaleUpperCase()
}

onMounted(loadBusiness)
</script>
