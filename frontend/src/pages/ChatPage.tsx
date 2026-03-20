import { useEffect, useRef } from 'react'
import { useParams, useNavigate, useOutletContext } from 'react-router-dom'
import {
  Alert,
  AlertIcon,
  Center,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Flex,
  Spinner,
  useDisclosure,
  useToast,
} from '@chakra-ui/react'
import {
  useConversations,
  useMessages,
  useSendMessage,
} from '../hooks/use-conversations'
import { useScrollAnchor } from '../hooks/use-scroll-anchor'
import { createConversation } from '../services/conversations'
import { MessageList } from '../components/chat/MessageList'
import { ChatInput } from '../components/chat/ChatInput'
import { ScrollToBottomButton } from '../components/chat/ScrollToBottomButton'
import { CitationDrawer } from '../components/chat/CitationDrawer'
import { EmptyChatState } from '../components/chat/EmptyChatState'
import { SessionForm } from '../components/journal/SessionForm'
import type { Citation } from '../components/chat/CitationBadge'
import type { ChatMessage, LayoutOutletContext } from '../types'
import type { AxiosError } from 'axios'
import { useState } from 'react'

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const navigate = useNavigate()
  const toast = useToast()
  const { setPageTitle } = useOutletContext<LayoutOutletContext>()

  const sendMessage = useSendMessage()
  const creatingRef = useRef(false)

  // Scroll anchor
  const { anchorRef, isAtBottom, scrollToBottom } = useScrollAnchor()

  // Citation drawer
  const citationDrawer = useDisclosure()
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null)

  // Session drawer (FAM → Log Session)
  const sessionDrawer = useDisclosure()

  // Quota exceeded state
  const [quotaExceeded, setQuotaExceeded] = useState(false)

  function handleCitationClick(citation: Citation) {
    setActiveCitation(citation)
    citationDrawer.onOpen()
  }

  // When no conversationId in URL, create a new conversation and redirect
  useEffect(() => {
    if (conversationId || creatingRef.current) return
    creatingRef.current = true
    createConversation()
      .then((conv) => {
        navigate(`/chat/${conv.id}`, { replace: true })
      })
      .catch((err) => {
        creatingRef.current = false
        const axiosErr = err as AxiosError<{ detail?: string }>
        const message = axiosErr?.response?.data?.detail || 'Failed to start conversation'
        toast({ title: message, status: 'error', duration: 4000 })
      })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId])

  // Fetch messages for the current conversation
  const { data: messageData, isLoading: messagesLoading } = useMessages(conversationId ?? '')

  // Read conversation title from cached conversations list
  const { data: conversationsData } = useConversations()
  const currentConversation = conversationsData?.items.find((c) => c.id === conversationId)

  // Propagate title to TopAppBar
  useEffect(() => {
    const title = currentConversation?.title
    if (title && title !== 'New Conversation') {
      setPageTitle(title)
    } else {
      setPageTitle(null)
    }
  }, [currentConversation?.title, setPageTitle])

  // Clear title on unmount
  useEffect(() => {
    return () => setPageTitle(null)
  }, [setPageTitle])

  // Handle send
  function handleSend(content: string) {
    if (!conversationId) return
    sendMessage.mutate(
      { conversationId, content },
      {
        onError: (err) => {
          const axiosErr = err as AxiosError
          if (axiosErr?.response?.status === 429) {
            setQuotaExceeded(true)
          }
        },
      },
    )
  }

  // Handle retry on failed message
  function handleRetry(message: ChatMessage) {
    if (!conversationId) return
    sendMessage.mutate(
      { conversationId, content: message.content, retryId: message.id },
      {
        onError: (err) => {
          const axiosErr = err as AxiosError
          if (axiosErr?.response?.status === 429) {
            setQuotaExceeded(true)
          }
        },
      },
    )
  }

  // Loading state while creating conversation
  if (!conversationId) {
    return (
      <Center flex={1} py={20}>
        <Spinner size="xl" color="brand.primary" thickness="3px" />
      </Center>
    )
  }

  const messages = messageData?.items ?? []

  const isEmpty = messages.length === 0 && !messagesLoading && !sendMessage.isPending

  return (
    <Flex direction="column" flex={1}>
      {quotaExceeded && (
        <Alert status="warning" variant="subtle" borderRadius={0}>
          <AlertIcon />
          Daily AI message quota reached. Please try again tomorrow.
        </Alert>
      )}

      {isEmpty ? (
        <EmptyChatState onPromptClick={handleSend} />
      ) : (
        <MessageList
          messages={messages}
          isLoading={messagesLoading}
          isPending={sendMessage.isPending}
          isAtBottom={isAtBottom}
          scrollToBottom={scrollToBottom}
          anchorRef={anchorRef}
          onCitationClick={handleCitationClick}
          onRetry={handleRetry}
        />
      )}

      <ScrollToBottomButton
        isVisible={!isAtBottom && messages.length > 0}
        onClick={scrollToBottom}
      />

      <ChatInput
        onSend={handleSend}
        isDisabled={quotaExceeded || sendMessage.isPending}
        onLogSession={sessionDrawer.onOpen}
        onAttachNote={() => toast({ title: 'Notes coming soon', status: 'info', duration: 2000 })}
      />

      <CitationDrawer
        citation={activeCitation}
        isOpen={citationDrawer.isOpen}
        onClose={citationDrawer.onClose}
      />

      <Drawer
        isOpen={sessionDrawer.isOpen}
        onClose={sessionDrawer.onClose}
        placement="bottom"
      >
        <DrawerOverlay />
        <DrawerContent bg="bg.muted" borderTopRadius="xl" maxH="50vh">
          <DrawerCloseButton color="text.secondary" />
          <DrawerHeader color="text.primary">Quick Log</DrawerHeader>
          <DrawerBody pb={8} overflowY="auto">
            <SessionForm mode="quick" onSuccess={sessionDrawer.onClose} />
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Flex>
  )
}
