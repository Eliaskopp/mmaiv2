import { IconButton } from '@chakra-ui/react'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronDown } from 'lucide-react'

const MotionIconButton = motion(IconButton)

interface ScrollToBottomButtonProps {
  isVisible: boolean
  onClick: () => void
}

export function ScrollToBottomButton({ isVisible, onClick }: ScrollToBottomButtonProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <MotionIconButton
          aria-label="Scroll to bottom"
          icon={<ChevronDown size={20} />}
          position="fixed"
          bottom="130px"
          left="50%"
          transform="translateX(-50%)"
          zIndex="sticky"
          size="sm"
          borderRadius="full"
          bg="bg.panel"
          color="text.secondary"
          boxShadow="lg"
          _hover={{ bg: 'bg.muted' }}
          onClick={onClick}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.15 }}
        />
      )}
    </AnimatePresence>
  )
}
