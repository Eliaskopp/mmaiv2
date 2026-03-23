import { useState } from 'react'
import {
  Badge,
  Box,
  Collapse,
  Flex,
  List,
  ListItem,
  Text,
} from '@chakra-ui/react'
import type { PerformanceEvent } from '../../types'

/** RPE color scale — matches ACWR semantic token pattern */
function rpeColor(rpe: number | null): string {
  if (rpe == null) return 'gray'
  if (rpe <= 4) return 'green'
  if (rpe <= 7) return 'yellow'
  return 'red'
}

/** Human-readable relative date from ISO string */
function relativeDate(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d ago`
  const weeks = Math.floor(days / 7)
  if (weeks < 5) return `${weeks}w ago`
  const months = Math.floor(days / 30)
  return `${months}mo ago`
}

interface EventCardProps {
  event: PerformanceEvent
}

export function EventCard({ event }: EventCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <Box
      bg="bg.subtle"
      borderRadius="lg"
      px={4}
      py={3}
      cursor="pointer"
      onClick={() => setExpanded((v) => !v)}
      transition="background 0.15s"
      _hover={{ bg: 'bg.muted' }}
    >
      {/* Collapsed summary row */}
      <Flex align="center" justify="space-between" gap={3} wrap="wrap">
        <Flex align="center" gap={2} minW={0}>
          <Text
            fontSize="sm"
            fontWeight="semibold"
            color="text.primary"
            textTransform="capitalize"
          >
            {event.discipline}
          </Text>
          <Text fontSize="sm" color="text.muted">
            {event.event_type.replace(/_/g, ' ')}
          </Text>
        </Flex>

        <Flex align="center" gap={2} flexShrink={0}>
          {event.rpe_score != null && (
            <Badge
              colorScheme={rpeColor(event.rpe_score)}
              fontSize="xs"
              fontFamily="mono"
              variant="subtle"
              px={2}
            >
              RPE {event.rpe_score}
            </Badge>
          )}
          <Text fontSize="xs" color="text.muted" whiteSpace="nowrap">
            {relativeDate(event.event_date)}
          </Text>
        </Flex>
      </Flex>

      {/* Expanded detail */}
      <Collapse in={expanded} animateOpacity>
        <Box pt={3} mt={3} borderTopWidth="1px" borderColor="bg.panel">
          {/* Outcome + Finish Type */}
          {event.outcome && (
            <Flex gap={2} mb={2} align="center">
              <Text fontSize="xs" color="text.muted" textTransform="uppercase" fontWeight="medium">
                Outcome
              </Text>
              <Text fontSize="sm" color="text.secondary" textTransform="capitalize">
                {event.outcome}
              </Text>
              {event.finish_type && (
                <Text fontSize="sm" color="text.muted">
                  — {event.finish_type}
                </Text>
              )}
            </Flex>
          )}

          {/* Root Causes */}
          {event.root_causes.length > 0 && (
            <Box mb={2}>
              <Text fontSize="xs" color="text.muted" textTransform="uppercase" fontWeight="medium" mb={1}>
                Root Causes
              </Text>
              <List spacing={0.5} pl={4} styleType="disc">
                {event.root_causes.map((cause, i) => (
                  <ListItem key={i} fontSize="sm" color="text.secondary">
                    {cause}
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Highlights */}
          {event.highlights.length > 0 && (
            <Box mb={2}>
              <Text fontSize="xs" color="text.muted" textTransform="uppercase" fontWeight="medium" mb={1}>
                Highlights
              </Text>
              <List spacing={0.5} pl={4} styleType="disc">
                {event.highlights.map((h, i) => (
                  <ListItem key={i} fontSize="sm" color="text.secondary">
                    {h}
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Opponent */}
          {event.opponent_description && (
            <Flex gap={2} mb={2} align="baseline">
              <Text fontSize="xs" color="text.muted" textTransform="uppercase" fontWeight="medium">
                Opponent
              </Text>
              <Text fontSize="sm" color="text.secondary">
                {event.opponent_description}
              </Text>
            </Flex>
          )}

          {/* Failure Domain + CNS Status */}
          <Flex gap={4} wrap="wrap" mb={2}>
            {event.failure_domain && (
              <Flex gap={2} align="baseline">
                <Text fontSize="xs" color="text.muted" textTransform="uppercase" fontWeight="medium">
                  Failure
                </Text>
                <Text fontSize="sm" color="text.secondary" textTransform="capitalize">
                  {event.failure_domain}
                </Text>
              </Flex>
            )}
            {event.cns_status && (
              <Flex gap={2} align="baseline">
                <Text fontSize="xs" color="text.muted" textTransform="uppercase" fontWeight="medium">
                  CNS
                </Text>
                <Text fontSize="sm" color="text.secondary" textTransform="capitalize">
                  {event.cns_status}
                </Text>
              </Flex>
            )}
          </Flex>

          {/* Extraction Confidence */}
          <Text fontSize="xs" color="text.muted" mt={1}>
            Confidence: {Math.round(event.extraction_confidence * 100)}%
          </Text>
        </Box>
      </Collapse>
    </Box>
  )
}
