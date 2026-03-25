import apiClient from './api-client'
import type {
  ConversationCreate,
  ConversationResponse,
  ConversationDetailResponse,
  ConversationListResponse,
  MessageResponse,
  MessageListResponse,
} from '../types'

export async function getConversations(offset = 0, limit = 20): Promise<ConversationListResponse> {
  const { data } = await apiClient.get<ConversationListResponse>('/conversations', {
    params: { offset, limit },
  })
  return data
}

export async function getConversation(id: string): Promise<ConversationDetailResponse> {
  const { data } = await apiClient.get<ConversationDetailResponse>(`/conversations/${id}`)
  return data
}

export async function createConversation(
  body: ConversationCreate = {},
): Promise<ConversationResponse> {
  const { data } = await apiClient.post<ConversationResponse>('/conversations', body)
  return data
}

export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/conversations/${id}`)
}

export async function getMessages(
  conversationId: string,
  offset = 0,
  limit = 50,
): Promise<MessageListResponse> {
  const { data } = await apiClient.get<MessageListResponse>(
    `/conversations/${conversationId}/messages`,
    { params: { offset, limit } },
  )
  return data
}

export async function sendMessage(
  conversationId: string,
  content: string,
): Promise<MessageResponse[]> {
  const { data } = await apiClient.post<MessageResponse[]>(
    `/conversations/${conversationId}/messages`,
    { content },
  )
  return data
}
