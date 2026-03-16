import { useState } from 'react'
import type { KeyboardEvent } from 'react'
import {
  HStack,
  IconButton,
  Input,
  Tag,
  TagCloseButton,
  TagLabel,
  Wrap,
  WrapItem,
  VStack,
} from '@chakra-ui/react'
import { Plus } from 'lucide-react'

interface TagInputProps {
  value: string[]
  onChange: (value: string[]) => void
  placeholder?: string
}

export function TagInput({ value, onChange, placeholder }: TagInputProps) {
  const [input, setInput] = useState('')

  function addTag() {
    const trimmed = input.trim()
    if (!trimmed) return
    const isDuplicate = value.some((t) => t.toLowerCase() === trimmed.toLowerCase())
    if (isDuplicate) return
    onChange([...value, trimmed])
    setInput('')
  }

  function removeTag(index: number) {
    onChange(value.filter((_, i) => i !== index))
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      addTag()
    }
  }

  return (
    <VStack align="stretch" spacing={2}>
      <HStack>
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          size="sm"
        />
        <IconButton
          aria-label="Add"
          icon={<Plus size={16} />}
          onClick={addTag}
          size="sm"
          variant="outline"
        />
      </HStack>
      {value.length > 0 && (
        <Wrap spacing={2}>
          {value.map((tag, i) => (
            <WrapItem key={tag}>
              <Tag bg="bg.muted" color="text.primary" size="md">
                <TagLabel>{tag}</TagLabel>
                <TagCloseButton onClick={() => removeTag(i)} />
              </Tag>
            </WrapItem>
          ))}
        </Wrap>
      )}
    </VStack>
  )
}
