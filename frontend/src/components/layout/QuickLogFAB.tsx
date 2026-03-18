import { useRef } from 'react'
import {
  Box,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  useDisclosure,
} from '@chakra-ui/react'
import { motion } from 'framer-motion'
import { Plus } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { SessionForm } from '../journal/SessionForm'

const MotionBox = motion(Box)

export function QuickLogFAB() {
  const location = useLocation()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const btnRef = useRef<HTMLDivElement>(null)

  if (location.pathname.startsWith('/chat')) return null

  return (
    <>
      <MotionBox
        ref={btnRef}
        position="fixed"
        bottom="80px"
        right="20px"
        zIndex="overlay"
        w="56px"
        h="56px"
        borderRadius="full"
        bg="brand.primary"
        color="white"
        display="flex"
        alignItems="center"
        justifyContent="center"
        cursor="pointer"
        boxShadow="0 4px 12px rgba(255, 107, 53, 0.4)"
        onClick={onOpen}
        whileTap={{ scale: 0.95 }}
        aria-label="Quick log"
        role="button"
      >
        <Plus size={26} />
      </MotionBox>

      <Drawer
        isOpen={isOpen}
        onClose={onClose}
        placement="bottom"
        finalFocusRef={btnRef}
      >
        <DrawerOverlay />
        <DrawerContent bg="bg.muted" borderTopRadius="xl" maxH="50vh">
          <DrawerCloseButton color="text.secondary" />
          <DrawerHeader color="text.primary">Quick Log</DrawerHeader>
          <DrawerBody pb={8} overflowY="auto">
            <SessionForm mode="quick" onSuccess={onClose} />
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </>
  )
}
