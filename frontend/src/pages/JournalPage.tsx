import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Box,
  Container,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  useDisclosure,
  useToast,
  VStack,
} from '@chakra-ui/react'
import { useOutletContext } from 'react-router-dom'
import { JournalList } from '../components/journal/JournalList'
import { SessionForm } from '../components/journal/SessionForm'
import { useInfiniteJournalSessions, useDeleteJournalSession } from '../hooks/use-journal'
import { useIntersectionObserver } from '../hooks/useIntersectionObserver'
import type { LayoutOutletContext, SessionResponse } from '../types'
import type { AxiosError } from 'axios'

export function JournalPage() {
  const { setPageTitle } = useOutletContext<LayoutOutletContext>()
  const toast = useToast()

  useEffect(() => {
    setPageTitle('Journal')
    return () => setPageTitle(null)
  }, [setPageTitle])

  const filters = useMemo(() => ({}), [])

  const { data, isLoading, hasNextPage, isFetchingNextPage, fetchNextPage } =
    useInfiniteJournalSessions(filters)

  const deleteMutation = useDeleteJournalSession()

  // --- Optimistic state masks ---
  const [pendingSessions, _setPendingSessions] = useState<SessionResponse[]>([])
  const [deletedIds, setDeletedIds] = useState<Set<string>>(new Set())

  const flattenedPages = useMemo(() => data?.pages.flatMap((page) => page.items) ?? [], [data])

  const visibleSessions = useMemo(
    () => [...pendingSessions, ...flattenedPages].filter((s) => !deletedIds.has(s.id)),
    [pendingSessions, flattenedPages, deletedIds],
  )

  const [editingSession, setEditingSession] = useState<SessionResponse | undefined>()
  const { isOpen, onOpen, onClose } = useDisclosure()

  function handleEdit(session: SessionResponse) {
    setEditingSession(session)
    onOpen()
  }

  function handleDelete(id: string) {
    // Optimistic: hide the card immediately
    setDeletedIds((prev) => new Set(prev).add(id))

    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast({ title: 'Session deleted', status: 'success', duration: 3000 })
      },
      onError: (err) => {
        // Rollback: card reappears
        setDeletedIds((prev) => {
          const next = new Set(prev)
          next.delete(id)
          return next
        })
        const msg =
          (err as AxiosError<{ detail?: string }>)?.response?.data?.detail || 'Delete failed'
        toast({ title: msg, status: 'error', duration: 4000 })
      },
    })
  }

  function handleEditSuccess() {
    onClose()
    setEditingSession(undefined)
  }

  // Infinite scroll sentinel
  const sentinelRef = useRef<HTMLDivElement>(null)
  const loadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage()
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  useIntersectionObserver(sentinelRef, loadMore, {
    enabled: hasNextPage && !isFetchingNextPage,
  })

  return (
    <Container maxW="container.md" py={4}>
      <VStack spacing={4} align="stretch">
        <JournalList
          sessions={visibleSessions}
          isLoading={isLoading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          sentinelRef={sentinelRef}
          isFetchingNextPage={isFetchingNextPage}
          hasNextPage={hasNextPage}
        />
      </VStack>

      {/* Edit Drawer */}
      <Drawer
        isOpen={isOpen}
        onClose={() => {
          onClose()
          setEditingSession(undefined)
        }}
        placement="bottom"
      >
        <DrawerOverlay />
        <DrawerContent bg="bg.muted" borderTopRadius="xl" maxH="85vh">
          <DrawerCloseButton color="text.secondary" />
          <DrawerHeader color="text.primary">
            {editingSession ? 'Edit Session' : 'New Session'}
          </DrawerHeader>
          <DrawerBody pb={8} overflowY="auto">
            <Box pb={4}>
              <SessionForm
                mode="full"
                editingSession={editingSession}
                onSuccess={handleEditSuccess}
                onCancel={() => {
                  onClose()
                  setEditingSession(undefined)
                }}
              />
            </Box>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Container>
  )
}
