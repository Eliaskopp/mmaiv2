import { Box, Flex, Text, useToken } from '@chakra-ui/react'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { ChartTooltip } from './ChartTooltip'
import type { DailyVolumePoint } from '../../types'

interface VolumeTrendChartProps {
  data: DailyVolumePoint[]
}

function formatDateTick(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00')
  return `${d.getDate()}/${d.getMonth() + 1}`
}

export function VolumeTrendChart({ data }: VolumeTrendChartProps) {
  const [accentBlue, brandPrimary, textMuted] = useToken('colors', [
    'accent.blue',
    'brand.primary',
    'text.muted',
  ])

  const TICK_STYLE = {
    fill: textMuted,
    fontSize: 11,
    fontVariantNumeric: 'tabular-nums' as const,
  }

  return (
    <Box bg="bg.subtle" p={4} borderRadius="lg">
      {/* Inline legend */}
      <Flex gap={4} mb={3} align="center">
        <Flex align="center" gap={1.5}>
          <Box w="10px" h="10px" borderRadius="sm" bg="accent.blue" opacity={0.6} />
          <Text fontSize="xs" color="text.secondary">
            Duration (min)
          </Text>
        </Flex>
        <Flex align="center" gap={1.5}>
          <Box w="10px" h="3px" borderRadius="full" bg="brand.primary" />
          <Text fontSize="xs" color="text.secondary">
            Exertion Load
          </Text>
        </Flex>
      </Flex>

      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />

          <XAxis
            dataKey="date"
            tickFormatter={formatDateTick}
            tick={TICK_STYLE}
            stroke="transparent"
            interval="preserveStartEnd"
            tickLine={false}
          />

          <YAxis
            yAxisId="duration"
            domain={[0, 'auto']}
            tick={TICK_STYLE}
            width={35}
            stroke="transparent"
            tickLine={false}
            axisLine={false}
          />

          <YAxis
            yAxisId="load"
            orientation="right"
            domain={[0, 'auto']}
            tick={TICK_STYLE}
            width={35}
            stroke="transparent"
            tickLine={false}
            axisLine={false}
          />

          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />

          <Bar
            dataKey="total_duration"
            yAxisId="duration"
            fill={accentBlue}
            fillOpacity={0.6}
            radius={[3, 3, 0, 0]}
            maxBarSize={12}
          />

          <Line
            dataKey="total_load"
            yAxisId="load"
            type="monotone"
            stroke={brandPrimary}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: brandPrimary }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Box>
  )
}
