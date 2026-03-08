import { ChakraProvider, Container, Heading, VStack } from '@chakra-ui/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HealthCheck } from './components/HealthCheck'

const queryClient = new QueryClient()

function App() {
  return (
    <ChakraProvider>
      <QueryClientProvider client={queryClient}>
        <Container maxW="container.md" py={10}>
          <VStack spacing={6}>
            <Heading>MMAi V2</Heading>
            <HealthCheck />
          </VStack>
        </Container>
      </QueryClientProvider>
    </ChakraProvider>
  )
}

export default App
