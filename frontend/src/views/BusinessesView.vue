<template>
  <section aria-labelledby="page-title">
    <div :inert="Boolean(verificationProgress)">
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
    <div v-if="verificationError" class="notice notice-error" role="alert">
      <span class="notice-icon" aria-hidden="true">!</span><span>{{ verificationError }}</span>
    </div>
    <div v-if="verificationMessage" class="notice notice-success" role="status">
      {{ verificationMessage }}
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
        <div
  v-else-if="filteredBusinesses.length"
  class="w-full overflow-x-auto rounded-xl border border-gray-200 bg-white"
>
  <table class="w-full border-collapse text-left text-sm">
    <thead>
      <tr class="border-b border-gray-200 bg-gray-50/80 text-xs font-semibold uppercase tracking-wider text-gray-500">
        <th scope="col" class="px-4 py-3 whitespace-nowrap">Business</th>
        <th scope="col" class="px-4 py-3 whitespace-nowrap">Location</th>
        <th scope="col" class="px-4 py-3 whitespace-nowrap">Verification</th>
        <th scope="col" class="px-4 py-3 text-right whitespace-nowrap">Actions</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      <tr
        v-for="business in filteredBusinesses"
        :key="business.id"
        class="transition-colors hover:bg-gray-50/70"
      >
        <!-- Business & Category -->
        <td class="px-4 py-3.5 align-middle">
          <div class="flex items-center gap-3">
            <span
              class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold text-gray-900"
              aria-hidden="true"
            >
              {{ getInitials(business.business_name) }}
            </span>
            <div class="flex min-w-0 flex-col">
              <span class="truncate font-semibold text-gray-900">
                {{ business.business_name }}
              </span>
              <span class="truncate text-xs text-gray-500">
                {{ business.category || 'Local business' }}
              </span>
            </div>
          </div>
        </td>

        <!-- Location -->
        <td class="px-4 py-3.5 align-middle whitespace-nowrap text-gray-600">
          {{ business.location || 'Malawi' }}
        </td>

        <!-- Verification Status -->
        <td class="px-4 py-3.5 align-middle whitespace-nowrap">
          <span
            class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium"
            :class="
              business.taxpayer_matches?.some((m) => m.status === 'pending')
                ? 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/20'
                : 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20'
            "
          >
            {{ verificationSummary(business) }}
          </span>
        </td>

        <!-- Actions -->
        <td class="px-4 py-3.5 text-right align-middle whitespace-nowrap">
          <div class="inline-flex items-center justify-end gap-2">
            <button
              type="button"
              class="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:border-gray-400 hover:bg-gray-50"
              @click="()=>{}"
            >
              View
            </button>

            <button
              type="button"
              class="rounded-lg bg-gray-300 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-gray-400 disabled:cursor-not-allowed disabled:opacity-50"
              :disabled="verifyingBusinessId !== null || reviewingMatchId !== null"
              @click="verifyBusiness(business.id)"
            >
              {{ verificationButtonLabel(business) }}
            </button>

            <a
              v-if="business.profile_url"
              class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 text-gray-500 transition hover:bg-gray-50 hover:text-gray-900"
              :href="business.profile_url"
              target="_blank"
              rel="noopener noreferrer"
              :aria-label="`Open ${business.business_name} profile`"
              title="External profile"
            >
              <svg
                class="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.75"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M7 17 17 7M8 7h9v9" />
              </svg>
            </a>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</div>
        <div v-else class="empty-state">{{ searchQuery ? `No businesses match “${searchQuery}”. Try another search.` : 'No businesses have been collected yet.' }}</div>
        <p v-if="hasLoaded && businesses.length" class="results-note">
          Showing all {{ businesses.length }} businesses in your local directory.
        </p>
      </div>
    </section>
    </div>

  <div
    v-if="verificationProgress"
    class="verification-modal-backdrop"
    @click.self="closeVerificationModal"
    @keydown.esc.stop.prevent="closeVerificationModal"
  >
    <section
      ref="verificationModalElement"
      class="verification-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="verification-modal-title"
      aria-describedby="verification-modal-status"
      :aria-busy="isVerificationInProgress"
      tabindex="-1"
    >
      <p class="section-kicker">TAXPAYER VERIFICATION</p>
      <h2 id="verification-modal-title">
        Verify {{ verificationProgress.businessName }}
      </h2>
      <ol
        class="scrape-progress verification-progress"
        aria-label="Verification progress"
      >
        <li
          v-for="(step, index) in verificationSteps"
          :key="step"
          class="scrape-progress-step"
          :class="verificationStepClass(index)"
        >
          <span class="scrape-progress-indicator" aria-hidden="true">
            <svg
              v-if="verificationStepClass(index) === 'is-complete'"
              viewBox="0 0 24 24"
            ><path d="m5 12 4 4L19 6" /></svg>
            <span
              v-else-if="verificationStepClass(index) === 'is-active'"
              class="progress-spinner"
            ></span>
            <span
              v-else-if="verificationStepClass(index) === 'is-failed'"
              class="progress-failure"
            >!</span>
            <span v-else class="progress-pending"></span>
          </span>
          <span>{{ step }}</span>
        </li>
      </ol>
      <p
        id="verification-modal-status"
        class="verification-modal-status"
        :class="`is-${verificationProgress.stage}`"
        role="status"
        aria-live="polite"
      >
        {{ verificationProgressMessage }}
      </p>
      <p
        v-if="verificationProgress.error"
        class="verification-modal-error"
        role="alert"
      >
        {{ verificationProgress.error }}
      </p>
      <button
        v-if="!isVerificationInProgress"
        class="button button-primary verification-modal-close"
        type="button"
        @click="closeVerificationModal"
      >
        Close
      </button>
    </section>
  </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import axios from 'axios'
import api, { type ApiErrorDetail, type BusinessLead } from '../services/api'

type VerificationStage =
  | 'connecting'
  | 'querying'
  | 'completed'
  | 'connection-error'
  | 'query-error'
  | 'configuration-error'
  | 'request-error'

interface VerificationProgress {
  businessName: string
  stage: VerificationStage
  error: string | null
}

const businesses = ref<BusinessLead[]>([])
const loading = ref(true)
const hasLoaded = ref(false)
const error = ref<string | null>(null)
const verificationError = ref<string | null>(null)
const verificationMessage = ref<string | null>(null)
const verifyingBusinessId = ref<number | null>(null)
const verificationProgress = ref<VerificationProgress | null>(null)
const verificationModalElement = ref<HTMLElement | null>(null)
const reviewingMatchId = ref<number | null>(null)
const searchQuery = ref('')
const verificationSteps = [
  'Connect to the taxpayer database',
  'Query taxpayer records',
]
const isVerificationInProgress = computed(() =>
  verificationProgress.value?.stage === 'connecting'
  || verificationProgress.value?.stage === 'querying',
)
const verificationProgressMessage = computed(() => {
  switch (verificationProgress.value?.stage) {
    case 'connecting':
      return 'Checking the connection to the taxpayer database…'
    case 'querying':
      return 'Connection confirmed. Searching for matching taxpayer records…'
    case 'completed':
      return 'Verification completed. Results have been updated.'
    case 'connection-error':
      return 'The connection was not established, so no taxpayer query was run.'
    case 'query-error':
      return 'Connection confirmed. The taxpayer lookup did not complete.'
    case 'configuration-error':
      return 'The taxpayer database is not configured.'
    case 'request-error':
      return 'The backend did not return a result. The database status is unknown.'
    default:
      return ''
  }
})
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
    console.error('Failed to load local businesses from FastAPI.', cause)
    error.value = 'We could not load local businesses. Check your connection and try again.'
  } finally {
    loading.value = false
  }
}

async function verifyBusiness(businessId: number) {
  verifyingBusinessId.value = businessId
  verificationError.value = null
  verificationMessage.value = null
  const business = businesses.value.find(({ id }) => id === businessId)
  verificationProgress.value = {
    businessName: business?.business_name ?? 'business',
    stage: 'connecting',
    error: null,
  }
  await nextTick()
  verificationModalElement.value?.focus()
  try {
    try {
      await api.get('/taxpayer-database/connection/')
    } catch (cause) {
      setVerificationFailure(cause)
      return
    }

    updateVerificationProgress({ stage: 'querying' })
    const response = await api.post<BusinessLead>(`/businesses/${businessId}/verify/`)
    updateBusiness(response.data)
    verificationMessage.value = 'Taxpayer verification is up to date.'
    updateVerificationProgress({ stage: 'completed' })
  } catch (cause) {
    console.error(
      'Failed to verify a business against the taxpayer database.',
      cause,
    )
    setVerificationFailure(cause)
  } finally {
    verifyingBusinessId.value = null
  }
}

function setVerificationFailure(cause: unknown) {
  const progress = verificationProgress.value
  if (!progress) return

  const detail = getApiErrorDetail(cause)
  const stage: VerificationStage =
    detail?.code === 'taxpayer_connection_error'
      ? 'connection-error'
      : detail?.code === 'taxpayer_query_error'
        ? 'query-error'
        : detail?.code === 'taxpayer_database_not_configured'
          ? 'configuration-error'
          : 'request-error'
  const isApiError = axios.isAxiosError(cause)
  const requestTimedOut =
    isApiError
    && (cause.code === 'ECONNABORTED' || cause.code === 'ETIMEDOUT')

  const error = detail?.message
    || (requestTimedOut
        ? 'The backend request timed out. The database status is unknown.'
        : isApiError && !cause.response
          ? 'The backend API could not be reached.'
          : 'The backend could not complete taxpayer verification.')

  verificationProgress.value = {
    ...progress,
    stage,
    error,
  }
}

function updateVerificationProgress(updates: Partial<VerificationProgress>) {
  const progress = verificationProgress.value
  if (progress) verificationProgress.value = { ...progress, ...updates }
}

function getApiErrorDetail(
  cause: unknown,
): (ApiErrorDetail & { message?: string }) | null {
  if (!axios.isAxiosError<{ detail?: ApiErrorDetail | string }>(cause)) {
    return null
  }
  const detail = cause.response?.data?.detail
  if (typeof detail === 'string') return { message: detail }
  return detail && typeof detail === 'object' ? detail : null
}

function verificationStepClass(index: number): string {
  switch (verificationProgress.value?.stage) {
    case 'connecting':
      return index === 0 ? 'is-active' : ''
    case 'querying':
      return index === 0 ? 'is-complete' : 'is-active'
    case 'completed':
      return 'is-complete'
    case 'connection-error':
      return index === 0 ? 'is-failed' : ''
    case 'query-error':
      return index === 0 ? 'is-complete' : 'is-failed'
    default:
      return ''
  }
}

function closeVerificationModal() {
  if (!isVerificationInProgress.value) verificationProgress.value = null
}

async function reviewMatch(
  businessId: number,
  matchId: number,
  decision: 'approve' | 'reject',
) {
  reviewingMatchId.value = matchId
  verificationError.value = null
  verificationMessage.value = null
  try {
    const response = await api.post<BusinessLead>(
      `/businesses/${businessId}/matches/${matchId}/${decision}/`,
    )
    updateBusiness(response.data)
    verificationMessage.value =
      decision === 'approve'
        ? 'Taxpayer match approved and TIN saved.'
        : 'Taxpayer candidate rejected.'
  } catch (cause) {
    console.error(`Failed to ${decision} a taxpayer match.`, cause)
    verificationError.value =
      'We could not update this taxpayer review. Refresh the page and try again.'
  } finally {
    reviewingMatchId.value = null
  }
}

function updateBusiness(updatedBusiness: BusinessLead) {
  const index = businesses.value.findIndex(({ id }) => id === updatedBusiness.id)
  if (index >= 0) businesses.value[index] = updatedBusiness
}

function verificationSummary(business: BusinessLead): string {
  if (business.matched_tin) return `Approved TIN: ${business.matched_tin}`
  const pendingCount = business.taxpayer_matches.filter(
    (match) => match.status === 'pending',
  ).length
  if (pendingCount) {
    return `${pendingCount} possible match${pendingCount === 1 ? '' : 'es'} to review`
  }
  if (!business.is_checked) return 'Not verified yet'
  if (business.taxpayer_matches.length) return 'No candidate approved'
  return 'No matching taxpayer found'
}

function verificationButtonLabel(business: BusinessLead): string {
  if (verifyingBusinessId.value === business.id) return 'Checking…'
  return business.is_checked ? 'Recheck' : 'Verify'
}

function getInitials(name: string): string {
  return name
  .trim()
  .split(/[\s_]+/)
  .filter(Boolean)
  .map((part) => part.charAt(0))
  .join('')
  .toLocaleUpperCase();

}

onMounted(loadBusinesses)
</script>
