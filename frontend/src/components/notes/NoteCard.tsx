import {
  Badge,
  Box,
  Flex,
  HStack,
  Text,
} from '@chakra-ui/react'
import { Bot, Pin, User } from 'lucide-react'
import type { NoteResponse } from '../../types'

const TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  technique: { label: 'Technique', color: 'blue.400' },
  drill: { label: 'Drill', color: 'green.400' },
  goal: { label: 'Goal', color: 'purple.400' },
  gear: { label: 'Gear', color: 'orange.400' },
  gym: { label: 'Gym', color: 'teal.400' },
  insight: { label: 'Insight', color: 'pink.400' },
}

interface NoteCardProps {
  note: NoteResponse
  onClick: (note: NoteResponse) => void
}

export function NoteCard({ note, onClick }: NoteCardProps) {
  const cfg = TYPE_CONFIG[note.type] ?? { label: note.type, color: 'gray.400' }
  const isAI = note.source === 'ai'

  return (
    <Box
      bg="bg.subtle"
      borderRadius="lg"
      p={3}
      borderLeft="4px solid"
      borderLeftColor={cfg.color}
      cursor="pointer"
      onClick={() => onClick(note)}
      _hover={{ bg: 'bg.muted' }}
      transition="background 0.15s ease"
    >
      {/* Top row: type label + badges */}
      <Flex align="center" gap={2} mb={1}>
        <Text fontSize="xs" fontWeight="bold" color={cfg.color} textTransform="uppercase">
          {cfg.label}
        </Text>
        <HStack spacing={1} ml="auto">
          {note.pinned && (
            <Box as={Pin} size={14} color="brand.primary" fill="currentColor" />
          )}
          <Badge
            fontSize="2xs"
            px={1.5}
            py={0.5}
            borderRadius="sm"
            bg={isAI ? 'accent.blue' : 'bg.panel'}
            color={isAI ? 'white' : 'text.secondary'}
            display="flex"
            alignItems="center"
            gap={1}
          >
            <Box as={isAI ? Bot : User} size={10} />
            {isAI ? 'AI' : 'Manual'}
          </Badge>
        </HStack>
      </Flex>

      {/* Title */}
      <Text fontSize="sm" fontWeight="semibold" noOfLines={1} color="text.primary">
        {note.title}
      </Text>

      {/* Summary preview */}
      {note.summary && (
        <Text fontSize="xs" color="text.secondary" noOfLines={2} mt={1}>
          {note.summary}
        </Text>
      )}
    </Box>
  )
}
