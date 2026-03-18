import { Box, Text, useToken } from '@chakra-ui/react'

interface RiskGaugeProps {
  ratio: number | null
  size?: number
}

const MAX_RATIO = 2.0
const CX = 110
const CY = 110
const RADIUS = 90
const STROKE_WIDTH = 18

/** Map a ratio [0, 2.0] to an angle in radians [PI, 0] (left to right) */
function ratioToAngle(ratio: number): number {
  const clamped = Math.max(0, Math.min(ratio, MAX_RATIO))
  return Math.PI * (1 - clamped / MAX_RATIO)
}

/** Get the (x, y) point on the arc for a given angle */
function pointOnArc(angle: number): { x: number; y: number } {
  return {
    x: CX + RADIUS * Math.cos(angle),
    y: CY - RADIUS * Math.sin(angle),
  }
}

/** Build an SVG arc path from startRatio to endRatio */
function arcPath(startRatio: number, endRatio: number): string {
  const startAngle = ratioToAngle(startRatio)
  const endAngle = ratioToAngle(endRatio)
  const start = pointOnArc(startAngle)
  const end = pointOnArc(endAngle)

  // Sweep flag: 1 = clockwise (since we go from higher angle to lower angle)
  // Large arc flag: 0 (each zone is < 180°)
  return `M ${start.x} ${start.y} A ${RADIUS} ${RADIUS} 0 0 1 ${end.x} ${end.y}`
}

export function RiskGauge({ ratio, size = 200 }: RiskGaugeProps) {
  const [accentBlue, green400, orange400, red500] = useToken('colors', [
    'accent.blue', 'green.400', 'orange.400', 'red.500',
  ])

  const ZONES = [
    { from: 0, to: 0.8, color: accentBlue },   // low
    { from: 0.8, to: 1.3, color: green400 },    // optimal
    { from: 1.3, to: 1.5, color: orange400 },   // high
    { from: 1.5, to: 2.0, color: red500 },      // very high
  ]

  const effectiveRatio = ratio ?? 0
  const needleAngle = ratioToAngle(effectiveRatio)
  const needleTip = pointOnArc(needleAngle)

  // Needle base (shorter line from center)
  const needleBaseLen = 20
  const needleBase = {
    x: CX + needleBaseLen * Math.cos(needleAngle),
    y: CY - needleBaseLen * Math.sin(needleAngle),
  }

  return (
    <Box display="flex" flexDirection="column" alignItems="center">
      <svg
        viewBox="0 0 220 130"
        width="100%"
        style={{ maxWidth: size }}
        role="img"
        aria-label={ratio != null ? `ACWR risk gauge: ${ratio.toFixed(2)}` : 'ACWR risk gauge: no data'}
      >
        {/* Zone arcs */}
        {ZONES.map((zone) => (
          <path
            key={zone.from}
            d={arcPath(zone.from, zone.to)}
            fill="none"
            stroke={zone.color}
            strokeWidth={STROKE_WIDTH}
            strokeLinecap="butt"
            opacity={0.85}
          />
        ))}

        {/* Needle line */}
        <line
          x1={needleBase.x}
          y1={needleBase.y}
          x2={needleTip.x}
          y2={needleTip.y}
          stroke={ratio != null ? '#FFFFFF' : 'rgba(255,255,255,0.3)'}
          strokeWidth={2.5}
          strokeLinecap="round"
        />

        {/* Needle tip dot */}
        <circle
          cx={needleTip.x}
          cy={needleTip.y}
          r={4}
          fill={ratio != null ? '#FFFFFF' : 'rgba(255,255,255,0.3)'}
        />

        {/* Center pivot dot */}
        <circle cx={CX} cy={CY} r={5} fill="rgba(255,255,255,0.6)" />

        {/* Ratio text centered in the semi-circle */}
        <text
          x={CX}
          y={CY - 20}
          textAnchor="middle"
          fill="rgba(255,255,255,0.9)"
          fontSize="24"
          fontWeight="bold"
          fontFamily="'JetBrains Mono', 'Fira Code', monospace"
          style={{ fontVariantNumeric: 'tabular-nums' }}
        >
          {ratio != null ? ratio.toFixed(2) : '--'}
        </text>
      </svg>

      {/* Zone labels below the gauge */}
      <Box display="flex" justifyContent="space-between" width="100%" maxW={`${size}px`} px={2} mt={-1}>
        <Text fontSize="2xs" color="text.muted" sx={{ fontVariantNumeric: 'tabular-nums' }}>0</Text>
        <Text fontSize="2xs" color="text.muted" sx={{ fontVariantNumeric: 'tabular-nums' }}>0.8</Text>
        <Text fontSize="2xs" color="text.muted" sx={{ fontVariantNumeric: 'tabular-nums' }}>1.3</Text>
        <Text fontSize="2xs" color="text.muted" sx={{ fontVariantNumeric: 'tabular-nums' }}>2.0</Text>
      </Box>
    </Box>
  )
}
