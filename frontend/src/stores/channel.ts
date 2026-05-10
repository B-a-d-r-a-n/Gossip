import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Channel } from '@/types'

export const useChannelStore = defineStore('channel', () => {
    const channels = ref<Channel[]>([])
    const userChannels = ref<Channel[]>([])
    const activeChannel = ref<Channel | null>(null)
    const activeChannelRole = ref<string | null>(null)
    const lastActiveChannelId = ref<string | null>(null)

    async function fetchChannels() {
        const res = await api.get('/channels')
        channels.value = res.data
    }

    async function fetchUserChannels() {
        const res = await api.get('/channels/me')
        userChannels.value = res.data
    }

    async function createChannel(name: string, description?: string) {
        const res = await api.post('/channels', { name, description })
        channels.value.push(res.data)
        userChannels.value.push(res.data)
        return res.data
    }

    function setActiveChannel(channel: Channel) {
        activeChannel.value = channel
        lastActiveChannelId.value = channel.id
    }

    function setActiveChannelById(channelId: string) {
        lastActiveChannelId.value = channelId
    }

    async function setActiveChannelRole(channelId: string) {
        try {
            const res = await api.get(`/channels/${channelId}/me`)
            activeChannelRole.value = res.data.role
        } catch {
            activeChannelRole.value = null
        }
    }

    async function leaveChannel(channelId: string) {
        await api.post(`/channels/${channelId}/leave`)
        userChannels.value = userChannels.value.filter(c => c.id !== channelId)
        if (activeChannel.value?.id === channelId) {
            activeChannel.value = null
            activeChannelRole.value = null
            lastActiveChannelId.value = null
        }
    }

    async function joinChannelByCode(token: string) {
        const res = await api.post(`/channels/join/${token}`)
        await fetchUserChannels()
        return res.data
    }

    function clearActiveChannel() {
        activeChannel.value = null
        activeChannelRole.value = null
        lastActiveChannelId.value = null
    }

    function removeChannelFromList(channelId: string) {
        userChannels.value = userChannels.value.filter(c => c.id !== channelId)
        if (activeChannel.value?.id === channelId) {
            activeChannel.value = null
            activeChannelRole.value = null
            lastActiveChannelId.value = null
        }
    }

    return {
        channels,
        userChannels,
        activeChannel,
        activeChannelRole,
        lastActiveChannelId,
        fetchChannels,
        fetchUserChannels,
        createChannel,
        setActiveChannel,
        setActiveChannelById,
        setActiveChannelRole,
        leaveChannel,
        joinChannelByCode,
        clearActiveChannel,
        removeChannelFromList,
    }
})