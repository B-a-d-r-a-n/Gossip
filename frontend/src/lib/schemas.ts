import { z } from 'zod'

export const loginSchema = z.object({
    username: z.string().min(3, 'Username must be at least 3 characters'),
    password: z.string().min(6, 'Password must be at least 6 characters'),
})

export const registerSchema = loginSchema

export const inviteTokenSchema = z.string().max(200).regex(/^[a-f0-9-]+$/i, 'Invalid token format')

export type LoginForm = z.infer<typeof loginSchema>
export type RegisterForm = z.infer<typeof registerSchema>
export type InviteToken = z.infer<typeof inviteTokenSchema>