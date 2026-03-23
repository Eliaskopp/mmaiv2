import { Box, Text, VStack } from '@chakra-ui/react'
import { EventCard } from './EventCard'
import type { PerformanceEvent } from '../../types'

interface EventTimelineProps {
  events: PerformanceEvent[]
  isLoading: boolean
}

export function EventTimeline({ events, isLoading }: EventTimelineProps) {
  if (isLoading) return null // parent handles skeleton

  if (events.length === 0) {
    return (
      <Box bg="bg.subtle" p={6} borderRadius="lg" textAlign="center">
        <Text fontSize="sm" color="text.muted">
          Your AI coach extracts training intel from your conversations. Start chatting!
        </Text>
      </Box>
    )
  }

  return (
    <VStack spacing={0} align="stretch">
      {events.map((event, idx) => (
        <Box
          key={event.id}
          position="relative"
          pl={6}
          pb={idx < events.length - 1 ? 4 : 0}
          /* Vertical line — runs from dot to next card */
          _before={
            idx < events.length - 1
              ? {
                  content: '""',
                  position: 'absolute',
                  left: '7px',
                  top: '18px',
                  bottom: 0,
                  width: '2px',
                  bg: 'bg.panel',
                }
              : undefined
          }
          /* Dot */
          _after={{
            content: '""',
            position: 'absolute',
            left: '3px',
            top: '14px',
            width: '10px',
            height: '10px',
            borderRadius: 'full',
            bg: 'text.muted',
          }}
        >
          <EventCard event={event} />
        </Box>
      ))}
    </VStack>
  )
}

// ── Mock data for visual testing (will be removed in M2) ─────────────
export const MOCK_EVENTS: PerformanceEvent[] = [
  {
    id: 'mock-1',
    user_id: 'u1',
    conversation_id: null,
    event_type: 'sparring',
    discipline: 'BJJ',
    outcome: 'loss',
    finish_type: 'rear naked choke',
    root_causes: ['Gave up back from half guard', 'Poor hand-fighting on collar grip'],
    highlights: ['Good guard retention in first 3 minutes'],
    opponent_description: 'Purple belt, ~85kg, pressure passer',
    rpe_score: 8,
    failure_domain: 'technical',
    cns_status: 'sluggish',
    event_date: new Date(Date.now() - 2 * 86_400_000).toISOString(),
    extraction_confidence: 0.87,
    created_at: new Date().toISOString(),
  },
  {
    id: 'mock-2',
    user_id: 'u1',
    conversation_id: null,
    event_type: 'drill',
    discipline: 'Muay Thai',
    outcome: null,
    finish_type: null,
    root_causes: [],
    highlights: ['Teep timing improved', 'Coach noted sharper switch kicks'],
    opponent_description: null,
    rpe_score: 5,
    failure_domain: null,
    cns_status: 'optimal',
    event_date: new Date(Date.now() - 4 * 86_400_000).toISOString(),
    extraction_confidence: 0.92,
    created_at: new Date().toISOString(),
  },
  {
    id: 'mock-3',
    user_id: 'u1',
    conversation_id: null,
    event_type: 'competition',
    discipline: 'MMA',
    outcome: 'win',
    finish_type: 'TKO (ground and pound)',
    root_causes: [],
    highlights: ['Takedown in round 1', 'Controlled top position for 2 minutes'],
    opponent_description: '0-1 amateur, southpaw',
    rpe_score: 9,
    failure_domain: null,
    cns_status: 'depleted',
    event_date: new Date(Date.now() - 7 * 86_400_000).toISOString(),
    extraction_confidence: 0.95,
    created_at: new Date().toISOString(),
  },
]
