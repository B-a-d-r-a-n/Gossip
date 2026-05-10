<template>
    <div class="flex gap-2 p-4 border-t border-border items-end">
        <Textarea ref="textareaRef" v-model="content" placeholder="Type a message..." class="flex-1"
            rows="1" @keydown.enter.exact.prevent="send" />
        <Button @click="send" :disabled="!content.trim()" class="h-10 w-10 sm:h-auto sm:w-auto">
            <Send class="h-4 w-4" />
            <span class="hidden sm:inline ml-2">Send</span>
        </Button>
    </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Send } from 'lucide-vue-next'

const emit = defineEmits<{
    send: [content: string]
}>()

const content = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function send() {
    if (!content.value.trim()) return
    emit('send', content.value)
    content.value = ''
    nextTick(() => {
        textareaRef.value?.focus()
    })
}
</script>
