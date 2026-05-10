<template>
    <div class="flex h-screen">
        <!-- Desktop Sidebar -->
        <aside class="hidden lg:flex w-62.5 bg-muted border-r border-border flex flex-col flex-shrink-0">
            <div class="p-4 flex justify-between items-center border-b border-border">
                <h3 class="font-semibold">Channels</h3>
                <div class="flex items-center gap-1">
                    <Button variant="ghost" size="icon" @click="handleLogout">
                        <LogOut class="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" @click="goHome">
                        <Home class="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" @click="showCreateDialog = true">
                        <Plus class="h-4 w-4" />
                    </Button>
                    <ThemeToggle />
                </div>
            </div>
            <div class="flex-1 overflow-y-auto p-2">
                <div v-for="channel in channelStore.userChannels" :key="channel.id"
                    class="px-3 py-2 cursor-pointer rounded-md mb-1 hover:bg-accent"
                    :class="{ 'bg-primary text-primary-foreground': isChannelActive(channel.id) }"
                    @click="selectChannel(channel)">
                    # {{ channel.name }}
                </div>
            </div>
        </aside>

        <!-- Mobile Sidebar Overlay -->
        <div v-if="sidebarOpen" class="fixed inset-0 z-50 lg:hidden" @click.self="sidebarOpen = false">
            <div class="fixed inset-0 bg-black/50" @click="sidebarOpen = false" />
            <div class="fixed inset-y-0 left-0 w-62.5 bg-muted border-r border-border flex flex-col shadow-xl">
                <div class="p-4 flex justify-between items-center border-b border-border">
                    <h3 class="font-semibold">Channels</h3>
                    <Button variant="ghost" size="icon" @click="sidebarOpen = false">
                        <X class="h-5 w-5" />
                    </Button>
                </div>
                <div class="flex-1 overflow-y-auto p-2">
                    <div v-for="channel in channelStore.userChannels" :key="channel.id"
                        class="px-3 py-2 cursor-pointer rounded-md mb-1 hover:bg-accent"
                        :class="{ 'bg-primary text-primary-foreground': isChannelActive(channel.id) }"
                        @click="selectChannel(channel); sidebarOpen = false">
                        # {{ channel.name }}
                    </div>
                </div>
                <div class="p-4 border-t border-border flex justify-between">
                    <Button variant="ghost" size="icon" @click="handleLogout">
                        <LogOut class="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" @click="goHome">
                        <Home class="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" @click="showCreateDialog = true; sidebarOpen = false">
                        <Plus class="h-4 w-4" />
                    </Button>
                    <ThemeToggle />
                </div>
            </div>
        </div>

        <!-- Mobile Header -->
        <header class="lg:hidden fixed top-0 left-0 right-0 h-14 bg-muted border-b border-border flex items-center px-4 z-40">
            <Button variant="ghost" size="icon" @click="sidebarOpen = true">
                <Menu class="h-5 w-5" />
            </Button>
            <span class="ml-3 font-semibold">Chat App</span>
        </header>

        <!-- Main Content -->
        <main class="flex-1 flex flex-col pt-14 lg:pt-0">
            <div class="flex-1 overflow-y-auto">
                <router-view :key="$route.fullPath" />
            </div>
        </main>

        <Dialog v-model:open="showCreateDialog">
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Create Channel</DialogTitle>
                </DialogHeader>
                
                <div class="mb-4">
                    <label for="channelName">Name</label>
                    <Input id="channelName" v-model="newChannel.name" class="w-full" />
                </div>
                <div class="mb-4">
                    <label for="channelDesc">Description</label>
                    <Textarea id="channelDesc" v-model="newChannel.description" class="w-full" />
                </div>
                
                <DialogFooter>
                    <Button variant="ghost" @click="showCreateDialog = false">Cancel</Button>
                    <Button @click="handleCreateChannel">Create</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    </div>
</template>

<script setup lang="ts">
    import { ref, onMounted } from 'vue'
    import { useRouter } from 'vue-router'
    import { useChannelStore } from '@/stores/channel'
    import { useAuthStore } from '@/stores/auth'
    import type { Channel } from '@/types'
    import { Button } from '@/components/ui/button'
    import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
    import { Input } from '@/components/ui/input'
    import { Textarea } from '@/components/ui/textarea'
    import { Plus, Home, LogOut, Menu, X } from 'lucide-vue-next'
    import ThemeToggle from '@/components/layout/ThemeToggle.vue'
    
    const channelStore = useChannelStore()
    const authStore = useAuthStore()
    const router = useRouter()
    const sidebarOpen = ref(false)
    const showCreateDialog = ref(false)
    const newChannel = ref({ name: '', description: '' })
    
    onMounted(() => {
        channelStore.fetchUserChannels()
    })
    
    function selectChannel(channel: Channel) {
        channelStore.setActiveChannel(channel)
        channelStore.setActiveChannelRole(channel.id)
        channelStore.setActiveChannelById(channel.id)
        router.push(`/channel/${channel.id}`)
    }

    async function handleLogout() {
        await authStore.logout()
        router.push('/login')
    }
    
    function isChannelActive(channelId: string) {
        return channelStore.activeChannel?.id === channelId || channelStore.lastActiveChannelId === channelId
    }
    
    function goHome() {
        channelStore.clearActiveChannel()
        router.push('/hub')
    }
    
    async function handleCreateChannel() {
        await channelStore.createChannel(newChannel.value.name, newChannel.value.description)
        showCreateDialog.value = false
        newChannel.value = { name: '', description: '' }
    }
</script>