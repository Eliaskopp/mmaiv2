import { useEffect, useMemo, useState } from 'react'
import {
  Box,
  Container,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Flex,
  Skeleton,
  Text,
  useDisclosure,
  useToast,
  VStack,
} from '@chakra-ui/react'
import { Link as RouterLink, useOutletContext } from 'react-router-dom'
import { useACWR } from '../hooks/use-stats'
import { JournalList } from '../components/journal/JournalList'
import { SessionForm } from '../components/journal/SessionForm'
import { useJournalSessions, useDeleteJournalSession } from '../hooks/use-journal'
import type { LayoutOutletContext, SessionResponse } from '../types'
import type { AxiosError } from 'axios'

function daysAgoISO(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().slice(0, 10)
}

export function JournalPage() {
  const { setPageTitle } = useOutletContext<LayoutOutletContext>()
  const toast = useToast()

  useEffect(() => {
    setPageTitle('Journal')
    return () => setPageTitle(null)
  }, [setPageTitle])

  const filters = useMemo(() => ({
    date_from: daysAgoISO(30),
    date_to: new Date().toISOString().slice(0, 10),
    limit: 100,
  }), [])

  const { data: acwr, isLoading: acwrLoading } = useACWR()
  const { data, isLoading } = useJournalSessions(filters)
  const deleteMutation = useDeleteJournalSession()

  const [editingSession, setEditingSession] = useState<SessionResponse | undefined>()
  const { isOpen, onOpen, onClose } = useDisclosure()

  function handleEdit(session: SessionResponse) {
    setEditingSession(session)
    onOpen()
  }

  function handleDelete(id: string) {
    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast({ title: 'Session deleted', status: 'success', duration: 3000 })
      },
      onError: (err) => {
        const msg = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail || 'Delete failed'
        toast({ title: msg, status: 'error', duration: 4000 })
      },
    })
  }

  function handleEditSuccess() {
    onClose()
    setEditingSession(undefined)
  }

  return (
    <Container maxW="container.md" py={4}>
      <VStack spacing={4} align="stretch">
        {/* Compact ACWR widget — links to /stats */}
        <Box
          as={RouterLink}
          to="/stats"
          bg="bg.subtle"
          p={4}
          borderRadius="lg"
          _hover={{ bg: 'bg.muted' }}
          transition="background 0.15s ease"
          cursor="pointer"
          display="block"
          textDecoration="none"
        >
          <Flex align="center" gap={4}>
            <Box>
              <Text fontSize="sm" fontWeight="semibold" color="text.primary">
                Training Load
              </Text>
              {acwrLoading ? (
                <Skeleton height="14px" width="140px" mt={1} />
              ) : (
                <Text fontSize="xs" color="text.secondary" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                  ACWR: {acwr?.is_calibrating ? 'Calibrating' : acwr?.acwr_ratio?.toFixed(2) ?? '--'} &middot;{' '}
                  {acwr?.is_calibrating ? 'Calibrating' :
                   acwr?.risk_zone === 'optimal' ? 'Optimal' :
                   acwr?.risk_zone === 'high' ? 'High' :
                   acwr?.risk_zone === 'very_high' ? 'Danger' :
                   acwr?.risk_zone === 'low' ? 'Low' : 'No data'}
                </Text>
              )}
            </Box>
            <Text ml="auto" color="text.muted" fontSize="lg">&rsaquo;</Text>
          </Flex>
        </Box>
        <JournalList
          sessions={data?.items ?? []}
          isLoading={isLoading}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </VStack>

      {/* Edit Drawer */}
      <Drawer
        isOpen={isOpen}
        onClose={() => { onClose(); setEditingSession(undefined) }}
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
                onCancel={() => { onClose(); setEditingSession(undefined) }}
              />
            </Box>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Container>
  )
}
