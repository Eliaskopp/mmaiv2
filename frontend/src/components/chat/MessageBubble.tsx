import { Box, Flex, Image, Text } from '@chakra-ui/react'
import { MarkdownContent } from './MarkdownContent'
import { CitationBadge } from './CitationBadge'
import type { Citation } from './CitationBadge'

interface MessageBubbleProps {
  role: string
  content: string
  createdAt: string
  isOptimistic?: boolean
  metadata?: Record<string, unknown> | null
  onCitationClick?: (citation: Citation) => void
}

function formatTime(iso: string): string {
  const date = new Date(iso)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function MessageBubble({
  role,
  content,
  createdAt,
  isOptimistic,
  metadata,
  onCitationClick,
}: MessageBubbleProps) {
  const isUser = role === 'user'
  const citations = metadata?.citations as Citation[] | undefined

  return (
    <Flex justify={isUser ? 'flex-end' : 'flex-start'} opacity={isOptimistic ? 0.7 : 1}>
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
          bg={isUser ? 'brand.primary' : 'bg.subtle'}
          color={isUser ? 'white' : 'text.primary'}
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

        <Text
          fontSize="2xs"
          color="text.muted"
          mt={1}
          textAlign={isUser ? 'right' : 'left'}
          px={1}
        >
          {formatTime(createdAt)}
        </Text>
      </Box>
    </Flex>
  )
}
