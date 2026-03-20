import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useToast } from '@chakra-ui/react'
import {
  getConversations,
  getMessages,
  createConversation,
  deleteConversation,
  sendMessage,
} from '../services/conversations'
import type {
  ConversationCreate,
  ChatMessage,
  MessageResponse,
  SendMessageVariables,
} from '../types'

export const CONVERSATIONS_KEY = ['conversations'] as const
export const MESSAGES_KEY = ['messages'] as const

/** Cache shape for messages — items are ChatMessage (MessageResponse + UI state) */
interface ChatMessageList {
  items: ChatMessage[]
  total: number
  offset: number
  limit: number
}

function hydrate(msg: MessageResponse): ChatMessage {
  return { ...msg, status: 'confirmed' }
}

function getErrorToast(error: unknown): {
  title: string
  description: string
  toastStatus: 'warning' | 'error'
  httpStatus?: number
} {
  const axiosErr = error as {
    response?: { status?: number; data?: { detail?: string; error?: string } }
    code?: string
  }
  const status = axiosErr?.response?.status

  if (status === 429) {
    return {
      title: 'Quota Exceeded',
      description: 'Daily message limit reached. Resets at midnight.',
      toastStatus: 'warning',
      httpStatus: 429,
    }
  }
  if (status && status >= 500) {
    return {
      title: 'Server Error',
      description: 'Something went wrong. Tap Retry on your message.',
      toastStatus: 'error',
      httpStatus: status,
    }
  }
  if (axiosErr?.code === 'ECONNABORTED' || axiosErr?.code === 'ERR_NETWORK' || !status) {
    return {
      title: 'Connection Lost',
      description: 'Check your network and tap Retry.',
      toastStatus: 'error',
      httpStatus: 0,
    }
  }
  const detail = axiosErr?.response?.data?.detail || axiosErr?.response?.data?.error
  return {
    title: 'Send Failed',
    description: detail || 'Something went wrong. Tap Retry on your message.',
    toastStatus: 'error',
    httpStatus: status,
  }
}

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
    queryFn: async (): Promise<ChatMessageList> => {
      const data = await getMessages(conversationId)
      return { ...data, items: data.items.map(hydrate) }
    },
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
  const toast = useToast()

  return useMutation({
    mutationFn: ({ conversationId, content }: SendMessageVariables) =>
      sendMessage(conversationId, content),

    onMutate: async ({ conversationId, content, retryId }) => {
      await queryClient.cancelQueries({ queryKey: [...MESSAGES_KEY, conversationId] })

      const previous = queryClient.getQueryData<ChatMessageList>(
        [...MESSAGES_KEY, conversationId],
      )

      const optimisticId = retryId ?? `optimistic-${Date.now()}`

      if (previous) {
        let newItems: ChatMessage[]

        if (retryId) {
          // Retry: flip errored message back to pending in-place
          newItems = previous.items.map((m) =>
            m.id === retryId
              ? { ...m, status: 'pending' as const, errorReason: undefined }
              : m,
          )
        } else {
          // Fresh send: append optimistic message
          const optimisticMsg: ChatMessage = {
            id: optimisticId,
            conversation_id: conversationId,
            role: 'user',
            content,
            metadata_: null,
            created_at: new Date().toISOString(),
            status: 'pending',
          }
          newItems = [...previous.items, optimisticMsg]
        }

        queryClient.setQueryData<ChatMessageList>(
          [...MESSAGES_KEY, conversationId],
          { ...previous, items: newItems, total: newItems.length },
        )
      }

      return { optimisticId, conversationId }
    },

    onSuccess: (newMessages, { conversationId }, context) => {
      if (!context) return

      const current = queryClient.getQueryData<ChatMessageList>(
        [...MESSAGES_KEY, conversationId],
      )
      if (current) {
        const confirmedMessages = newMessages.map(hydrate)
        const items = current.items.flatMap((m) =>
          m.id === context.optimisticId ? confirmedMessages : [m],
        )
        queryClient.setQueryData<ChatMessageList>(
          [...MESSAGES_KEY, conversationId],
          { ...current, items, total: items.length },
        )
      }

      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY })
    },

    onError: (error, { conversationId }, context) => {
      if (!context) return

      const current = queryClient.getQueryData<ChatMessageList>(
        [...MESSAGES_KEY, conversationId],
      )
      const toastInfo = getErrorToast(error)

      if (current) {
        const items = current.items.map((m) =>
          m.id === context.optimisticId
            ? { ...m, status: 'error' as const, errorReason: toastInfo.description }
            : m,
        )
        queryClient.setQueryData<ChatMessageList>(
          [...MESSAGES_KEY, conversationId],
          { ...current, items },
        )
      }

      toast({
        title: toastInfo.title,
        description: toastInfo.description,
        status: toastInfo.toastStatus,
        duration: 5000,
        position: 'top',
        isClosable: true,
      })
    },
  })
}
