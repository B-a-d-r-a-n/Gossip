<template>
    <div class="h-full flex">
        <main class="flex-1 flex flex-col min-h-0">
            <header class="p-4 border-b border-border flex items-center gap-2">
                <Button variant="ghost" size="icon" class="md:hidden" @click="memberPanelOpen = true">
                    <Users class="h-5 w-5" />
                </Button>
                <h3 class="m-0">{{ channel?.name ?? (`loading...`) }}</h3>
            </header>

            <section class="flex-1 min-h-0 flex flex-col">
                <MessageFeed :channelId="channelId" :newMessage="latestMessage" :sentimentUpdate="latestSentimentUpdate" />
            </section>

            <footer>
                <ChatInput @send="onSend" />
            </footer>
        </main>

        <!-- Desktop Member List -->
        <aside class="hidden md:flex w-fit border-l border-border p-2 shrink-0">
            <MemberList :channelId="channelId" :triggerKey="memberListKey" @leave="onLeaveChannel" />
        </aside>

        <!-- Mobile Member Panel Overlay -->
        <div v-if="memberPanelOpen" class="fixed inset-0 z-50 md:hidden" @click.self="memberPanelOpen = false">
            <div class="fixed inset-0 bg-black/50" @click="memberPanelOpen = false" />
            <div class="fixed inset-y-0 right-0 w-[320px] bg-card border-l border-border shadow-xl flex flex-col">
                <div class="flex items-center justify-between p-4 border-b border-border">
                    <h4 class="font-semibold m-0">Members</h4>
                    <Button variant="ghost" size="icon" @click="memberPanelOpen = false">
                        <X class="h-5 w-5" />
                    </Button>
                </div>
                <div class="flex-1 overflow-y-auto p-2">
                    <MemberList :channelId="channelId" :triggerKey="memberListKey" @leave="onLeaveChannel" />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import type { Channel, Message, SentimentUpdate } from '@/types'
import MessageFeed from '@/components/chat/MessageFeed.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import MemberList from '@/components/channel/MemberList.vue'
import { Button } from '@/components/ui/button'
import { useChatSocket } from '@/composables/useChatSocket'
import { useChannelStore } from '@/stores/channel'
import { toast } from 'vue-sonner'
import { Users, X } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const channelId = computed(() => String(route.params.id || ''))
const channelStore = useChannelStore()
const memberPanelOpen = ref(false)
let exitingChannel = false

const latestMessage = ref<Message | undefined>(undefined)
const latestSentimentUpdate = ref<SentimentUpdate | undefined>(undefined)
const channel = ref<Channel | null>(null)
const memberListKey = ref(0)

const socket = useChatSocket(() => channelId.value)

onMounted(async () => {
    await socket.connect()
    channelStore.setActiveChannelById(channelId.value)

    try {
        const res = await api.get(`/channels/${channelId.value}`)
        channel.value = res.data
    } catch {
        // ignore if endpoint missing
    }
})

const sendMessage = socket.sendMessage
const isConnected = socket.isConnected

// Forward newest socket message into the MessageFeed via prop
watch(socket.messages, (msgs) => {
    if (msgs && msgs.length) {
        latestMessage.value = msgs[0]
    }
}, { deep: true })

// Forward sentiment updates into the MessageFeed via prop
watch(socket.sentimentUpdates, (updates) => {
    if (updates && updates.length) {
        latestSentimentUpdate.value = updates[0]
    }
}, { deep: true })

// Handle member events - refresh member list
watch(socket.memberEvent, (event) => {
    if (event) {
        memberListKey.value++
    }
})

// Handle kicked event - redirect to hub
watch(socket.kickedEvent, (event) => {
    if (event && !exitingChannel) {
        channelStore.removeChannelFromList(event.channel_id)
        channelStore.clearActiveChannel()
        toast.warning('You have been kicked from the channel')
        router.push('/hub')
    }
})

function onLeaveChannel() {
    exitingChannel = true
    channelStore.clearActiveChannel()
    router.push('/hub')
}

function onSend(content: string) {
    if (isConnected.value) {
        sendMessage(content)
    } else {
        toast.error('Unable to send message')
    }
}
</script>