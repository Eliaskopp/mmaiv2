import { useState } from 'react'
import { Box, Flex } from '@chakra-ui/react'
import { Outlet } from 'react-router-dom'
import { TopAppBar } from './TopAppBar'
import { BottomNav } from './BottomNav'
import { QuickLogFAB } from './QuickLogFAB'
import type { LayoutOutletContext } from '../../types'

export function RootLayout() {
  const [pageTitle, setPageTitle] = useState<string | null>(null)

  const outletContext: LayoutOutletContext = { setPageTitle }

  return (
    <Flex direction="column" minH="100dvh" bg="bg.canvas">
      <TopAppBar title={pageTitle} />
      <Box as="main" flex="1" overflowY="auto" pb="80px">
        <Outlet context={outletContext} />
      </Box>
      <BottomNav />
      <QuickLogFAB />
    </Flex>
  )
}
