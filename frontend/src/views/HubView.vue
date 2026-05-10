<template>
    <div class="h-full p-4 sm:p-6 lg:p-8">
        <div v-if="channelStore.userChannels.length === 0" class="text-center text-muted-foreground">
            <p class="text-lg mb-8">You're not in any channel</p>
            
            <div class="max-w-md mx-auto w-full px-0 sm:px-4">
                <h3 class="font-semibold mb-4">Join via Code</h3>
                <div class="flex flex-col sm:flex-row gap-2">
                    <Input v-model="inviteCode" placeholder="Enter invite code" class="flex-1" />
                    <Button @click="joinChannel" :disabled="!inviteCode.trim() || joining" class="w-full sm:w-auto">
                        <span v-if="joining">Joining...</span>
                        <span v-else>Join</span>
                    </Button>
                </div>
                <p v-if="joinError" class="text-destructive mt-2 text-sm">{{ joinError }}</p>
            </div>
        </div>
        
        <div v-else class="max-w-2xl mx-auto w-full px-0 sm:px-4">
            <h2 class="text-xl font-semibold mb-6">Your Channels</h2>
            <div class="space-y-2">
                <div v-for="channel in channelStore.userChannels" :key="channel.id"
                    class="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 border border-border rounded-lg bg-card hover:bg-accent cursor-pointer gap-2"
                    :class="{ 'border-primary bg-accent': isActiveChannel(channel.id) }"
                    @click="connectToChannel(channel)">
                    <span class="font-medium"># {{ channel.name }}</span>
                    <Button variant="ghost" size="sm">Connect</Button>
                </div>
            </div>
            
            <div class="mt-8 border-t border-border pt-8">
                <h3 class="font-semibold mb-4">Join via Code</h3>
                <div class="flex flex-col sm:flex-row gap-2">
                    <Input v-model="inviteCode" placeholder="Enter invite code" class="flex-1" />
                    <Button @click="joinChannel" :disabled="!inviteCode.trim() || joining" class="w-full sm:w-auto">
                        <span v-if="joining">Joining...</span>
                        <span v-else>Join</span>
                    </Button>
                </div>
                <p v-if="joinError" class="text-destructive mt-2 text-sm">{{ joinError }}</p>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
    import { ref, onMounted } from 'vue'
    import { useRouter, useRoute } from 'vue-router'
    import { useChannelStore } from '@/stores/channel'
    import { inviteTokenSchema } from '@/lib/schemas'
    import type { Channel } from '@/types'
    import { Button } from '@/components/ui/button'
    import { Input } from '@/components/ui/input'
    import { toast } from 'vue-sonner'

    const channelStore = useChannelStore()
    const router = useRouter()
    const route = useRoute()
    
    const inviteCode = ref('')
    const joining = ref(false)
    const joinError = ref('')

    onMounted(() => {
        channelStore.fetchUserChannels()
    })

    function connectToChannel(channel: Channel) {
        channelStore.setActiveChannel(channel)
        channelStore.setActiveChannelRole(channel.id)
        router.push(`/channel/${channel.id}`)
    }

    function isActiveChannel(channelId: string) {
        return channelStore.lastActiveChannelId === channelId
    }

    function extractToken(input: string) {
        const trimmed = input.trim()
        const urlMatch = trimmed.match(/\/join\/([a-f0-9-]+)/i)
        const token = urlMatch ? urlMatch[1] : trimmed
        
        const result = inviteTokenSchema.safeParse(token)
        return result.success ? result.data : ''
    }

    async function joinChannel() {
        if (!inviteCode.value.trim()) return
        
        joining.value = true
        joinError.value = ''
        
        try {
            const token = extractToken(inviteCode.value)
            await channelStore.joinChannelByCode(token as string)
            toast('Joined channel successfully')
            inviteCode.value = ''
        } catch (error: unknown) {
            const err = error as { response?: { data?: { detail?: string } } }
            joinError.value = err.response?.data?.detail || 'Failed to join channel'
        } finally {
            joining.value = false
        }
    }
</script>