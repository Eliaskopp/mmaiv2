import { useCallback, useRef, useState } from 'react'
import { Flex, IconButton, Textarea, useDisclosure } from '@chakra-ui/react'
import { keyframes } from '@emotion/react'
import { Mic, Plus, Send } from 'lucide-react'
import { FloatingActionMenu } from './FloatingActionMenu'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'

const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(232, 81, 45, 0.5); }
  70% { box-shadow: 0 0 0 8px rgba(232, 81, 45, 0); }
  100% { box-shadow: 0 0 0 0 rgba(232, 81, 45, 0); }
`

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

  const handleTranscriptComplete = useCallback((transcript: string) => {
    setValue((prev) => {
      const spacer = prev && !prev.endsWith(' ') ? ' ' : ''
      return prev + spacer + transcript
    })
  }, [])

  const speech = useSpeechRecognition({ onTranscriptComplete: handleTranscriptComplete })

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
      {speech.isSupported && (
        <IconButton
          aria-label={speech.isListening ? 'Stop listening' : 'Voice input'}
          icon={<Mic size={20} />}
          variant="ghost"
          color={speech.isListening ? 'brand.primary' : 'text.secondary'}
          borderRadius="full"
          size="md"
          _hover={{ bg: 'bg.muted' }}
          onClick={speech.isListening ? speech.stopListening : speech.startListening}
          animation={speech.isListening ? `${pulse} 1.5s infinite` : undefined}
        />
      )}
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
