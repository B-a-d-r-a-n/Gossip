import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL, withCredentials: true })
let isRefreshing = false

api.interceptors.response.use(
    res => res,
    async error => {
        const status = error.response?.status

        if (status === 401) {
            const auth = useAuthStore()

            if (isRefreshing) {
                return Promise.reject(error)
            }

            if (auth.hasExceededMaxRefreshAttempts()) {
                await auth.logout()
                return Promise.reject(error)
            }

            isRefreshing = true
            const refreshed = await auth.tryRefresh()
            isRefreshing = false

            if (!refreshed) {
                await auth.logout()
                return Promise.reject(error)
            }

            return api.request(error.config)
        }

        return Promise.reject(error)
    }
)

export default api