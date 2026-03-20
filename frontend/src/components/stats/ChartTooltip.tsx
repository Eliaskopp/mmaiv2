import { Box, Text } from '@chakra-ui/react'
import type { TooltipPayloadEntry } from 'recharts/types/state/tooltipSlice'

interface ChartTooltipProps {
  active?: boolean
  payload?: TooltipPayloadEntry[]
  label?: string | number
}

export function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null

  return (
    <Box
      bg="rgba(15, 30, 53, 0.85)"
      backdropFilter="blur(10px)"
      borderRadius="md"
      border="1px solid"
      borderColor="bg.panel"
      px={3}
      py={2}
      boxShadow="lg"
    >
      <Text fontSize="xs" color="text.secondary" mb={1} sx={{ fontVariantNumeric: 'tabular-nums' }}>
        {label}
      </Text>
      {payload.map((entry) => (
        <Text
          key={String(entry.dataKey)}
          fontSize="sm"
          fontWeight="semibold"
          color={entry.dataKey === 'total_duration' ? 'accent.blue' : 'brand.primary'}
          sx={{ fontVariantNumeric: 'tabular-nums' }}
        >
          {entry.dataKey === 'total_duration'
            ? `${entry.value} min`
            : `Load: ${entry.value}`}
        </Text>
      ))}
    </Box>
  )
}
