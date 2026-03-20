export interface ConversationCreate {
  title?: string | null
}

export interface MessageCreate {
  content: string
}

export interface MessageResponse {
  id: string
  conversation_id: string
  role: string
  content: string
  metadata_: Record<string, unknown> | null
  created_at: string
}

export type MessageStatus = 'confirmed' | 'pending' | 'error'

export type ChatMessage = MessageResponse & {
  status: MessageStatus
  errorReason?: string
}

export interface SendMessageVariables {
  conversationId: string
  content: string
  retryId?: string
}

export interface ConversationResponse {
  id: string
  user_id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string | null
}

export interface ConversationDetailResponse extends ConversationResponse {
  messages: MessageResponse[]
}

export interface ConversationListResponse {
  items: ConversationResponse[]
  total: number
  offset: number
  limit: number
}

export interface MessageListResponse {
  items: MessageResponse[]
  total: number
  offset: number
  limit: number
}
