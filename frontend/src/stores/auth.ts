import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { User } from '@/types'

/**
 * Auth store keeps the access token in-memory only (not exposed).
 * Refresh tokens live in Secure HttpOnly cookies (server-set).
 * Initialization flow:
 *  - Call GET /auth/me to validate current access token
 *  - If 401, call POST /auth/refresh (will rely on cookie)
 *  - If refresh succeeds, set access token in-memory and re-check /auth/me
 */
export const useAuthStore = defineStore('auth', () => {
    const user = ref<User | null>(null)
    const isReady = ref(false)

    const failedRefreshAttempts = ref(0)
    const MAX_REFRESH_ATTEMPTS = 3

    function recordFailedRefresh() {
        failedRefreshAttempts.value++
    }

    function resetFailedRefreshAttempts() {
        failedRefreshAttempts.value = 0
    }

    function hasExceededMaxRefreshAttempts() {
        return failedRefreshAttempts.value >= MAX_REFRESH_ATTEMPTS
    }

    async function logout() {
        try {
            await api.post('/auth/logout')
        } catch (_) {
            console.log(_);
        }
        user.value = null
        resetFailedRefreshAttempts()
    }

    async function tryRefresh() {
        if (hasExceededMaxRefreshAttempts()) {
            return false
        }
        try {
            await api.post('/auth/refresh')
            resetFailedRefreshAttempts()
            return true
        } catch (_) {
            console.log(_);
            recordFailedRefresh()
            return false
        }
    }

    function getUserId(): string | null {
        return user.value?.id || null
    }

    async function initialize() {
        try {
            if (user.value) {
                return true
            }
            const res = await api.get('/auth/me')
            user.value = res.data.user
            resetFailedRefreshAttempts()
            return true
        } catch (err: any) {
            if (err.response?.status === 401) {
                const refreshed = await tryRefresh()
                if (!refreshed) return false
                try {
                    const res2 = await api.get('/auth/me')
                    user.value = res2.data.user
                    return true
                } catch {
                    return false
                }
            }
            return false
        } finally {
            isReady.value = true
        }
    }

    return { user, logout, tryRefresh, initialize, hasExceededMaxRefreshAttempts, isReady, getUserId }
})
