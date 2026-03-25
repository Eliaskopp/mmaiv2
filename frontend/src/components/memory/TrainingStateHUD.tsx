import { Box, Flex, Tag, Text, VStack, Wrap, WrapItem } from '@chakra-ui/react'
import type { TrainingState } from '../../types'

interface TagSectionProps {
  label: string
  items: string[]
  colorScheme: string
}

function TagSection({ label, items, colorScheme }: TagSectionProps) {
  if (items.length === 0) return null

  return (
    <Box>
      <Text
        fontSize="xs"
        fontWeight="medium"
        color="text.muted"
        textTransform="uppercase"
        letterSpacing="wider"
        mb={1.5}
      >
        {label}
      </Text>
      <Wrap spacing={2}>
        {items.map((item) => (
          <WrapItem key={item}>
            <Tag
              size="sm"
              colorScheme={colorScheme}
              variant="subtle"
              borderRadius="full"
              px={3}
              fontSize="xs"
            >
              {item}
            </Tag>
          </WrapItem>
        ))}
      </Wrap>
    </Box>
  )
}

interface TrainingStateHUDProps {
  state: TrainingState | null
  isLoading: boolean
}

export function TrainingStateHUD({ state, isLoading }: TrainingStateHUDProps) {
  if (isLoading) return null // parent handles skeleton

  const isEmpty =
    !state ||
    (state.current_focus.length === 0 &&
      state.active_injuries.length === 0 &&
      state.short_term_goals.length === 0)

  if (isEmpty) {
    return (
      <Box bg="bg.subtle" p={6} borderRadius="lg" textAlign="center">
        <Text fontSize="sm" color="text.muted">
          Chat with your coach to build your training profile
        </Text>
      </Box>
    )
  }

  return (
    <Box bg="bg.subtle" p={5} borderRadius="lg">
      <Flex align="center" mb={4}>
        <Text
          fontSize="xs"
          fontWeight="medium"
          color="text.muted"
          textTransform="uppercase"
          letterSpacing="wider"
        >
          Training State
        </Text>
      </Flex>

      <VStack spacing={4} align="stretch">
        <TagSection label="Focus" items={state.current_focus} colorScheme="blue" />
        <TagSection label="Injuries" items={state.active_injuries} colorScheme="red" />
        <TagSection label="Goals" items={state.short_term_goals} colorScheme="green" />
      </VStack>
    </Box>
  )
}
