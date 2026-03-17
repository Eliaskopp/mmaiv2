import { Flex, Text, VStack } from '@chakra-ui/react'
import { Heart, BarChart3, StickyNote, BookOpen, MessageCircle } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'

interface NavItem {
  icon: LucideIcon
  label: string
  to: string
}

const NAV_ITEMS: NavItem[] = [
  { icon: Heart, label: 'Recovery', to: '/recovery' },
  { icon: BarChart3, label: 'Stats', to: '/stats' },
  { icon: BookOpen, label: 'Journal', to: '/journal' },
  { icon: StickyNote, label: 'Notes', to: '/notes' },
  { icon: MessageCircle, label: 'Chat', to: '/chat' },
]

export function BottomNav() {
  const location = useLocation()

  return (
    <Flex
      as="nav"
      position="fixed"
      bottom="0"
      left="0"
      right="0"
      zIndex="sticky"
      bg="bg.subtle"
      h="64px"
      align="center"
      justify="space-around"
    >
      {NAV_ITEMS.map((item) => {
        const isActive = location.pathname.startsWith(item.to)
        const Icon = item.icon

        return (
          <VStack
            key={item.to}
            as={Link}
            to={item.to}
            spacing={0.5}
            flex="1"
            align="center"
            justify="center"
            h="100%"
            color={isActive ? 'brand.primary' : 'text.secondary'}
            _hover={{ textDecoration: 'none' }}
            role="tab"
            aria-selected={isActive}
          >
            <Icon size={22} />
            <Text fontSize="2xs" fontWeight={isActive ? '600' : '400'}>
              {item.label}
            </Text>
          </VStack>
        )
      })}
    </Flex>
  )
}
