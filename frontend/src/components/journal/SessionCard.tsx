import { useRef } from 'react'
import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogOverlay,
  Box,
  Button,
  Flex,
  IconButton,
  Text,
  useDisclosure,
} from '@chakra-ui/react'
import { Trash2 } from 'lucide-react'
import { SESSION_TYPE_MAP, getRPEColor } from './session-utils'
import type { SessionResponse } from '../../types'

interface SessionCardProps {
  session: SessionResponse
  onEdit: (session: SessionResponse) => void
  onDelete: (id: string) => void
}

export function SessionCard({ session, onEdit, onDelete }: SessionCardProps) {
  const { isOpen, onOpen, onClose } = useDisclosure()
  const cancelRef = useRef<HTMLButtonElement>(null)

  const config = SESSION_TYPE_MAP[session.session_type] ?? SESSION_TYPE_MAP.other
  const Icon = config.icon

  const dateLabel = new Date(session.session_date.slice(0, 10) + 'T00:00:00')
    .toLocaleDateString('en-US', { month: 'short', day: 'numeric' })

  const techniqueCount = session.techniques?.length ?? 0

  return (
    <>
      <Box
        bg="bg.subtle"
        borderRadius="lg"
        p={3}
        borderLeft="4px solid"
        borderLeftColor={config.color}
        cursor="pointer"
        onClick={() => onEdit(session)}
        position="relative"
        _hover={{ bg: 'bg.muted' }}
        transition="background 0.15s ease"
      >
        {/* Delete button */}
        <IconButton
          aria-label="Delete session"
          icon={<Trash2 size={14} />}
          size="xs"
          variant="ghost"
          color="text.muted"
          position="absolute"
          top={2}
          right={2}
          onClick={(e) => {
            e.stopPropagation()
            onOpen()
          }}
          _hover={{ color: 'red.400' }}
        />

        {/* Top row */}
        <Flex align="center" gap={2} pr={6}>
          <Box as={Icon} size={16} color={config.color} flexShrink={0} />
          <Text fontSize="sm" fontWeight="semibold" noOfLines={1}>
            {config.label}
          </Text>
          <Flex ml="auto" align="center" gap={3} flexShrink={0}>
            {session.duration_minutes && (
              <Text fontSize="xs" color="text.secondary">
                {session.duration_minutes} min
              </Text>
            )}
            {session.intensity_rpe && (
              <Flex
                align="center"
                justify="center"
                bg={getRPEColor(session.intensity_rpe)}
                color="white"
                borderRadius="full"
                w="22px"
                h="22px"
                fontSize="xs"
                fontWeight="bold"
              >
                {session.intensity_rpe}
              </Flex>
            )}
          </Flex>
        </Flex>

        {/* Bottom row */}
        <Flex align="center" mt={1} gap={2}>
          {techniqueCount > 0 && (
            <Text fontSize="xs" color="text.muted">
              {techniqueCount} technique{techniqueCount !== 1 ? 's' : ''}
            </Text>
          )}
          <Text fontSize="xs" color="text.muted" ml="auto">
            {dateLabel}
          </Text>
        </Flex>
      </Box>

      {/* Delete confirmation */}
      <AlertDialog isOpen={isOpen} leastDestructiveRef={cancelRef} onClose={onClose} isCentered>
        <AlertDialogOverlay>
          <AlertDialogContent bg="bg.subtle" mx={4}>
            <AlertDialogHeader fontSize="lg" fontWeight="bold" color="text.primary">
              Delete session?
            </AlertDialogHeader>
            <AlertDialogBody color="text.secondary">
              This {config.label} session will be permanently removed.
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onClose} variant="ghost" size="sm">
                Cancel
              </Button>
              <Button
                colorScheme="red"
                onClick={() => {
                  onDelete(session.id)
                  onClose()
                }}
                ml={3}
                size="sm"
              >
                Delete
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </>
  )
}
