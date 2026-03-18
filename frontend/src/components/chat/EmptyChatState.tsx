import { Button, Flex, Text, VStack } from '@chakra-ui/react'
import { MessageCircle } from 'lucide-react'

const SUGGESTED_PROMPTS = [
  'How does the ACWR score calculate my injury risk?',
  'What should I log in my daily journal?',
  'How do you use my profile data to coach me?',
]

interface EmptyChatStateProps {
  onPromptClick: (text: string) => void
}

export function EmptyChatState({ onPromptClick }: EmptyChatStateProps) {
  return (
    <VStack spacing={6} flex={1} justify="center" align="center" py={20} px={6}>
      <Flex
        align="center"
        justify="center"
        w="64px"
        h="64px"
        borderRadius="full"
        bg="brand.subtle"
        color="brand.primary"
      >
        <MessageCircle size={32} color="currentColor" />
      </Flex>
      <VStack spacing={1}>
        <Text color="text.primary" fontSize="lg" fontWeight="semibold">
          Welcome to your AI Coach
        </Text>
        <Text color="text.muted" fontSize="sm" textAlign="center" maxW="280px">
          Ask anything about training, or try one of these:
        </Text>
      </VStack>
      <VStack spacing={3} w="100%" maxW="360px">
        {SUGGESTED_PROMPTS.map((prompt) => (
          <Button
            key={prompt}
            variant="outline"
            size="sm"
            w="100%"
            whiteSpace="normal"
            textAlign="left"
            h="auto"
            py={3}
            px={4}
            fontWeight="normal"
            fontSize="sm"
            color="text.secondary"
            borderColor="bg.panel"
            _hover={{ bg: 'bg.muted', borderColor: 'brand.primary' }}
            onClick={() => onPromptClick(prompt)}
          >
            {prompt}
          </Button>
        ))}
      </VStack>
    </VStack>
  )
}
