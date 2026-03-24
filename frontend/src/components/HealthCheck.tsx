import { Badge, HStack, Spinner, Text } from '@chakra-ui/react'
import { useHealth } from '../hooks/use-health'

export function HealthCheck() {
  const { data, isLoading, isError } = useHealth()

  if (isLoading) {
    return (
      <HStack>
        <Spinner size="sm" />
        <Text fontSize="sm">Checking API...</Text>
      </HStack>
    )
  }

  if (isError || !data) {
    return (
      <HStack>
        <Badge colorScheme="red">API Offline</Badge>
      </HStack>
    )
  }

  return (
    <HStack spacing={3}>
      <Badge colorScheme={data.status === 'healthy' ? 'green' : 'red'}>{data.status}</Badge>
      <Badge colorScheme="blue">v{data.version}</Badge>
      <Badge colorScheme={data.database === 'connected' ? 'green' : 'red'}>
        DB: {data.database}
      </Badge>
    </HStack>
  )
}
