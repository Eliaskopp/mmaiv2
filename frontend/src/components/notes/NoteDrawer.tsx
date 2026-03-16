import { useEffect, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import {
  Box,
  Button,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  FormControl,
  FormLabel,
  HStack,
  IconButton,
  Input,
  Text,
  Textarea,
  VStack,
  useToast,
} from '@chakra-ui/react'
import { Archive, ExternalLink, Pin } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useUpdateNote } from '../../hooks/use-notes'
import type { NoteResponse, NoteUpdate } from '../../types'
import type { AxiosError } from 'axios'

interface NoteDrawerProps {
  note: NoteResponse | undefined
  isOpen: boolean
  onClose: () => void
}

interface FormValues {
  title: string
  summary: string
  user_notes: string
}

export function NoteDrawer({ note, isOpen, onClose }: NoteDrawerProps) {
  const toast = useToast()
  const navigate = useNavigate()
  const updateMutation = useUpdateNote()

  // Track pinned state locally for optimistic toggle
  const [localPinned, setLocalPinned] = useState(false)

  useEffect(() => {
    if (note) {
      setLocalPinned(note.pinned)
    }
  }, [note?.id, note?.pinned])

  const { control, handleSubmit, reset } = useForm<FormValues>({
    defaultValues: { title: '', summary: '', user_notes: '' },
  })

  useEffect(() => {
    if (note) {
      reset({
        title: note.title,
        summary: note.summary ?? '',
        user_notes: note.user_notes ?? '',
      })
    }
  }, [note, reset])

  function onSubmit(values: FormValues) {
    if (!note) return
    const body: NoteUpdate = {
      title: values.title || null,
      summary: values.summary || null,
      user_notes: values.user_notes || null,
    }
    updateMutation.mutate(
      { id: note.id, body },
      {
        onSuccess: () => {
          toast({ title: 'Note updated', status: 'success', duration: 3000 })
          onClose()
        },
        onError: (err) => {
          const msg = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail || 'Update failed'
          toast({ title: msg, status: 'error', duration: 4000 })
        },
      },
    )
  }

  function handleTogglePin() {
    if (!note) return
    const newPinned = !localPinned
    setLocalPinned(newPinned)
    updateMutation.mutate(
      { id: note.id, body: { pinned: newPinned } },
      {
        onSuccess: () => {
          toast({
            title: newPinned ? 'Pinned' : 'Unpinned',
            status: 'success',
            duration: 2000,
          })
        },
        onError: () => {
          setLocalPinned(!newPinned)
        },
      },
    )
  }

  function handleArchive() {
    if (!note) return
    updateMutation.mutate(
      { id: note.id, body: { status: 'archived' } },
      {
        onSuccess: () => {
          toast({ title: 'Note archived', status: 'success', duration: 3000 })
          onClose()
        },
        onError: (err) => {
          const msg = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail || 'Archive failed'
          toast({ title: msg, status: 'error', duration: 4000 })
        },
      },
    )
  }

  function handleGoToSource() {
    if (note?.source_conversation_id) {
      navigate(`/chat/${note.source_conversation_id}`)
    }
  }

  const isAI = note?.source === 'ai'
  const typeLabel = note?.type ? note.type.charAt(0).toUpperCase() + note.type.slice(1) : ''

  return (
    <Drawer isOpen={isOpen} onClose={onClose} placement="bottom">
      <DrawerOverlay />
      <DrawerContent bg="bg.muted" borderTopRadius="xl" maxH="85vh">
        <DrawerCloseButton color="text.secondary" />
        <DrawerHeader color="text.primary">
          <HStack spacing={2}>
            <Text>{typeLabel}</Text>
            <Text fontSize="xs" color="text.muted" fontWeight="normal">
              {isAI ? 'AI extracted' : 'Manual'}
            </Text>
          </HStack>
        </DrawerHeader>
        <DrawerBody pb={8} overflowY="auto">
          <Box as="form" onSubmit={handleSubmit(onSubmit)}>
            <VStack spacing={4} align="stretch">
              {/* Action bar */}
              <HStack spacing={2}>
                <IconButton
                  aria-label={localPinned ? 'Unpin note' : 'Pin note'}
                  icon={<Pin size={18} fill={localPinned ? 'currentColor' : 'none'} />}
                  variant="ghost"
                  color={localPinned ? 'brand.primary' : 'text.muted'}
                  minH="48px"
                  minW="48px"
                  onClick={handleTogglePin}
                />
                <IconButton
                  aria-label="Archive note"
                  icon={<Archive size={18} />}
                  variant="ghost"
                  color="text.muted"
                  minH="48px"
                  minW="48px"
                  onClick={handleArchive}
                />
                {note?.source_conversation_id && (
                  <Button
                    leftIcon={<ExternalLink size={14} />}
                    variant="ghost"
                    color="accent.blue"
                    size="sm"
                    minH="48px"
                    onClick={handleGoToSource}
                  >
                    Go to Source
                  </Button>
                )}
              </HStack>

              {/* Title */}
              <FormControl>
                <FormLabel fontSize="sm">Title</FormLabel>
                <Controller
                  name="title"
                  control={control}
                  rules={{ required: true, maxLength: 200 }}
                  render={({ field }) => (
                    <Input {...field} size="sm" maxLength={200} />
                  )}
                />
              </FormControl>

              {/* Summary */}
              <FormControl>
                <FormLabel fontSize="sm">Summary</FormLabel>
                <Controller
                  name="summary"
                  control={control}
                  render={({ field }) => (
                    <Textarea
                      {...field}
                      size="sm"
                      rows={3}
                      placeholder="Key details..."
                    />
                  )}
                />
              </FormControl>

              {/* User Notes */}
              <FormControl>
                <FormLabel fontSize="sm">Your Notes</FormLabel>
                <Controller
                  name="user_notes"
                  control={control}
                  render={({ field }) => (
                    <Textarea
                      {...field}
                      size="sm"
                      rows={4}
                      placeholder="Add your own notes..."
                    />
                  )}
                />
              </FormControl>

              {/* Save */}
              <Button
                type="submit"
                colorScheme="brand"
                size="lg"
                width="full"
                isLoading={updateMutation.isPending}
              >
                Save Changes
              </Button>
            </VStack>
          </Box>
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  )
}
