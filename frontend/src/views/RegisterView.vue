<template>
    <div class="min-h-screen flex items-center justify-center p-4">
        <Card class="w-full max-w-md">
            <CardHeader>
                <CardTitle>Register</CardTitle>
            </CardHeader>
            <CardContent>
                <form @submit.prevent="handleRegister">
                    <div class="mb-6">
                        <label for="username">Username</label>
                        <Input id="username" v-model="form.username" class="w-full" />
                        <small class="text-destructive">{{ errors.username }}</small>
                    </div>
                    <div class="mb-6">
                        <label for="password">Password</label>
                        <Input id="password" v-model="form.password" type="password" class="w-full" />
                        <small class="text-destructive">{{ errors.password }}</small>
                    </div>
                    <Button type="submit" class="w-full" :disabled="loading">
                        <span v-if="loading">Loading...</span>
                        <span v-else>Register</span>
                    </Button>
                </form>
                <div class="mt-3">
                    <router-link to="/login" class="text-muted-foreground hover:text-foreground text-sm">Already have an account? Login</router-link>
                </div>
            </CardContent>
        </Card>
    </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { registerSchema } from '@/lib/schemas'
import api from '@/services/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const router = useRouter()
const loading = ref(false)

const form = reactive({
    username: '',
    password: '',
})

const errors = reactive({
    username: '',
    password: '',
})

async function handleRegister() {
    errors.username = ''
    errors.password = ''

    const result = registerSchema.safeParse(form)
    if (!result.success) {
        result.error.issues.forEach(err => {
            if (err.path[0]) errors[err.path[0] as keyof typeof errors] = err.message
        })
        return
    }

    loading.value = true
    try {
        await api.post('/auth/register', form)
        router.push('/login')
    } catch (error) {
        console.error('Registration failed:', error)
    } finally {
        loading.value = false
    }
}
</script>


