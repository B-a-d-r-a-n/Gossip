<template>
    <div>
        <div class="flex items-center justify-between my-1">
            <h4 class="font-semibold me-2 hidden md:block">Members</h4>
            <template v-if="myRole === 'admin'">
            <InviteDialog :channelId="channelId" :open="inviteOpen" @update:open="inviteOpen = $event" />
            </template>
        </div>
        
        <div v-for="member in members" :key="member.user_id" class="py-3 border-b border-border first:border-t hover:bg-muted px-2">
            <div class="flex justify-between items-center">
                <div class="flex items-center gap-2">
                    <span class="font-medium">{{ member.username }}</span>
                    <Badge :variant="member.role === 'admin' ? 'destructive' : 'default'">{{ member.role }}</Badge>
                </div>
                <div v-if="isCurrentUser(member.user_id)" class="flex gap-1">
                    <Button variant="ghost" size="sm" @click="leaveChannel">
                        <LogOut class="h-4 w-4" />
                    </Button>
                </div>
                <div v-else-if="myRole === 'admin' && member.role !== 'admin'" class="flex gap-1">
                    <Button variant="ghost" size="sm" @click="promoteMember(member.user_id)">
                        <ArrowUp class="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" @click="kickMember(member.user_id)">
                        <Ban class="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>

    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, toRef } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useChannelStore } from '@/stores/channel'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { toast } from 'vue-sonner'
import { ArrowUp, Ban, Link as LinkIcon, LogOut } from 'lucide-vue-next'
import InviteDialog from './InviteDialog.vue'

interface ChannelMember {
    user_id: string
    username: string
    role: string
}

const props = defineProps<{ channelId: string; triggerKey?: number }>()
const emit = defineEmits<{
    (e: 'leave'): void
}>()
const authStore = useAuthStore()
const channelStore = useChannelStore()
const router = useRouter()
const members = ref<ChannelMember[]>([])
const inviteOpen = ref(false)
const myRole = ref<string | null>(null)
const triggerValue = toRef(props, 'triggerKey')
const leaving = ref(false)

function isCurrentUser(userId: string): boolean {
    return authStore.getUserId() === userId
}

async function fetchMyRole() {
    try {
        const res = await api.get(`/channels/${props.channelId}/me`)
        myRole.value = res.data.role
        console.log(myRole.value && members.value);
        
    } catch {
        myRole.value = null
    }
}

function openInviteDialog() {
    inviteOpen.value = true
}

async function fetchMembers() {
    try {
        const res = await api.get(`/channels/${props.channelId}/members`)
        members.value = res.data
    } catch (error) {
        console.error('Failed to fetch members', error)
    }
}

async function promoteMember(userId: string) {
    try {
        await api.post(`/channels/${props.channelId}/members/${userId}/promote`)
        toast('Promoted')
        fetchMembers()
    } catch (error) {
        console.error('Failed to promote', error)
    }
}

async function kickMember(userId: string) {
    try {
        await api.post(`/channels/${props.channelId}/members/${userId}/kick`)
        toast('Kicked')
        fetchMembers()
    } catch (error) {
        console.error('Failed to kick', error)
    }
}

async function leaveChannel() {
    emit('leave')
    await channelStore.leaveChannel(props.channelId)
    toast('Left channel')
}

onMounted(() => {
    fetchMembers()
    fetchMyRole()
})

watch(() => props.channelId, () => {
    members.value = []
    myRole.value = null
    fetchMembers()
    fetchMyRole()
})

watch(() => triggerValue.value, () => {
    fetchMembers()
    fetchMyRole()
})
</script>