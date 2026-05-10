import type { components } from './generated/api'

export type User = components['schemas']['UserResponse']
export type Channel = components['schemas']['ChannelListItem']
export type Message = components['schemas']['MessageItem'] & { username?: string; role?: string }
export type MessagesResponse = components['schemas']['MessagesResponse']
export type InviteResponse = components['schemas']['InviteResponse']
export type WsTicketResponse = components['schemas']['WsTicketResponse']
export type MessageResponse = components['schemas']['MessageResponse']

export type RegisterRequest = components['schemas']['RegisterRequest']
export type LoginRequest = components['schemas']['LoginRequest']
export type ChannelCreate = components['schemas']['ChannelCreate']
export type ChannelInviteCreate = components['schemas']['ChannelInviteCreate']

export interface SentimentUpdate {
    id: string
    sentiment_label: string | null
    sentiment_score: number | null
    sentiment_status: string
}