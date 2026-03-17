import { useRef, useState } from 'react'
import { Flex, IconButton, Textarea, useDisclosure } from '@chakra-ui/react'
import { Plus, Send } from 'lucide-react'
import { FloatingActionMenu } from './FloatingActionMenu'

interface ChatInputProps {
  onSend: (content: string) => void
  isDisabled: boolean
  onLogSession?: () => void
  onAttachNote?: () => void
}

export function ChatInput({ onSend, isDisabled, onLogSession, onAttachNote }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const menu = useDisclosure()

  function handleSend() {
    const trimmed = value.trim()
    if (!trimmed || isDisabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
    if (e.key === 'Escape' && menu.isOpen) {
      menu.onClose()
    }
  }

  function handleInput() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 96)}px`
  }

  return (
    <Flex
      position="fixed"
      bottom="64px"
      left={0}
      right={0}
      zIndex="sticky"
      bg="bg.canvas"
      borderTop="1px solid"
      borderColor="bg.panel"
      px={4}
      py={3}
      gap={2}
      align="flex-end"
    >
      <FloatingActionMenu
        isOpen={menu.isOpen}
        onClose={menu.onClose}
        onLogSession={onLogSession ?? (() => {})}
        onAttachNote={onAttachNote ?? (() => {})}
      />
      <IconButton
        aria-label="Attachments"
        icon={<Plus size={20} />}
        variant="ghost"
        color="text.secondary"
        borderRadius="full"
        size="md"
        _hover={{ bg: 'bg.muted' }}
        onClick={menu.onToggle}
      />
      <Textarea
        ref={textareaRef}
        aria-label="Type your message"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        placeholder="Message your coach..."
        rows={1}
        resize="none"
        maxLength={4000}
        bg="bg.subtle"
        borderColor="bg.panel"
        _focus={{ borderColor: 'brand.primary', boxShadow: 'none' }}
        _placeholder={{ color: 'text.muted' }}
        flex={1}
        fontSize="sm"
      />
      <IconButton
        aria-label="Send message"
        icon={<Send size={20} />}
        colorScheme="brand"
        borderRadius="full"
        size="md"
        isDisabled={isDisabled || !value.trim()}
        onClick={handleSend}
      />
    </Flex>
  )
}
