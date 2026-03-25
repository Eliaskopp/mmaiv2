import { GridItem, SimpleGrid, Skeleton } from '@chakra-ui/react'
import { TrainingStateHUD } from './TrainingStateHUD'
import { EventTimeline } from './EventTimeline'
import { useTrainingState, usePerformanceEvents } from '../../hooks/use-memory'

export function MemoryPanel() {
  const { data: state, isLoading: stateLoading } = useTrainingState()
  const { data: eventsData, isLoading: eventsLoading } = usePerformanceEvents()

  return (
    <SimpleGrid columns={{ base: 1, lg: 3 }} spacing={4}>
      <GridItem colSpan={1}>
        {stateLoading ? (
          <Skeleton height="200px" borderRadius="lg" />
        ) : (
          <TrainingStateHUD state={state ?? null} isLoading={false} />
        )}
      </GridItem>

      <GridItem colSpan={{ base: 1, lg: 2 }}>
        {eventsLoading ? (
          <Skeleton height="300px" borderRadius="lg" />
        ) : (
          <EventTimeline events={eventsData?.items ?? []} isLoading={false} />
        )}
      </GridItem>
    </SimpleGrid>
  )
}
