<template>
    <div class="h-full overflow-y-auto p-4" ref="feedRef" @scroll="onScroll">
        <div v-if="nextCursor" class="text-center p-2">
            <Button variant="ghost" @click="loadMore" :disabled="loading">
                <span v-if="loading">Loading...</span>
                <span v-else>Load more</span>
            </Button>
        </div>
        <div v-for="msg in messages" :key="msg.id" class="mb-4 p-3 rounded-lg bg-muted">
            <div class="flex flex-wrap items-center gap-1 sm:gap-2 mb-1">
                <span class="font-bold">{{ msg.username || msg.user_id }}</span>
                <Badge v-if="msg.role === 'admin'" variant="destructive" class="text-xs">admin</Badge>
                <Badge v-else variant="outline" class="text-xs">member</Badge>
                <span class="text-sm text-muted-foreground">{{ formatTime(msg.created_at) }}</span>
                <Badge v-if="msg.sentiment_label" variant="secondary"
                    class="ml-2">{{ msg.sentiment_label }} ({{ msg.sentiment_score?.toFixed(2) ?? '?' }})</Badge>
                <Badge v-if="msg.sentiment_status === 'pending'" variant="outline" class="ml-2">Analyzing...</Badge>
                <Badge v-if="msg.sentiment_status === 'failed'" variant="destructive" class="ml-2">Failed</Badge>
            </div>
            <div class="whitespace-pre-wrap break-words">{{ msg.content }}</div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { Message, SentimentUpdate } from '@/types'

const props = defineProps<{ channelId: string; newMessage?: Message; sentimentUpdate?: SentimentUpdate }>()
const messages = ref<Message[]>([])
const nextCursor = ref<string | null>(null)
const loading = ref(false)
const feedRef = ref<HTMLElement>()
const atTop = ref(true)

async function fetchMessages(cursor?: string) {
    loading.value = true
    try {
        const res = await api.get(`/chat/${props.channelId}/messages`, {
            params: cursor ? { cursor } : {}
        })
        const newMessages = res.data.messages.reverse()
        if (cursor) {
            messages.value = [...newMessages, ...messages.value]
        } else {
            messages.value = newMessages
        }
        nextCursor.value = res.data.next_cursor
        atTop.value = !nextCursor.value
        await nextTick()
        if (!cursor) {
            scrollToBottom()
        }
    } catch (error) {
        console.error('Failed to fetch messages', error)
    } finally {
        loading.value = false
    }
}

function loadMore() {
    if (nextCursor.value) {
        fetchMessages(nextCursor.value)
    }
}

function onScroll() {
    if (feedRef.value && feedRef.value.scrollTop < 100 && nextCursor.value && !loading.value) {
        loadMore()
    }
}

function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString()
}

function scrollToBottom() {
    if (feedRef.value) {
        feedRef.value.scrollTop = feedRef.value.scrollHeight
    }
}

onMounted(() => fetchMessages())

watch(() => props.channelId, () => {
    messages.value = []
    nextCursor.value = null
    fetchMessages()
})

// Accept single incoming live message via `newMessage` prop and append
watch(
    () => props.newMessage,
    (m) => {
        if (!m) return
        if (!messages.value.find((x) => x.id === m.id)) {
            messages.value = [...messages.value, m]
            nextTick(() => scrollToBottom())
        }
    }
)

// Accept sentiment updates and update the matching message
watch(
    () => props.sentimentUpdate,
    (update) => {
        if (!update) return
        const msg = messages.value.find((x) => x.id === update.id)
        if (msg) {
            msg.sentiment_label = update.sentiment_label
            msg.sentiment_score = update.sentiment_score
            msg.sentiment_status = update.sentiment_status
            messages.value = [...messages.value]
        }
    }
)
</script>