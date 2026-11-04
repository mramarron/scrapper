<template>
  <section aria-labelledby="page-title">
    <div class="page-heading">
      <div>
        <p class="eyebrow"><span class="eyebrow-line"></span> WORKSPACE</p>
        <h1 id="page-title">Settings <span>&amp; tools.</span></h1>
        <p class="page-description">Manage data collection for your business directory.</p>
      </div>
    </div>

    <div v-if="pageError" class="notice notice-error" role="alert">
      <span class="notice-icon" aria-hidden="true">!</span>
      <span>{{ pageError }}</span>
      <button class="notice-action" type="button" @click="loadLatestRun">Try again</button>
    </div>

    <section class="settings-card" aria-labelledby="scraper-title">
      <div class="settings-card-heading">
        <span class="settings-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path d="M4 19.5h16M6 16V9m4 7V5m4 11v-4m4 4V7" /></svg>
        </span>
        <div>
          <p class="section-kicker">DATA COLLECTION</p>
          <h2 id="scraper-title">Mthandizi business scraper</h2>
        </div>
      </div>

      <p class="settings-description">
        Collect the latest business profiles and featured products from Mthandizi.
        New records will be available in the Businesses and Marketplace pages.
      </p>

      <button
        class="button button-primary refresh-button"
        type="button"
        :disabled="starting || isRunning || checkingStatus"
        @click="startScrape"
      >
        <svg v-if="starting || isRunning" class="is-spinning" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8 8 0 0 0-14.7-3L4 10m0 0V5m0 5h5m-5 2a8 8 0 0 0 14.7 3L20 14m0 0v5m0-5h-5" /></svg>
        <svg v-else-if="displayStatus === 'completed'" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg>
        <svg v-else viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14m-7-7h14" /></svg>
        {{ starting ? 'Starting scraper…' : isRunning ? 'Scraper running…' : 'Run scraper' }}
      </button>

      <div v-if="checkingStatus" class="scrape-status" role="status">
        <span class="spinner"></span>
        Checking scraper status…
      </div>
      <div v-else-if="run" class="scrape-status" :class="`scrape-status-${displayStatus}`" aria-live="polite">
        <span v-if="displayStatus === 'queued' || displayStatus === 'running'" class="spinner" aria-hidden="true"></span>
        <svg v-else-if="run.status === 'completed'" class="status-check" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg>
        <span v-else-if="run.status === 'failed'" class="status-failure" aria-hidden="true">!</span>
        <span v-else class="status-dot" aria-hidden="true"></span>
        <div class="scrape-status-copy">
          <strong>{{ statusTitle }}</strong>
          <span>{{ statusDescription }}</span>
        </div>
      </div>

      <ol v-if="showProgressSteps" class="scrape-progress" aria-label="Scraper progress">
        <li
          v-for="(step, index) in progressSteps"
          :key="step"
          class="scrape-progress-step"
          :class="progressStepClass(index)"
        >
          <span class="scrape-progress-indicator" aria-hidden="true">
            <svg v-if="progressStepClass(index) === 'is-complete'" viewBox="0 0 24 24"><path d="m5 12 4 4L19 6" /></svg>
            <span v-else-if="progressStepClass(index) === 'is-active'" class="progress-spinner"></span>
            <span v-else-if="progressStepClass(index) === 'is-failed'" class="progress-failure">!</span>
            <span v-else class="progress-pending"></span>
          </span>
          <span>{{ step }}</span>
        </li>
      </ol>
      <p
        v-if="run?.progress?.stage === 'processing_businesses' && run.progress.total"
        class="scrape-progress-count"
      >
        Business {{ run.progress.current }} of {{ run.progress.total }}
        <span v-if="run.progress.businesses_processed !== undefined">
          · {{ run.progress.businesses_processed }} processed
        </span>
        <span v-if="run.progress.products_processed !== undefined">
          · {{ run.progress.products_processed }} products
        </span>
        <span v-if="run.progress.products_added">
          · {{ run.progress.products_added }} new
        </span>
      </p>

      <div v-if="run?.status === 'failed'" class="scrape-error" role="alert">
        <strong>{{ errorTitle }}</strong>
        <span>{{ errorMessage }}</span>
      </div>
      <pre v-if="displayStatus === 'completed' && run?.output" class="scrape-output">{{ run.output }}</pre>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import api, { type ScrapeRun } from '../services/api'

const run = ref<ScrapeRun | null>(null)
const starting = ref(false)
const checkingStatus = ref(true)
const pageError = ref<string | null>(null)
const progressSteps = [
  'Starting scraper services',
  'Loading the Mthandizi business directory',
  'Processing profiles and featured products',
]
let pollTimer: ReturnType<typeof setTimeout> | undefined

const isRunning = computed(() => run.value?.status === 'queued' || run.value?.status === 'running')
const displayStatus = computed(() => run.value?.status)
const errorTitles: Record<NonNullable<ScrapeRun['error_code']>, string> = {
  upstream_timeout: 'Connection timed out',
  upstream_unreachable: 'Mthandizi unavailable',
  upstream_rate_limited: 'Request limit reached',
  upstream_access_denied: 'Access temporarily denied',
  upstream_server_error: 'Mthandizi service problem',
  upstream_request_failed: 'Could not load Mthandizi page',
  directory_empty: 'No business profiles found',
  storage_error: 'Could not save scraper results',
  worker_unavailable: 'Scraper could not start',
  unexpected_error: 'Unexpected scraper error',
  '': 'Scrape failed',
}
const errorTitle = computed(() => {
  const code = run.value?.error_code ?? ''
  return errorTitles[code] || 'Scrape failed'
})
const errorMessage = computed(() => {
  const message = run.value?.error
  if (
    !message
    || message === 'The scraper failed. Check the Django server logs for details.'
  ) {
    return 'An unexpected error interrupted the scrape. Please try again later.'
  }
  return message
})
const showProgressSteps = computed(() =>
  run.value?.status === 'queued'
  || run.value?.status === 'running'
  || run.value?.status === 'failed'
  || run.value?.status === 'completed',
)
const activeProgressStep = computed(() => {
  const stage = run.value?.progress?.stage
  if (stage === 'starting') return 0
  if (stage === 'loading_directory') return 1
  if (stage === 'processing_businesses') return 2
  return -1
})
const statusTitle = computed(() => {
  if (displayStatus.value === 'queued') return 'Scraper queued'
  if (displayStatus.value === 'running') return 'Scraper is running'
  if (displayStatus.value === 'completed') return 'Scrape completed'
  return 'Scrape failed'
})
const statusDescription = computed(() => {
  const currentRun = run.value
  if (!currentRun) return ''
  if (displayStatus.value === 'queued') return 'The scraper will start shortly.'
  if (displayStatus.value === 'running') {
    return currentRun.progress?.message || 'The scraper is running.'
  }
  if (displayStatus.value === 'completed') {
    return currentRun.completed_at
      ? `Finished ${new Intl.DateTimeFormat('en-MW', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(currentRun.completed_at))}.`
      : 'The latest Mthandizi data is ready.'
  }
  return 'The scraper did not finish successfully.'
})

async function loadLatestRun() {
  checkingStatus.value = true
  pageError.value = null
  try {
    const response = await api.get<{ run: ScrapeRun | null }>('/scrape-mthandizi/')
    run.value = response.data.run
    if (run.value && isRunning.value) scheduleStatusCheck(run.value.id)
  } catch (cause) {
    console.error('Failed to load the Mthandizi scraper status.', cause)
    pageError.value = 'We could not load scraper status. Check your connection and try again.'
  } finally {
    checkingStatus.value = false
  }
}

async function startScrape() {
  starting.value = true
  pageError.value = null
  try {
    const response = await api.post<ScrapeRun>('/scrape-mthandizi/')
    run.value = response.data
    if (isRunning.value) scheduleStatusCheck(response.data.id)
  } catch (cause) {
    console.error('Failed to start the Mthandizi scraper.', cause)
    pageError.value = 'We could not start the scraper. Check your connection and try again.'
  } finally {
    starting.value = false
  }
}

function scheduleStatusCheck(runId: string) {
  if (pollTimer) clearTimeout(pollTimer)
  pollTimer = setTimeout(() => {
    void refreshStatus(runId)
  }, 1500)
}

function progressStepClass(index: number) {
  if (run.value?.status === 'completed') return 'is-complete'
  if (run.value?.status === 'failed' && activeProgressStep.value >= 0) {
    if (index < activeProgressStep.value) return 'is-complete'
    if (index === activeProgressStep.value) return 'is-failed'
    return 'is-pending'
  }
  if (index < activeProgressStep.value) return 'is-complete'
  if (index === activeProgressStep.value) return 'is-active'
  return 'is-pending'
}

async function refreshStatus(runId: string) {
  try {
    const response = await api.get<ScrapeRun>(`/scrape-mthandizi/${runId}/`)
    run.value = response.data
    pageError.value = null
    if (isRunning.value) scheduleStatusCheck(runId)
  } catch (cause) {
    console.error('Failed to refresh the Mthandizi scraper status.', cause)
    pageError.value = 'We temporarily lost the scraper status connection. Retrying…'
    scheduleStatusCheck(runId)
  }
}

onMounted(loadLatestRun)
onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
})
</script>
