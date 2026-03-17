import { useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  HStack,
  IconButton,
  Slider,
  SliderFilledTrack,
  SliderThumb,
  SliderTrack,
  Text,
  Textarea,
  VStack,
  useToast,
} from '@chakra-ui/react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useOutletContext, useSearchParams } from 'react-router-dom'
import { ChoiceChipGroup } from '../components/ChoiceChipGroup'
import { useRecoveryLog, useUpsertRecoveryLog } from '../hooks/use-recovery'
import type { LayoutOutletContext, RecoveryLogCreate } from '../types'
import type { AxiosError } from 'axios'

/* ── helpers ─────────────────────────────────────────────── */

function todayISO(): string {
  return new Date().toISOString().slice(0, 10)
}

function shiftDate(dateStr: string, days: number): string {
  const d = new Date(dateStr + 'T12:00:00') // noon avoids DST edge
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00')
  const weekday = d.toLocaleDateString('en-AU', { weekday: 'short' })
  const day = d.getDate()
  const month = d.toLocaleDateString('en-AU', { month: 'short' })
  const label = `${weekday}, ${day} ${month}`
  return dateStr === todayISO() ? `${label} (Today)` : label
}

const SLEEP_LABELS: Record<number, string> = {
  1: 'Terrible',
  2: 'Poor',
  3: 'Okay',
  4: 'Good',
  5: 'Great',
}

const SLEEP_COLORS: Record<number, string> = {
  1: 'red.400',
  2: 'orange.400',
  3: 'yellow.400',
  4: 'green.300',
  5: 'green.400',
}

const SORENESS_OPTIONS = [
  { value: '1', label: 'None' },
  { value: '2', label: 'Mild' },
  { value: '3', label: 'Moderate' },
  { value: '4', label: 'Sore' },
  { value: '5', label: 'Severe' },
]

const ENERGY_OPTIONS = [
  { value: '1', label: 'Drained' },
  { value: '2', label: 'Low' },
  { value: '3', label: 'Normal' },
  { value: '4', label: 'Good' },
  { value: '5', label: 'Energized' },
]

/* ── form values ─────────────────────────────────────────── */

interface FormValues {
  sleep_quality: number
  soreness: string | null
  energy: string | null
  notes: string
}

const DEFAULTS: FormValues = {
  sleep_quality: 3,
  soreness: null,
  energy: null,
  notes: '',
}

/* ── page component ──────────────────────────────────────── */

export function RecoveryPage() {
  const { setPageTitle } = useOutletContext<LayoutOutletContext>()
  const toast = useToast()
  const [searchParams, setSearchParams] = useSearchParams()

  const selectedDate = searchParams.get('date') || todayISO()

  function setSelectedDate(next: string | ((prev: string) => string)) {
    setSearchParams((prev) => {
      const current = prev.get('date') || todayISO()
      const value = typeof next === 'function' ? next(current) : next
      const params = new URLSearchParams(prev)
      if (value === todayISO()) { params.delete('date') } else { params.set('date', value) }
      return params
    }, { replace: true })
  }

  useEffect(() => {
    setPageTitle('Recovery')
    return () => setPageTitle(null)
  }, [setPageTitle])

  const { data: existingLog, error, isError } = useRecoveryLog(selectedDate)
  const upsertMutation = useUpsertRecoveryLog()

  const is404 = isError && (error as AxiosError)?.response?.status === 404
  const isRealError = isError && !is404
  const isEditing = !!existingLog && !is404

  const { control, handleSubmit, reset } = useForm<FormValues>({
    defaultValues: DEFAULTS,
  })

  // Reset form when existing log loads or date changes to a 404
  useEffect(() => {
    if (existingLog) {
      reset({
        sleep_quality: existingLog.sleep_quality ?? 3,
        soreness: existingLog.soreness?.toString() ?? null,
        energy: existingLog.energy?.toString() ?? null,
        notes: existingLog.notes ?? '',
      })
    } else if (is404 || !isError) {
      reset(DEFAULTS)
    }
  }, [existingLog, is404, isError, reset])

  function onSubmit(values: FormValues) {
    const body: RecoveryLogCreate = {
      sleep_quality: values.sleep_quality,
      soreness: values.soreness ? Number(values.soreness) : null,
      energy: values.energy ? Number(values.energy) : null,
      notes: values.notes || null,
      logged_for: selectedDate,
    }
    upsertMutation.mutate(body, {
      onSuccess: () => {
        toast({
          title: isEditing ? 'Recovery log updated' : 'Recovery log saved',
          status: 'success',
          duration: 3000,
        })
      },
      onError: (err) => {
        const msg = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail || 'Save failed'
        toast({ title: msg, status: 'error', duration: 4000 })
      },
    })
  }

  return (
    <Container maxW="container.md" py={4}>
      <VStack spacing={4} align="stretch">
        {/* Date Switcher */}
        <HStack justify="center" spacing={3}>
          <IconButton
            aria-label="Previous day"
            icon={<ChevronLeft size={20} />}
            variant="ghost"
            size="sm"
            onClick={() => setSelectedDate((d) => shiftDate(d, -1))}
          />
          <Text fontWeight="semibold" color="text.primary" minW="160px" textAlign="center">
            {formatDateLabel(selectedDate)}
          </Text>
          <IconButton
            aria-label="Next day"
            icon={<ChevronRight size={20} />}
            variant="ghost"
            size="sm"
            isDisabled={selectedDate === todayISO()}
            onClick={() => setSelectedDate((d) => shiftDate(d, 1))}
          />
        </HStack>

        {isRealError && (
          <Text color="red.400" textAlign="center">
            Failed to load recovery log.
          </Text>
        )}

        {/* Wellness Survey Card */}
        <Box
          as="form"
          onSubmit={handleSubmit(onSubmit)}
          bg="bg.subtle"
          p={5}
          borderRadius="lg"
        >
          <VStack spacing={5} align="stretch">
            {/* Sleep Quality — Slider */}
            <FormControl>
              <FormLabel fontSize="sm">Sleep Quality</FormLabel>
              <Controller
                name="sleep_quality"
                control={control}
                render={({ field }) => (
                  <Box px={2}>
                    <Slider
                      min={1}
                      max={5}
                      step={1}
                      value={field.value}
                      onChange={field.onChange}
                      aria-label="Sleep Quality"
                      aria-valuetext={SLEEP_LABELS[field.value]}
                    >
                      <SliderTrack>
                        <SliderFilledTrack bg={SLEEP_COLORS[field.value]} />
                      </SliderTrack>
                      <SliderThumb boxSize={6} />
                    </Slider>
                    <Text fontSize="sm" color="text.secondary" mt={1} textAlign="center">
                      {field.value} — {SLEEP_LABELS[field.value]}
                    </Text>
                  </Box>
                )}
              />
            </FormControl>

            {/* Soreness — ChoiceChipGroup */}
            <FormControl>
              <FormLabel fontSize="sm">Soreness</FormLabel>
              <Controller
                name="soreness"
                control={control}
                render={({ field }) => (
                  <ChoiceChipGroup
                    options={SORENESS_OPTIONS}
                    value={field.value}
                    onChange={field.onChange}
                    columns={5}
                  />
                )}
              />
            </FormControl>

            {/* Energy — ChoiceChipGroup */}
            <FormControl>
              <FormLabel fontSize="sm">Energy</FormLabel>
              <Controller
                name="energy"
                control={control}
                render={({ field }) => (
                  <ChoiceChipGroup
                    options={ENERGY_OPTIONS}
                    value={field.value}
                    onChange={field.onChange}
                    columns={5}
                  />
                )}
              />
            </FormControl>

            {/* Notes — Textarea */}
            <FormControl>
              <FormLabel fontSize="sm">Notes</FormLabel>
              <Controller
                name="notes"
                control={control}
                render={({ field }) => (
                  <Textarea
                    {...field}
                    placeholder="How are you feeling today?"
                    maxLength={2000}
                    size="sm"
                    rows={3}
                  />
                )}
              />
            </FormControl>

            {/* Save Button */}
            <Button
              type="submit"
              colorScheme="brand"
              size="lg"
              width="full"
              isLoading={upsertMutation.isPending}
            >
              {isEditing ? 'Update Log' : 'Save Log'}
            </Button>
          </VStack>
        </Box>
      </VStack>
    </Container>
  )
}
