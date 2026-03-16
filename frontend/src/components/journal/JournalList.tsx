import { Box, Center, Skeleton, Text, VStack } from '@chakra-ui/react'
import { BookOpen } from 'lucide-react'
import { SessionCard } from './SessionCard'
import { groupSessionsByDate } from './session-utils'
import type { SessionResponse } from '../../types'

interface JournalListProps {
  sessions: SessionResponse[]
  isLoading: boolean
  onEdit: (session: SessionResponse) => void
  onDelete: (id: string) => void
}

export function JournalList({ sessions, isLoading, onEdit, onDelete }: JournalListProps) {
  if (isLoading) {
    return (
      <VStack spacing={3} align="stretch">
        {[1, 2, 3].map((n) => (
          <Skeleton key={n} height="64px" borderRadius="lg" />
        ))}
      </VStack>
    )
  }

  if (sessions.length === 0) {
    return (
      <Center flexDirection="column" py={12} gap={3}>
        <Box as={BookOpen} size={40} color="text.muted" />
        <Text color="text.muted" fontWeight="medium">
          No sessions yet
        </Text>
        <Text fontSize="sm" color="text.muted">
          Tap + to log your first session
        </Text>
      </Center>
    )
  }

  const groups = groupSessionsByDate(sessions)

  return (
    <VStack spacing={4} align="stretch">
      {groups.map((group) => (
        <Box key={group.label}>
          <Text
            fontSize="xs"
            color="text.muted"
            textTransform="uppercase"
            letterSpacing="wide"
            fontWeight="semibold"
            mb={2}
            position="sticky"
            top={0}
            bg="bg.canvas"
            py={1}
            zIndex={1}
          >
            {group.label}
          </Text>
          <VStack spacing={2} align="stretch">
            {group.sessions.map((session) => (
              <SessionCard
                key={session.id}
                session={session}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </VStack>
        </Box>
      ))}
    </VStack>
  )
}
