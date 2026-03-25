import { Button, Flex, Text, VStack } from '@chakra-ui/react'
import { MessageCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'

interface EmptyChatStateProps {
  onPromptClick: (text: string) => void
}

export function EmptyChatState({ onPromptClick }: EmptyChatStateProps) {
  const { t } = useTranslation()

  const prompts = [
    t('chat.chip1'),
    t('chat.chip2'),
    t('chat.chip3'),
    t('chat.chip4'),
    t('chat.chip5'),
    t('chat.chip6'),
  ]

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
          {t('chat.welcomeTitle')}
        </Text>
        <Text color="text.muted" fontSize="sm" textAlign="center" maxW="280px">
          {t('chat.welcomeSubtitle')}
        </Text>
      </VStack>
      <VStack spacing={3} w="100%" maxW="360px">
        {prompts.map((prompt) => (
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
