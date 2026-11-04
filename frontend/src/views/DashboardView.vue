<template>
  <div>
    <section class="page-heading" aria-labelledby="page-title">
      <div>
        <p class="eyebrow"><span class="eyebrow-line"></span> MARKET INTELLIGENCE</p>
        <h1 id="page-title">Your directory, <span>at a glance.</span></h1>
        <p class="page-description">A clear view of the latest marketplace and local business data.</p>
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

    <section class="overview-grid" aria-label="Directory analytics">
      <article class="analytics-card activity-card">
        <div class="analytics-heading">
          <div>
            <p class="section-kicker">COLLECTION TRENDS</p>
            <h2>Records collected <span class="chart-period">Last 14 days</span></h2>
          </div>
          <span class="chart-legend"><span></span> Records</span>
        </div>
        <p v-if="loading && !hasLoaded" class="chart-message" role="status">Loading collection activity…</p>
        <p v-else-if="error && !hasLoaded" class="chart-message">Activity is unavailable until the directory connection is restored.</p>
        <div v-else-if="!hasChartData" class="chart-message">No recent collection activity to display.</div>
        <ChartContainer
          v-else
          :config="activityChartConfig"
          class="activity-chart-canvas"
          role="img"
          :aria-label="activityChartLabel"
        >
          <VisXYContainer :data="activity" :margin="{ top: 16, right: 6, bottom: 22, left: 6 }">
            <VisGroupedBar
              :x="activityX"
              :y="activityY"
              :color="[activityChartConfig.count.color]"
              :bar-padding="0.35"
              :rounded-corners="4"
            />
            <VisAxis
              type="x"
              :x="activityX"
              :tick-values="activity.map((day) => day.timestamp)"
              :tick-format="activityTickFormat"
              :tick-line="false"
              :domain-line="false"
              :grid-line="false"
            />
            <VisAxis
              type="y"
              :tick-format="() => ''"
              :tick-line="false"
              :domain-line="false"
              :grid-line="true"
            />
            <ChartTooltip />
            <ChartCrosshair
              :x="activityX"
              :y="activityY"
              :template="activityTooltipTemplate"
              :color="[activityChartConfig.count.color]"
            />
          </VisXYContainer>
        </ChartContainer>
        <p class="chart-footnote">Based on the latest records returned by each directory.</p>
      </article>

      <article class="analytics-card source-card">
        <div class="analytics-heading">
          <div>
            <p class="section-kicker">DATA SOURCES</p>
            <h2>Directory mix</h2>
          </div>
        </div>
        <p v-if="loading && !hasLoaded" class="chart-message source-chart-message" role="status">Loading directory mix…</p>
        <p v-else-if="error && !hasLoaded" class="chart-message source-chart-message">Directory mix is unavailable until the connection is restored.</p>
        <p v-else-if="!hasSourceData" class="chart-message source-chart-message">No source records to display.</p>
        <div v-else class="source-chart-content">
          <ChartContainer
            :config="sourceChartConfig"
            class="source-chart-canvas"
            role="img"
            :aria-label="sourceChartLabel"
          >
            <VisSingleContainer :data="sourceChartData" :height="136">
              <VisDonut
                :value="sourceValue"
                :color="sourceColor"
                :central-label="String(listings.length + businesses.length)"
                central-sub-label="records"
                :arc-width="20"
                :show-empty-segments="true"
              />
            </VisSingleContainer>
          </ChartContainer>
          <div class="source-breakdown" aria-label="Records by source">
            <div v-for="source in sourceChartData" :key="source.key" class="source-row-heading">
              <span><i class="source-dot" :style="{ backgroundColor: source.color }"></i>{{ source.label }}</span>
              <strong>{{ source.count }}</strong>
            </div>
          </div>
        </div>
        <p class="chart-footnote">Latest {{ listings.length + businesses.length }} records across both sources.</p>
      </article>
    </section>

    <section class="quick-links" aria-labelledby="explore-title">
      <div class="quick-links-heading">
        <div>
          <p class="section-kicker">EXPLORE YOUR DATA</p>
          <h2 id="explore-title">Go to a directory</h2>
        </div>
      </div>
      <div class="quick-link-grid">
        <RouterLink class="quick-link-card" to="/marketplace">
          <span class="quick-link-icon icon-mint"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7.5h16l-1.5 13h-13L4 7.5ZM8 8V6a4 4 0 0 1 8 0v2" /></svg></span>
          <span class="quick-link-copy"><strong>Marketplace listings</strong><small>Browse collected items and offers</small></span>
          <span class="quick-link-count">{{ listings.length }}</span>
          <span class="quick-link-arrow" aria-hidden="true">→</span>
        </RouterLink>
        <RouterLink class="quick-link-card" to="/businesses">
          <span class="quick-link-icon icon-lilac"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 20.5h17M5.5 20.5v-11l6.5-5 6.5 5v11M9 20.5v-5h6v5M9 11h.01M15 11h.01" /></svg></span>
          <span class="quick-link-copy"><strong>Local businesses</strong><small>Discover businesses in the directory</small></span>
          <span class="quick-link-count">{{ businesses.length }}</span>
          <span class="quick-link-arrow" aria-hidden="true">→</span>
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { VisAxis, VisDonut, VisGroupedBar, VisSingleContainer, VisXYContainer } from '@unovis/vue'
import type { ChartConfig } from '@/components/ui/chart'
import {
  ChartContainer,
  ChartCrosshair,
  ChartTooltip,
  ChartTooltipContent,
  componentToString,
} from '@/components/ui/chart'
import api, { type BusinessLead, type ScrapedListing } from '../services/api'

interface ActivityDay {
  key: string
  dateLabel: string
  timestamp: number
  count: number
}

interface SourceSlice {
  key: 'marketplace' | 'businesses'
  label: string
  count: number
  color: string
}

const activityChartConfig = {
  count: {
    label: 'Records',
    color: '#56a176',
  },
} satisfies ChartConfig

const sourceChartConfig = {
  marketplace: {
    label: 'Marketplace',
    color: '#56a176',
  },
  businesses: {
    label: 'Businesses',
    color: '#9482bd',
  },
} satisfies ChartConfig

const listings = ref<ScrapedListing[]>([])
const businesses = ref<BusinessLead[]>([])
const loading = ref(true)
const hasLoaded = ref(false)
const error = ref<string | null>(null)

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

const activity = computed<ActivityDay[]>(() => {
  const today = new Date()
  const days = Array.from({ length: 14 }, (_, index) => {
    const date = new Date(today)
    date.setHours(0, 0, 0, 0)
    date.setDate(today.getDate() - (13 - index))
    return {
      key: dateKey(date),
      dateLabel: new Intl.DateTimeFormat('en-MW', { day: 'numeric', month: 'short' }).format(date),
      timestamp: date.getTime(),
      count: 0,
    }
  })
  const counts = new Map(days.map((day) => [day.key, day]))

  for (const timestamp of [
    ...listings.value.map((listing) => listing.scraped_at),
    ...businesses.value.map((business) => business.scraped_at),
  ]) {
    const date = new Date(timestamp)
    if (Number.isNaN(date.getTime())) continue
    const day = counts.get(dateKey(date))
    if (day) day.count += 1
  }

  return days
})

const hasChartData = computed(() => activity.value.some((day) => day.count > 0))
const activityChartLabel = computed(() =>
  `Records collected over the last fourteen days: ${activity.value.map((day) => `${day.dateLabel}, ${day.count}`).join('; ')}`,
)
const sourceChartData = computed<SourceSlice[]>(() => [
  {
    key: 'marketplace',
    label: 'Marketplace',
    count: listings.value.length,
    color: sourceChartConfig.marketplace.color,
  },
  {
    key: 'businesses',
    label: 'Businesses',
    count: businesses.value.length,
    color: sourceChartConfig.businesses.color,
  },
])
const hasSourceData = computed(() => sourceChartData.value.some((source) => source.count > 0))
const sourceChartLabel = computed(() =>
  `Directory mix: ${sourceChartData.value.map((source) => `${source.label}, ${source.count}`).join('; ')}`,
)
const activityTooltipTemplate = componentToString(activityChartConfig, ChartTooltipContent, {
  labelFormatter: (timestamp) =>
    new Intl.DateTimeFormat('en-MW', { day: 'numeric', month: 'short' }).format(
      timestamp instanceof Date ? timestamp : new Date(timestamp),
    ),
})

const activityX = (day: ActivityDay) => day.timestamp
const activityY = (day: ActivityDay) => day.count
const activityTickFormat = (timestamp: number) => String(new Date(timestamp).getDate())
const sourceValue = (source: SourceSlice) => source.count
const sourceColor = (source: SourceSlice) => source.color

function dateKey(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

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
    console.error('Failed to load directory overview from Django.', cause)
    error.value = 'We could not load the latest directory data. Check your connection and try again.'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
