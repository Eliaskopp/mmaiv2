import { Flex, Image, Text } from '@chakra-ui/react'
import { User } from 'lucide-react'
import { Link } from 'react-router-dom'

interface TopAppBarProps {
  title?: string | null
}

export function TopAppBar({ title }: TopAppBarProps) {
  return (
    <Flex
      as="header"
      position="sticky"
      top="0"
      zIndex="sticky"
      bg="bg.subtle"
      h="56px"
      px={4}
      align="center"
      justify="space-between"
    >
      <Link to="/chat">
        <Image src="/logo.png" alt="MMAi" h="28px" />
      </Link>

      {title && (
        <Text fontSize="sm" color="text.secondary" noOfLines={1} maxW="50%" textAlign="center">
          {title}
        </Text>
      )}

      <Flex
        as={Link}
        to="/profile"
        aria-label="Profile"
        align="center"
        justify="center"
        w="40px"
        h="40px"
        borderRadius="full"
        color="text.secondary"
        _hover={{ color: 'text.primary' }}
        flexShrink={0}
      >
        <User size={22} />
      </Flex>
    </Flex>
  )
}
