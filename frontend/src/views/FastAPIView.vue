<script lang="ts" setup>
import {ref,onMounted} from 'vue'
import axios from 'axios'

const fastAPIData = ref<any>(null)
const loading = ref<boolean>(false)

async function fetchFastAPIData() {
  try {
    loading.value = true
    const response = await axios.get('http://localhost:8000/home')
    fastAPIData.value = response.data
  } catch (error) {
    console.error('Error fetching FastAPI data:', error)
  }
  finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchFastAPIData()
})
</script>

<template>
  <div class="fastapi-view">
    <h1>FastAPI Data</h1>
    <p v-if="!loading && fastAPIData">{{ fastAPIData.message }}</p>
    <p v-else-if="loading">Loading...</p>
    <p v-else>No data available</p>
  </div>
  </template>