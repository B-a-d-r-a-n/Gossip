<template>
    <div class="min-h-screen flex items-center justify-center p-4">
        <div class="text-center">
            <p v-if="loading">Joining channel...</p>
            <p v-else-if="error" class="text-destructive">{{ error }}</p>
            <p v-else>Joined! Redirecting...</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')

onMounted(async () => {
    const token = route.params.token as string
    
    try {
        const res = await api.post(`/channels/join/${token}`)
        router.push(`/channel/${res.data.channel_id}`)
    } catch (err: unknown) {
        const e = err as { response?: { data?: { code?: string, message?: string; channel_id?: string } } }
        if (e.response?.data?.code === 'ALREADY_MEMBER' && e.response?.data?.channel_id) {
            router.push(`/channel/${e.response.data.channel_id}`)
            return
        }
        error.value = e.response?.data?.message || 'Failed to join channel'
        loading.value = false
    }
})
</script>