<template>
  <div class="app-container">
    <h1>Django + Vue Decoupled App</h1>
    
    <div v-if="loading" class="status">Fetching data from backend...</div>
    <div v-else-if="error" class="status error">{{ error }}</div>
    
    <ul v-else class="item-list">
      <li v-for="item in items" :key="item.id">
        <strong>{{ item.title }}</strong>: {{ item.description }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from './services/api';

const items = ref([]);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    // Hits http://127.0.0 behind the scenes
    const response = await api.get('/items/'); 
    items.value = response.data;
  } catch (err) {
    error.value = 'Failed to load data from Django backend.';
    console.error(err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.app-container {
  font-family: Arial, sans-serif;
  max-width: 600px;
  margin: 40px auto;
  padding: 20px;
  border-radius: 8px;
  background-color: #f9f9f9;
}
.status { color: #666; }
.error { color: #d9534f; }
.item-list { list-style-type: none; padding: 0; }
.item-list li { padding: 10px; margin-bottom: 8px; background: #fff; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
</style>
