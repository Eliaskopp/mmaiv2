import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getConversations,
  getMessages,
  createConversation,
  deleteConversation,
  sendMessage,
} from '../services/conversations'
import type {
  ConversationCreate,
  MessageResponse,
  MessageListResponse,
} from '../types'

export const CONVERSATIONS_KEY = ['conversations'] as const
export const MESSAGES_KEY = ['messages'] as const

export function useConversations() {
  return useQuery({
    queryKey: CONVERSATIONS_KEY,
    queryFn: () => getConversations(),
    staleTime: 30_000,
  })
}

export function useMessages(conversationId: string) {
  return useQuery({
    queryKey: [...MESSAGES_KEY, conversationId] as const,
    queryFn: () => getMessages(conversationId),
    enabled: !!conversationId,
    staleTime: Infinity,
  })
}

export function useCreateConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body?: ConversationCreate) => createConversation(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY })
    },
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteConversation(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY })
      queryClient.removeQueries({ queryKey: [...MESSAGES_KEY, id] })
    },
  })
}

export function useSendMessage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ conversationId, content }: { conversationId: string; content: string }) =>
      sendMessage(conversationId, content),

    onMutate: async ({ conversationId, content }) => {
      await queryClient.cancelQueries({ queryKey: [...MESSAGES_KEY, conversationId] })

      const previous = queryClient.getQueryData<MessageListResponse>(
        [...MESSAGES_KEY, conversationId],
      )

      if (previous) {
        const optimisticMsg: MessageResponse = {
          id: `optimistic-${Date.now()}`,
          conversation_id: conversationId,
          role: 'user',
          content,
          metadata_: null,
          created_at: new Date().toISOString(),
        }
        queryClient.setQueryData<MessageListResponse>(
          [...MESSAGES_KEY, conversationId],
          {
            ...previous,
            items: [...previous.items, optimisticMsg],
            total: previous.total + 1,
          },
        )
      }

      return { previous, conversationId }
    },

    onSuccess: (newMessages, { conversationId }) => {
      const current = queryClient.getQueryData<MessageListResponse>(
        [...MESSAGES_KEY, conversationId],
      )
      if (current) {
        const realItems = current.items.filter((m) => !m.id.startsWith('optimistic-'))
        queryClient.setQueryData<MessageListResponse>(
          [...MESSAGES_KEY, conversationId],
          {
            ...current,
            items: [...realItems, ...newMessages],
            total: realItems.length + newMessages.length,
          },
        )
      }
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY })
    },

    onError: (_error, _variables, context) => {
      if (context?.previous && context?.conversationId) {
        queryClient.setQueryData(
          [...MESSAGES_KEY, context.conversationId],
          context.previous,
        )
      }
    },
  })
}
