<template>
    <!-- 1. The Trigger Button -->
    <Button class="w-full md:w-auto" variant="outline" @click="open = true">
        <LinkIcon class="h-4 w-4 mr-2" />
        Generate Invite
    </Button>

    <!-- 2. The Dialog -->
    <Dialog :open="open" @update:open="open = $event">
        <DialogContent class="sm:max-w-md">
            <DialogHeader>
                <DialogTitle>Generate Invite Link</DialogTitle>
            </DialogHeader>

            <div class="space-y-4 py-4">
                <div class="space-y-2">
                    <label class="text-sm font-medium">Expires in (minutes)</label>
                    <NumberField v-model="expiresIn" :min="1" :max="168" class="w-full">
                        <NumberFieldContent>
                            <NumberFieldDecrement />
                            <NumberFieldInput />
                            <NumberFieldIncrement />
                        </NumberFieldContent>
                    </NumberField>
                </div>

                <div v-if="inviteToken" class="space-y-2">
                    <label class="text-sm font-medium">Invite Link:</label>
                    <div class="flex items-center gap-2">
                        <Input :model-value="inviteUrl" readonly class="flex-1" />
                        <Button variant="ghost" size="icon" @click="copyToClipboard">
                            <Copy class="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </div>

            <DialogFooter class="sm:justify-end">
                <Button variant="ghost" @click="open = false">Cancel</Button>
                <Button @click="generateInvite" :disabled="loading">
                    {{ loading ? 'Generating...' : 'Generate' }}
                </Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Link as LinkIcon, Copy } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import api from '@/services/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { NumberField, NumberFieldContent, NumberFieldDecrement, NumberFieldInput, NumberFieldIncrement } from '@/components/ui/number-field'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const props = defineProps<{ channelId: string }>()

const open = ref(false)
const expiresIn = ref(5)
const loading = ref(false)
const inviteToken = ref('')

const inviteUrl = computed(() => `${window.location.origin}/join/${inviteToken.value}`)

// Reset state when dialog opens
watch(open, (isOpen) => {
    if (isOpen) {
        expiresIn.value = 5
        inviteToken.value = ''
    }
})

async function generateInvite() {
    loading.value = true
    try {
        const res = await api.post(`/channels/${props.channelId}/invite`, {
            expires_in_minutes: expiresIn.value,
        })
        inviteToken.value = res.data.token
    } catch (error) {
        console.error('Failed to generate invite', error)
    } finally {
        loading.value = false
    }
}

function copyToClipboard() {
    navigator.clipboard.writeText(inviteUrl.value)
    toast('Copied to clipboard')
}
</script>