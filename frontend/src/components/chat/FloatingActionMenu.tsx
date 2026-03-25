import { Box, Flex, Text } from '@chakra-ui/react'
import { AnimatePresence, motion } from 'framer-motion'
import { Dumbbell, StickyNote } from 'lucide-react'

const MotionBox = motion(Box)

interface FloatingActionMenuProps {
  isOpen: boolean
  onClose: () => void
  onLogSession: () => void
  onAttachNote: () => void
}

interface MenuItemProps {
  icon: React.ReactNode
  label: string
  onClick: () => void
}

function MenuItem({ icon, label, onClick }: MenuItemProps) {
  return (
    <Flex
      align="center"
      gap={3}
      px={4}
      py={2.5}
      cursor="pointer"
      borderRadius="lg"
      _hover={{ bg: 'bg.muted' }}
      transition="background 0.15s"
      onClick={onClick}
    >
      <Flex
        align="center"
        justify="center"
        w="32px"
        h="32px"
        borderRadius="lg"
        bg="brand.subtle"
        color="brand.primary"
        flexShrink={0}
      >
        {icon}
      </Flex>
      <Text fontSize="sm" fontWeight="medium" color="text.primary">
        {label}
      </Text>
    </Flex>
  )
}

export function FloatingActionMenu({
  isOpen,
  onClose,
  onLogSession,
  onAttachNote,
}: FloatingActionMenuProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <Box position="fixed" inset={0} zIndex="popover" onClick={onClose} />
          {/* Menu */}
          <MotionBox
            position="absolute"
            bottom="calc(100% + 8px)"
            left="0"
            zIndex="popover"
            bg="rgba(15, 30, 53, 0.85)"
            backdropFilter="blur(10px)"
            borderRadius="xl"
            border="1px solid"
            borderColor="bg.panel"
            py={2}
            minW="200px"
            boxShadow="dark-lg"
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.15 }}
          >
            <MenuItem
              icon={<Dumbbell size={16} color="currentColor" />}
              label="Log Session"
              onClick={() => {
                onClose()
                onLogSession()
              }}
            />
            <MenuItem
              icon={<StickyNote size={16} color="currentColor" />}
              label="Attach Note"
              onClick={() => {
                onClose()
                onAttachNote()
              }}
            />
          </MotionBox>
        </>
      )}
    </AnimatePresence>
  )
}
