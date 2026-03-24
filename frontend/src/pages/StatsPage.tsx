import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Collapse,
  Container,
  Flex,
  HStack,
  Progress,
  Skeleton,
  Text,
  VStack,
} from '@chakra-ui/react'
import { useOutletContext, useSearchParams } from 'react-router-dom'
import { ExertionStatus } from '../components/stats/ExertionStatus'
import { RiskGauge } from '../components/stats/RiskGauge'
import { VolumeTrendChart } from '../components/stats/VolumeTrendChart'
import { MemoryPanel } from '../components/memory/MemoryPanel'
import { useACWR, useVolumeTrends } from '../hooks/use-stats'
import type { LayoutOutletContext } from '../types'

const DAY_OPTIONS = [7, 14, 30] as const
const TABS = ['volume', 'intelligence'] as const
type Tab = (typeof TABS)[number]

export function StatsPage() {
  const { setPageTitle } = useOutletContext<LayoutOutletContext>()

  useEffect(() => {
    setPageTitle('Stats')
    return () => setPageTitle(null)
  }, [setPageTitle])

  const [searchParams, setSearchParams] = useSearchParams()

  // ── Tab state from URL ─────────────────────────────────────────────
  const rawTab = searchParams.get('tab')
  const activeTab: Tab = TABS.includes(rawTab as Tab) ? (rawTab as Tab) : 'intelligence'

  function setTab(tab: Tab) {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (tab === 'intelligence') {
          next.delete('tab')
        } else {
          next.set('tab', tab)
        }
        return next
      },
      { replace: true },
    )
  }

  // ── Volume-specific state ──────────────────────────────────────────
  const rawDays = Number(searchParams.get('days'))
  const days = DAY_OPTIONS.includes(rawDays as (typeof DAY_OPTIONS)[number]) ? rawDays : 30

  function setDays(value: number) {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (value === 30) {
          next.delete('days')
        } else {
          next.set('days', String(value))
        }
        return next
      },
      { replace: true },
    )
  }

  const { data: acwr, isLoading: acwrLoading, isError: acwrError } = useACWR()
  const { data: volume, isLoading: volumeLoading, isError: volumeError } = useVolumeTrends(days)
  const [showChart, setShowChart] = useState(true)

  return (
    <Container maxW="container.md" py={4}>
      <VStack spacing={4} align="stretch">
        {/* Tab bar */}
        <HStack spacing={1} bg="bg.subtle" p={1} borderRadius="lg">
          {TABS.map((tab) => (
            <Button
              key={tab}
              size="sm"
              flex={1}
              variant={activeTab === tab ? 'solid' : 'ghost'}
              colorScheme={activeTab === tab ? 'brand' : undefined}
              color={activeTab !== tab ? 'text.secondary' : undefined}
              onClick={() => setTab(tab)}
              textTransform="capitalize"
              fontWeight="medium"
              minH="36px"
            >
              {tab}
            </Button>
          ))}
        </HStack>

        {/* Volume tab */}
        {activeTab === 'volume' && (
          <>
            {/* ACWR Status Card */}
            {acwrLoading ? (
              <Skeleton height="120px" borderRadius="lg" />
            ) : acwrError ? (
              <Text color="red.400" fontSize="sm">
                Failed to load training status.
              </Text>
            ) : acwr ? (
              <ExertionStatus
                riskZone={acwr.risk_zone}
                acwrRatio={acwr.acwr_ratio}
                acuteLoad={acwr.acute_load}
                chronicLoad={acwr.chronic_load}
                isCalibrating={acwr.is_calibrating}
              />
            ) : null}

            {/* Risk Gauge / Calibration Bar */}
            {acwrLoading ? (
              <Flex justify="center">
                <Skeleton height="130px" width="200px" borderRadius="lg" />
              </Flex>
            ) : acwr?.is_calibrating || acwr?.risk_zone === 'insufficient_data' ? (
              <Box bg="bg.subtle" p={4} borderRadius="lg">
                <Progress
                  value={Math.min(((acwr?.session_count ?? 0) / 4) * 100, 100)}
                  size="sm"
                  colorScheme="brand"
                  borderRadius="full"
                  bg="whiteAlpha.100"
                  mb={2}
                />
                <Text
                  textTransform="uppercase"
                  fontSize="xs"
                  color="text.muted"
                  letterSpacing="wide"
                  textAlign="center"
                >
                  <Text as="span" fontWeight="bold" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                    {acwr?.session_count ?? 0} / 4
                  </Text>{' '}
                  sessions logged
                </Text>
              </Box>
            ) : (
              <RiskGauge ratio={acwr?.acwr_ratio ?? null} isCalibrating={false} />
            )}

            {/* Volume Section Toggle + Day Selector */}
            <Flex align="center" justify="space-between">
              <Button
                variant="ghost"
                size="sm"
                minH="44px"
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
                <Text color="red.400" fontSize="sm">
                  Failed to load volume trends.
                </Text>
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
          </>
        )}

        {/* Intelligence tab */}
        {activeTab === 'intelligence' && <MemoryPanel />}
      </VStack>
    </Container>
  )
}
