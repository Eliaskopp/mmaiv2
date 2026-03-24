import { Box, Button, Flex, Image, Text } from '@chakra-ui/react'
import { AlertCircle, RotateCcw } from 'lucide-react'
import { MarkdownContent } from './MarkdownContent'
import { CitationBadge } from './CitationBadge'
import type { Citation } from './CitationBadge'
import type { ChatMessage } from '../../types'

interface MessageBubbleProps {
  message: ChatMessage
  onCitationClick?: (citation: Citation) => void
  onRetry?: (message: ChatMessage) => void
}

export function MessageBubble({ message, onCitationClick, onRetry }: MessageBubbleProps) {
  const { role, content, status, metadata_ } = message
  const isUser = role === 'user'
  const isError = status === 'error'
  const isPending = status === 'pending'
  const citations = metadata_?.citations as Citation[] | undefined

  return (
    <Flex
      justify={isUser ? 'flex-end' : 'flex-start'}
      opacity={isError ? 0.6 : isPending ? 0.7 : 1}
    >
      <Box maxW="85%">
        {!isUser && (
          <Flex align="center" gap={1.5} mb={1}>
            <Image src="/logo-symbol.png" alt="MMAi" w="22px" h="22px" />
            <Text fontSize="xs" color="text.muted" fontWeight="600">
              MMAi Coach
            </Text>
          </Flex>
        )}

        <Box
          bg={isUser ? 'chat.user.bg' : 'chat.ai.bg'}
          color={isUser ? 'chat.user.text' : 'chat.ai.text'}
          px={4}
          py={3}
          borderRadius="2xl"
          borderBottomRightRadius={isUser ? 'sm' : '2xl'}
          borderBottomLeftRadius={isUser ? '2xl' : 'sm'}
        >
          {isUser ? (
            <Text whiteSpace="pre-wrap" fontSize="sm" lineHeight="tall">
              {content}
            </Text>
          ) : (
            <MarkdownContent content={content} />
          )}

          {citations?.length && onCitationClick ? (
            <Flex gap={1.5} mt={2} flexWrap="wrap">
              {citations.map((c) => (
                <CitationBadge key={c.id} citation={c} onClick={onCitationClick} />
              ))}
            </Flex>
          ) : null}
        </Box>

        {isError && (
          <Flex align="center" justify="flex-end" gap={2} mt={1} px={1}>
            <Flex align="center" gap={1} color="red.400">
              <AlertCircle size={14} />
              <Text fontSize="xs">Send failed</Text>
            </Flex>
            {onRetry && (
              <Button
                variant="ghost"
                size="xs"
                color="brand.primary"
                leftIcon={<RotateCcw size={12} />}
                onClick={() => onRetry(message)}
              >
                Retry
              </Button>
            )}
          </Flex>
        )}
      </Box>
    </Flex>
  )
}
