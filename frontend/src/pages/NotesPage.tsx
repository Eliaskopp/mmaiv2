import { useEffect, useMemo, useState } from 'react'
import {
  Box,
  Button,
  Center,
  Container,
  Flex,
  Skeleton,
  Text,
  VStack,
  useDisclosure,
} from '@chakra-ui/react'
import { MessageCircle, Pin, StickyNote } from 'lucide-react'
import { useNavigate, useOutletContext, useSearchParams } from 'react-router-dom'
import { NoteCard } from '../components/notes/NoteCard'
import { NoteDrawer } from '../components/notes/NoteDrawer'
import { useNotes } from '../hooks/use-notes'
import type { LayoutOutletContext, NoteResponse, NoteType } from '../types'

const NOTE_TYPES: Set<string> = new Set(['technique', 'drill', 'goal', 'gear', 'gym', 'insight'])

const TYPE_OPTIONS: { value: NoteType; label: string }[] = [
  { value: 'technique', label: 'Technique' },
  { value: 'drill', label: 'Drill' },
  { value: 'goal', label: 'Goal' },
  { value: 'gear', label: 'Gear' },
  { value: 'gym', label: 'Gym' },
  { value: 'insight', label: 'Insight' },
]

export function NotesPage() {
  const { setPageTitle } = useOutletContext<LayoutOutletContext>()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  useEffect(() => {
    setPageTitle('Notes')
    return () => setPageTitle(null)
  }, [setPageTitle])

  // Derive filter state from URL search params
  const rawType = searchParams.get('type')
  const typeFilter: NoteType | null =
    rawType && NOTE_TYPES.has(rawType) ? (rawType as NoteType) : null
  const pinnedOnly = searchParams.get('pinned') === 'true'

  function setTypeFilter(type: NoteType | null) {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (type) {
          next.set('type', type)
        } else {
          next.delete('type')
        }
        return next
      },
      { replace: true },
    )
  }

  function togglePinned() {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (pinnedOnly) {
          next.delete('pinned')
        } else {
          next.set('pinned', 'true')
        }
        return next
      },
      { replace: true },
    )
  }

  const filters = useMemo(
    () => ({
      limit: 100,
      status: 'active' as const,
      ...(typeFilter ? { type: typeFilter } : {}),
      ...(pinnedOnly ? { pinned: true } : {}),
    }),
    [typeFilter, pinnedOnly],
  )

  const { data, isLoading } = useNotes(filters)

  const [selectedNote, setSelectedNote] = useState<NoteResponse | undefined>()
  const { isOpen, onOpen, onClose } = useDisclosure()

  function handleCardClick(note: NoteResponse) {
    setSelectedNote(note)
    onOpen()
  }

  function handleDrawerClose() {
    onClose()
    setSelectedNote(undefined)
  }

  return (
    <Container maxW="container.md" py={4}>
      <VStack spacing={4} align="stretch">
        {/* Filter Bar — horizontal scrollable chips */}
        <Flex
          overflowX="auto"
          gap={2}
          pb={2}
          css={{
            '&::-webkit-scrollbar': { display: 'none' },
            scrollbarWidth: 'none',
          }}
        >
          {TYPE_OPTIONS.map((opt) => {
            const isSelected = opt.value === typeFilter
            return (
              <Button
                key={opt.value}
                variant={isSelected ? 'solid' : 'outline'}
                bg={isSelected ? 'brand.primary' : 'bg.muted'}
                color={isSelected ? 'chat.user.text' : 'text.primary'}
                borderColor="transparent"
                _hover={{ bg: isSelected ? 'brand.600' : 'bg.panel' }}
                onClick={() => setTypeFilter(isSelected ? null : (opt.value as NoteType))}
                size="sm"
                minH="48px"
                minW="auto"
                px={4}
                flexShrink={0}
              >
                {opt.label}
              </Button>
            )
          })}

          {/* Pinned toggle */}
          <Button
            variant={pinnedOnly ? 'solid' : 'outline'}
            bg={pinnedOnly ? 'brand.primary' : 'bg.muted'}
            color={pinnedOnly ? 'chat.user.text' : 'text.primary'}
            borderColor="transparent"
            _hover={{ bg: pinnedOnly ? 'brand.600' : 'bg.panel' }}
            onClick={togglePinned}
            size="sm"
            minH="48px"
            minW="48px"
            px={3}
            flexShrink={0}
            leftIcon={<Pin size={14} fill={pinnedOnly ? 'currentColor' : 'none'} />}
          >
            Pinned
          </Button>
        </Flex>

        {/* Note List */}
        {isLoading ? (
          <VStack spacing={3} align="stretch">
            {[1, 2, 3].map((n) => (
              <Skeleton key={n} height="72px" borderRadius="lg" />
            ))}
          </VStack>
        ) : data?.items.length === 0 ? (
          <Center flexDirection="column" py={12} gap={3}>
            <Box as={StickyNote} size={40} color="text.muted" />
            <Text color="text.muted" fontWeight="medium">
              No notes yet
            </Text>
            <Text fontSize="sm" color="text.muted" textAlign="center" maxW="260px">
              Go chat with your AI Coach to extract some techniques.
            </Text>
            <Button
              variant="outline"
              size="sm"
              leftIcon={<MessageCircle size={14} />}
              onClick={() => navigate('/chat')}
              mt={2}
            >
              Open Coach
            </Button>
          </Center>
        ) : (
          <VStack spacing={2} align="stretch">
            {data?.items.map((note) => (
              <NoteCard key={note.id} note={note} onClick={handleCardClick} />
            ))}
          </VStack>
        )}
      </VStack>

      {/* Edit/View Drawer */}
      <NoteDrawer note={selectedNote} isOpen={isOpen} onClose={handleDrawerClose} />
    </Container>
  )
}
