import { Box, Flex, Image, Text } from '@chakra-ui/react'
import { keyframes } from '@emotion/react'

const bounce = keyframes`
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
`

export function TypingIndicator() {
  return (
    <Flex justify="flex-start">
      <Box maxW="85%">
        <Flex align="center" gap={1.5} mb={1}>
          <Image src="/logo-symbol.png" alt="MMAi" w="22px" h="22px" />
          <Text fontSize="xs" color="text.muted" fontWeight="600">
            MMAi Coach
          </Text>
        </Flex>

        <Box bg="bg.subtle" px={4} py={3} borderRadius="2xl" borderBottomLeftRadius="sm">
          <Flex gap={1.5} align="center" h="20px">
            {[0, 1, 2].map((i) => (
              <Box
                key={i}
                w="8px"
                h="8px"
                borderRadius="full"
                bg="text.muted"
                animation={`${bounce} 1.2s ease-in-out infinite`}
                style={{ animationDelay: `${i * 0.2}s` }}
              />
            ))}
          </Flex>
        </Box>
      </Box>
    </Flex>
  )
}
