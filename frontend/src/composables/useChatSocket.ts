import { ref, onUnmounted } from 'vue'
import api from '@/services/api'
import { toast } from 'vue-sonner'
import type { Message } from '@/types'

interface SentimentUpdate {
    type: 'sentiment_update'
    id: string
    sentiment_label: string | null
    sentiment_score: number | null
    sentiment_status: string
}

interface MemberEvent {
    type: 'member_joined' | 'member_left' | 'member_kicked' | 'member_promoted'
    user_id: string
    role?: string
}

interface ChannelEvent {
    type: 'channel_created'
    id: string
    name: string
}

export interface KickedEvent {
    type: 'kicked'
    channel_id: string
    user_id: string
}

export function useChatSocket(channelIdGetter: () => string) {
    const socket = ref<WebSocket | null>(null);
    const messages = ref<Message[]>([]);
    const isConnected = ref(false);
    const sentimentUpdates = ref<SentimentUpdate[]>([]);
    const memberEvent = ref<MemberEvent | null>(null);
    const channelEvent = ref<ChannelEvent | null>(null);
    const kickedEvent = ref<KickedEvent | null>(null);
    const currentUserId = ref<string | null>(null);

    const connect = async () => {
        const channelId = channelIdGetter()

        try {
            const { data: userData } = await api.get('/auth/me')
            currentUserId.value = userData.id

            const { data } = await api.post('/chat/ws/ticket')
            const ticket: string = data.ticket

            const wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/chat/ws/chat/${channelId}?ticket=${ticket}`
            socket.value = new WebSocket(wsUrl)

            socket.value.onopen = () => {
                isConnected.value = true
            }

            socket.value.onmessage = (event) => {
                try {
                    const d = JSON.parse(event.data)
                    if (d.type === 'sentiment_update') {
                        sentimentUpdates.value.unshift(d)
                    } else if (['member_joined', 'member_left', 'member_kicked', 'member_promoted'].includes(d.type)) {
                        const memberEvt = d as MemberEvent
                        memberEvent.value = memberEvt
                        if (memberEvt.type === 'member_kicked' && memberEvt.user_id === currentUserId.value) {
                            kickedEvent.value = { type: 'kicked', channel_id: channelId, user_id: memberEvt.user_id }
                        }
                    } else if (d.type === 'channel_created') {
                        channelEvent.value = d as ChannelEvent
                    } else {
                        messages.value.unshift(d as Message)
                    }
                } catch (e) {
                    console.error('Invalid WS message', e)
                }
            }

            socket.value.onerror = () => {
                toast.warning('Connection lost')
            }

            socket.value.onclose = (event) => {
                isConnected.value = false
                if (event.code === 4003) {
                    kickedEvent.value = { type: 'kicked', channel_id: channelId, user_id: currentUserId.value || '' }
                }
            }
        } catch (error) {
            console.error('WebSocket connection failed', error)
            toast.error('Unable to connect to chat')
        }
    }

    const sendMessage = (content: string) => {
        if (socket.value && isConnected.value) {
            socket.value.send(JSON.stringify({ content }))
        }
    }

    onUnmounted(() => {
        socket.value?.close()
    })

    return { socket, messages, sentimentUpdates, memberEvent, channelEvent, kickedEvent, isConnected, connect, sendMessage }
}