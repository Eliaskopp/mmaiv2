import {
  Box,
  Button,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Flex,
  Link,
  Tag,
  Text,
} from '@chakra-ui/react'
import { ExternalLink } from 'lucide-react'
import type { Citation } from './CitationBadge'

const TYPE_LABELS: Record<Citation['type'], string> = {
  web: 'Web Source',
  session: 'Training Session',
  note: 'Note',
  recovery: 'Recovery Log',
}

const TYPE_COLORS: Record<Citation['type'], string> = {
  web: 'blue',
  session: 'orange',
  note: 'purple',
  recovery: 'green',
}

interface CitationDrawerProps {
  citation: Citation | null
  isOpen: boolean
  onClose: () => void
}

export function CitationDrawer({ citation, isOpen, onClose }: CitationDrawerProps) {
  if (!citation) return null

  return (
    <Drawer isOpen={isOpen} onClose={onClose} placement="bottom">
      <DrawerOverlay />
      <DrawerContent bg="bg.muted" borderTopRadius="xl" maxH="60vh">
        <DrawerCloseButton color="text.secondary" />
        <DrawerHeader pb={2}>
          <Flex align="center" gap={2}>
            <Text color="text.primary" fontSize="md">
              {citation.title}
            </Text>
            <Tag size="sm" colorScheme={TYPE_COLORS[citation.type]}>
              {TYPE_LABELS[citation.type]}
            </Tag>
          </Flex>
        </DrawerHeader>
        <DrawerBody pb={8}>
          {citation.snippet && (
            <Box
              bg="bg.subtle"
              p={4}
              borderRadius="md"
              mb={4}
              borderLeft="3px solid"
              borderColor="brand.primary"
            >
              <Text fontSize="sm" color="text.secondary" lineHeight="tall">
                {citation.snippet}
              </Text>
            </Box>
          )}

          {citation.url && (
            <Button
              as={Link}
              href={citation.url}
              isExternal
              size="sm"
              variant="outline"
              leftIcon={<ExternalLink size={14} />}
              colorScheme="brand"
            >
              Open Source
            </Button>
          )}

          {!citation.snippet && !citation.url && (
            <Text fontSize="sm" color="text.muted">
              No additional details available.
            </Text>
          )}
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  )
}
