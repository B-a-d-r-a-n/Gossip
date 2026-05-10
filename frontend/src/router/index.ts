import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: () => import('@/views/ChatLayout.vue'),
            meta: { requiresAuth: true },
            children: [
                {
                    path: '',
                    redirect: '/hub',
                },
                {
                    path: 'hub',
                    name: 'hub',
                    component: () => import('@/views/HubView.vue'),
                },
                {
                    path: 'channel/:id',
                    name: 'channel',
                    component: () => import('@/views/ChannelView.vue'),
                },
            ],
        },
        {
            path: '/login',
            name: 'login',
            component: () => import('@/views/LoginView.vue'),
            meta: { guestOnly: true },
        },
        {
            path: '/register',
            name: 'register',
            component: () => import('@/views/RegisterView.vue'),
            meta: { guestOnly: true },
        },
        {
            path: '/join/:token',
            name: 'join',
            component: () => import('@/views/JoinView.vue'),
            meta: { requiresAuth: true },
        },
    ],
})

router.beforeEach(async (to, from, next) => {
    const auth = useAuthStore()

    if (!auth.isReady) {
        await auth.initialize()
    }

    if (to.meta.requiresAuth && !auth.user) {
        next('/login')
    } else if (to.meta.guestOnly && auth.user) {
        next('/hub')
    } else if (to.name === 'channel' && to.params.id) {
        const { useChannelStore } = await import('@/stores/channel')
        const channelStore = useChannelStore()
        await channelStore.fetchUserChannels()
        const isMember = channelStore.userChannels.some(c => c.id === to.params.id)
        if (!isMember) {
            next('/hub')
        } else {
            channelStore.setActiveChannelById(to.params.id as string)
            next()
        }
    } else {
        next()
    }
})

export default router
