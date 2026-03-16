import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Collapse,
  Container,
  Flex,
  HStack,
  Skeleton,
  Text,
  VStack,
} from '@chakra-ui/react'
import { useOutletContext, useSearchParams } from 'react-router-dom'
import { ExertionStatus } from '../components/stats/ExertionStatus'
import { RiskGauge } from '../components/stats/RiskGauge'
import { VolumeTrendChart } from '../components/stats/VolumeTrendChart'
import { useACWR, useVolumeTrends } from '../hooks/use-stats'
import type { LayoutOutletContext } from '../types'

const DAY_OPTIONS = [7, 14, 30] as const

export function StatsPage() {
  const { setPageTitle } = useOutletContext<LayoutOutletContext>()

  useEffect(() => {
    setPageTitle('Stats')
    return () => setPageTitle(null)
  }, [setPageTitle])

  const [searchParams, setSearchParams] = useSearchParams()

  const rawDays = Number(searchParams.get('days'))
  const days = DAY_OPTIONS.includes(rawDays as typeof DAY_OPTIONS[number]) ? rawDays : 30

  function setDays(value: number) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (value === 30) { next.delete('days') } else { next.set('days', String(value)) }
      return next
    }, { replace: true })
  }

  const { data: acwr, isLoading: acwrLoading, isError: acwrError } = useACWR()
  const { data: volume, isLoading: volumeLoading, isError: volumeError } = useVolumeTrends(days)
  const [showChart, setShowChart] = useState(true)

  return (
    <Container maxW="container.md" py={4}>
      <VStack spacing={4} align="stretch">
        {/* ACWR Status Card */}
        {acwrLoading ? (
          <Skeleton height="120px" borderRadius="lg" />
        ) : acwrError ? (
          <Text color="red.400" fontSize="sm">Failed to load training status.</Text>
        ) : acwr ? (
          <ExertionStatus
            riskZone={acwr.risk_zone}
            acwrRatio={acwr.acwr_ratio}
            acuteLoad={acwr.acute_load}
            chronicLoad={acwr.chronic_load}
          />
        ) : null}

        {/* Risk Gauge */}
        {acwrLoading ? (
          <Flex justify="center">
            <Skeleton height="130px" width="200px" borderRadius="lg" />
          </Flex>
        ) : (
          <RiskGauge ratio={acwr?.acwr_ratio ?? null} />
        )}

        {/* Volume Section Toggle + Day Selector */}
        <Flex align="center" justify="space-between">
          <Button
            variant="link"
            size="sm"
            color="text.secondary"
            onClick={() => setShowChart((v) => !v)}
            _hover={{ color: 'text.primary' }}
          >
            {showChart ? 'Hide' : 'Show'} Volume Trends
          </Button>

          {showChart && (
            <HStack spacing={1}>
              {DAY_OPTIONS.map((opt) => (
                <Button
                  key={opt}
                  size="xs"
                  variant={days === opt ? 'solid' : 'outline'}
                  colorScheme={days === opt ? 'brand' : undefined}
                  borderColor={days !== opt ? 'bg.panel' : undefined}
                  color={days !== opt ? 'text.secondary' : undefined}
                  onClick={() => setDays(opt)}
                  minW="40px"
                >
                  {opt}d
                </Button>
              ))}
            </HStack>
          )}
        </Flex>

        {/* Volume Chart */}
        <Collapse in={showChart} animateOpacity>
          {volumeLoading ? (
            <Skeleton height="300px" borderRadius="lg" />
          ) : volumeError ? (
            <Text color="red.400" fontSize="sm">Failed to load volume trends.</Text>
          ) : volume ? (
            <VolumeTrendChart data={volume} />
          ) : null}
        </Collapse>

        {/* Empty state hint */}
        {acwr?.risk_zone === 'insufficient_data' && !acwrLoading && (
          <Box bg="bg.subtle" p={4} borderRadius="lg" textAlign="center">
            <Text fontSize="sm" color="text.muted">
              Log some training sessions to see your stats here.
            </Text>
          </Box>
        )}
      </VStack>
    </Container>
  )
}
