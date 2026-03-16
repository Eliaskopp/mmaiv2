import { Box, CircularProgress, Flex, Text } from '@chakra-ui/react'

export function ACWRPlaceholder() {
  return (
    <Box
      bg="bg.subtle"
      p={4}
      borderRadius="lg"
      borderStyle="dashed"
      borderWidth="1px"
      borderColor="bg.panel"
    >
      <Flex align="center" gap={4}>
        <CircularProgress
          value={0}
          size="40px"
          trackColor="bg.muted"
          color="bg.panel"
          thickness="8px"
        />
        <Box>
          <Text fontSize="sm" fontWeight="semibold" color="text.primary">
            Training Load
          </Text>
          <Text fontSize="xs" color="text.muted">
            ACWR analysis coming soon
          </Text>
        </Box>
      </Flex>
    </Box>
  )
}
