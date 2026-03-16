import { Box, Flex, Text } from '@chakra-ui/react'

const ZONE_CONFIG: Record<string, { label: string; color: string }> = {
  optimal: { label: 'OPTIMAL', color: 'green.500' },
  high: { label: 'HIGH', color: 'orange.400' },
  very_high: { label: 'DANGER', color: 'red.500' },
  low: { label: 'LOW', color: 'accent.blue' },
  insufficient_data: { label: 'NO DATA', color: 'text.muted' },
}

interface ExertionStatusProps {
  riskZone: string
  acwrRatio: number | null
  acuteLoad: number
  chronicLoad: number
}

export function ExertionStatus({ riskZone, acwrRatio, acuteLoad, chronicLoad }: ExertionStatusProps) {
  const zone = ZONE_CONFIG[riskZone] ?? ZONE_CONFIG.insufficient_data

  return (
    <Box bg="bg.subtle" p={5} borderRadius="lg">
      <Flex align="center" justify="space-between" gap={4}>
        <Box>
          <Text fontSize="xs" fontWeight="medium" color="text.muted" textTransform="uppercase" letterSpacing="wider" mb={1}>
            Exertion Status
          </Text>
          <Text fontSize="2xl" fontWeight="bold" color={zone.color} lineHeight="1">
            {zone.label}
          </Text>
        </Box>
        <Box textAlign="right">
          <Text
            fontSize="3xl"
            fontWeight="bold"
            fontFamily="mono"
            color="text.primary"
            lineHeight="1"
            sx={{ fontVariantNumeric: 'tabular-nums' }}
          >
            {acwrRatio != null ? acwrRatio.toFixed(2) : '--'}
          </Text>
          <Text fontSize="xs" color="text.muted" mt={1}>
            ACWR Ratio
          </Text>
        </Box>
      </Flex>

      <Flex mt={3} gap={6}>
        <Box>
          <Text fontSize="xs" color="text.muted">Acute (7d)</Text>
          <Text fontSize="sm" fontWeight="semibold" color="text.secondary" fontFamily="mono" sx={{ fontVariantNumeric: 'tabular-nums' }}>
            {acuteLoad.toFixed(0)}
          </Text>
        </Box>
        <Box>
          <Text fontSize="xs" color="text.muted">Chronic (28d)</Text>
          <Text fontSize="sm" fontWeight="semibold" color="text.secondary" fontFamily="mono" sx={{ fontVariantNumeric: 'tabular-nums' }}>
            {chronicLoad.toFixed(0)}
          </Text>
        </Box>
      </Flex>
    </Box>
  )
}
