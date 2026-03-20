import { useEffect } from 'react'
import { Center, Flex, Spinner, Text, VStack } from '@chakra-ui/react'
import { MessageCircle } from 'lucide-react'
import { MessageBubble } from './MessageBubble'
import { TypingIndicator } from './TypingIndicator'
import type { MessageResponse } from '../../types'
import type { Citation } from './CitationBadge'

interface MessageListProps {
  messages: MessageResponse[]
  isLoading: boolean
  isPending: boolean
  isAtBottom: boolean
  scrollToBottom: () => void
  anchorRef: (node: HTMLDivElement | null) => void
  onCitationClick?: (citation: Citation) => void
}

export function MessageList({
  messages,
  isLoading,
  isPending,
  isAtBottom,
  scrollToBottom,
  anchorRef,
  onCitationClick,
}: MessageListProps) {
  // Auto-scroll when new messages arrive, but only if already at bottom
  useEffect(() => {
    if (isAtBottom) {
      scrollToBottom()
    }
  }, [messages.length, isPending, isAtBottom, scrollToBottom])

  if (isLoading) {
    return (
      <Center flex={1} py={20}>
        <Spinner size="xl" color="brand.primary" thickness="3px" />
      </Center>
    )
  }

  if (messages.length === 0 && !isPending) {
    return (
      <VStack spacing={3} flex={1} justify="center" align="center" py={20} px={6}>
        <Flex
          align="center"
          justify="center"
          w="64px"
          h="64px"
          borderRadius="full"
          bg="brand.subtle"
          color="brand.primary"
        >
          <MessageCircle size={32} color="currentColor" />
        </Flex>
        <Text color="text.secondary" fontSize="lg" fontWeight="medium">
          Start a conversation
        </Text>
        <Text color="text.muted" fontSize="sm" textAlign="center" maxW="280px">
          Ask your AI coach anything about training, technique, or strategy.
        </Text>
      </VStack>
    )
  }

  return (
    <Flex direction="column" gap={3} px={4} py={4} pb="140px">
      {messages.map((msg) => (
        <MessageBubble
          key={msg.id}
          role={msg.role}
          content={msg.content}
          isOptimistic={msg.id.startsWith('optimistic-')}
          metadata={msg.metadata_}
          onCitationClick={onCitationClick}
        />
      ))}
      {isPending && <TypingIndicator />}
      <div ref={anchorRef} />
    </Flex>
  )
}
