import { useCallback, useEffect } from 'react'
import { useForm, useWatch, Controller } from 'react-hook-form'
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  IconButton,
  Input,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  SimpleGrid,
  Textarea,
  VStack,
  useToast,
} from '@chakra-ui/react'
import { keyframes } from '@emotion/react'
import { Mic } from 'lucide-react'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import { ChoiceChipGroup } from '../ChoiceChipGroup'
import { TagInput } from '../TagInput'
import { RPEPicker } from './RPEPicker'
import { SESSION_TYPE_OPTIONS } from './session-utils'
import { useCreateJournalSession, useUpdateJournalSession } from '../../hooks/use-journal'
import type { SessionCreate, SessionUpdate, SessionResponse, SessionType } from '../../types'
import type { AxiosError } from 'axios'

const MOOD_OPTIONS = [
  { value: '1', label: 'Awful' },
  { value: '2', label: 'Low' },
  { value: '3', label: 'Okay' },
  { value: '4', label: 'Good' },
  { value: '5', label: 'Great' },
]

const ENERGY_OPTIONS = [
  { value: '1', label: 'Drained' },
  { value: '2', label: 'Low' },
  { value: '3', label: 'Normal' },
  { value: '4', label: 'Good' },
  { value: '5', label: 'Energized' },
]

const DURATION_PRESETS = [
  { value: '30', label: '30m' },
  { value: '45', label: '45m' },
  { value: '60', label: '60m' },
  { value: '90', label: '90m' },
  { value: '120', label: '2h' },
]

interface FormValues {
  session_type: string
  duration_minutes: string
  intensity_rpe: number | null
  title: string
  session_date: string
  rounds: string
  round_duration_minutes: string
  mood_before: string | null
  mood_after: string | null
  energy_level: string | null
  techniques: string[]
  training_partner: string
  gym_name: string
  notes: string
}

interface SessionFormProps {
  mode: 'quick' | 'full'
  editingSession?: SessionResponse
  onSuccess: () => void
  onCancel?: () => void
}

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

function getDefaults(): FormValues {
  return {
    session_type: '',
    duration_minutes: '',
    intensity_rpe: null,
    title: '',
    session_date: todayISO(),
    rounds: '',
    round_duration_minutes: '',
    mood_before: null,
    mood_after: null,
    energy_level: null,
    techniques: [],
    training_partner: '',
    gym_name: '',
    notes: '',
  }
}

const micPulse = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(232, 81, 45, 0.5); }
  70% { box-shadow: 0 0 0 8px rgba(232, 81, 45, 0); }
  100% { box-shadow: 0 0 0 0 rgba(232, 81, 45, 0); }
`

export function SessionForm({ mode, editingSession, onSuccess, onCancel }: SessionFormProps) {
  const toast = useToast()
  const createMutation = useCreateJournalSession()
  const updateMutation = useUpdateJournalSession()
  const isEditing = !!editingSession

  const { control, handleSubmit, reset, getValues, setValue: setFormValue, formState: { errors } } = useForm<FormValues>({
    defaultValues: getDefaults(),
  })

  const durationValue = useWatch({ control, name: 'duration_minutes' })

  const handleTranscriptComplete = useCallback((transcript: string) => {
    const current = getValues('notes')
    const spacer = current && !current.endsWith(' ') ? ' ' : ''
    setFormValue('notes', current + spacer + transcript)
  }, [getValues, setFormValue])

  const speech = useSpeechRecognition({ onTranscriptComplete: handleTranscriptComplete })

  useEffect(() => {
    if (editingSession) {
      reset({
        session_type: editingSession.session_type,
        duration_minutes: editingSession.duration_minutes?.toString() ?? '',
        intensity_rpe: editingSession.intensity_rpe,
        title: editingSession.title ?? '',
        session_date: editingSession.session_date.slice(0, 10),
        rounds: editingSession.rounds?.toString() ?? '',
        round_duration_minutes: editingSession.round_duration_minutes?.toString() ?? '',
        mood_before: editingSession.mood_before?.toString() ?? null,
        mood_after: editingSession.mood_after?.toString() ?? null,
        energy_level: editingSession.energy_level?.toString() ?? null,
        techniques: editingSession.techniques ?? [],
        training_partner: editingSession.training_partner ?? '',
        gym_name: editingSession.gym_name ?? '',
        notes: editingSession.notes ?? '',
      })
    } else {
      reset(getDefaults())
    }
  }, [editingSession, reset])

  function onSubmit(values: FormValues) {
    if (!values.session_type) return

    if (isEditing) {
      const body: SessionUpdate = {
        session_type: values.session_type as SessionType,
        session_date: values.session_date || null,
        title: values.title || null,
        notes: values.notes || null,
        duration_minutes: values.duration_minutes ? Number(values.duration_minutes) : null,
        rounds: values.rounds ? Number(values.rounds) : null,
        round_duration_minutes: values.round_duration_minutes ? Number(values.round_duration_minutes) : null,
        intensity_rpe: values.intensity_rpe,
        mood_before: values.mood_before ? Number(values.mood_before) : null,
        mood_after: values.mood_after ? Number(values.mood_after) : null,
        energy_level: values.energy_level ? Number(values.energy_level) : null,
        techniques: values.techniques.length ? values.techniques : null,
        training_partner: values.training_partner || null,
        gym_name: values.gym_name || null,
        source: 'manual',
      }
      updateMutation.mutate({ id: editingSession!.id, body }, {
        onSuccess: () => {
          toast({ title: 'Session updated', status: 'success', duration: 3000 })
          onSuccess()
        },
        onError: (err) => {
          const msg = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail || 'Update failed'
          toast({ title: msg, status: 'error', duration: 4000 })
        },
      })
    } else {
      const body: SessionCreate = {
        session_type: values.session_type as SessionType,
        session_date: values.session_date || null,
        title: values.title || null,
        notes: values.notes || null,
        duration_minutes: values.duration_minutes ? Number(values.duration_minutes) : null,
        rounds: values.rounds ? Number(values.rounds) : null,
        round_duration_minutes: values.round_duration_minutes ? Number(values.round_duration_minutes) : null,
        intensity_rpe: values.intensity_rpe,
        mood_before: values.mood_before ? Number(values.mood_before) : null,
        mood_after: values.mood_after ? Number(values.mood_after) : null,
        energy_level: values.energy_level ? Number(values.energy_level) : null,
        techniques: values.techniques.length ? values.techniques : null,
        training_partner: values.training_partner || null,
        gym_name: values.gym_name || null,
        source: 'manual',
      }
      createMutation.mutate(body, {
        onSuccess: () => {
          toast({ title: 'Session logged', status: 'success', duration: 3000 })
          reset(getDefaults())
          onSuccess()
        },
        onError: (err) => {
          const msg = (err as AxiosError<{ detail?: string }>)?.response?.data?.detail || 'Log failed'
          toast({ title: msg, status: 'error', duration: 4000 })
        },
      })
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <Box as="form" onSubmit={handleSubmit(onSubmit)}>
      <VStack spacing={4} align="stretch">
        {/* Session Type — required */}
        <FormControl isInvalid={!!errors.session_type}>
          <FormLabel fontSize="sm">Type</FormLabel>
          <Controller
            name="session_type"
            control={control}
            rules={{ required: 'Select a session type' }}
            render={({ field }) => (
              <ChoiceChipGroup
                options={SESSION_TYPE_OPTIONS}
                value={field.value || null}
                onChange={field.onChange}
                columns={3}
              />
            )}
          />
        </FormControl>

        {/* Duration */}
        <FormControl>
          <FormLabel fontSize="sm">Duration (min)</FormLabel>
          <SimpleGrid columns={5} spacing={2} mb={2}>
            {DURATION_PRESETS.map((preset) => {
              const isActive = durationValue === preset.value
              return (
                <Button
                  key={preset.value}
                  variant={isActive ? 'solid' : 'outline'}
                  bg={isActive ? 'brand.primary' : 'bg.muted'}
                  color={isActive ? 'chat.user.text' : 'text.primary'}
                  borderColor="transparent"
                  _hover={{ bg: isActive ? 'brand.600' : 'bg.panel' }}
                  size="sm"
                  minH="40px"
                  onClick={() => setFormValue('duration_minutes', preset.value)}
                  type="button"
                >
                  {preset.label}
                </Button>
              )
            })}
          </SimpleGrid>
          <Controller
            name="duration_minutes"
            control={control}
            render={({ field }) => (
              <NumberInput
                min={1}
                max={600}
                value={field.value}
                onChange={(val) => field.onChange(val)}
                size="sm"
              >
                <NumberInputField placeholder="e.g. 60" />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            )}
          />
        </FormControl>

        {/* RPE */}
        <FormControl>
          <FormLabel fontSize="sm">Intensity (RPE)</FormLabel>
          <Controller
            name="intensity_rpe"
            control={control}
            render={({ field }) => (
              <RPEPicker value={field.value} onChange={field.onChange} />
            )}
          />
        </FormControl>

        {/* Full mode fields */}
        {mode === 'full' && (
          <>
            <FormControl>
              <FormLabel fontSize="sm">Title</FormLabel>
              <Controller
                name="title"
                control={control}
                render={({ field }) => (
                  <Input {...field} placeholder="Session title" maxLength={200} size="sm" />
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Date</FormLabel>
              <Controller
                name="session_date"
                control={control}
                render={({ field }) => (
                  <Input {...field} type="date" size="sm" />
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Rounds</FormLabel>
              <Controller
                name="rounds"
                control={control}
                render={({ field }) => (
                  <NumberInput
                    min={1}
                    max={50}
                    value={field.value}
                    onChange={(val) => field.onChange(val)}
                    size="sm"
                  >
                    <NumberInputField placeholder="e.g. 5" />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Round Duration (min)</FormLabel>
              <Controller
                name="round_duration_minutes"
                control={control}
                render={({ field }) => (
                  <NumberInput
                    min={1}
                    max={30}
                    value={field.value}
                    onChange={(val) => field.onChange(val)}
                    size="sm"
                  >
                    <NumberInputField placeholder="e.g. 3" />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Mood Before</FormLabel>
              <Controller
                name="mood_before"
                control={control}
                render={({ field }) => (
                  <ChoiceChipGroup
                    options={MOOD_OPTIONS}
                    value={field.value}
                    onChange={field.onChange}
                    columns={5}
                  />
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Mood After</FormLabel>
              <Controller
                name="mood_after"
                control={control}
                render={({ field }) => (
                  <ChoiceChipGroup
                    options={MOOD_OPTIONS}
                    value={field.value}
                    onChange={field.onChange}
                    columns={5}
                  />
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Energy Level</FormLabel>
              <Controller
                name="energy_level"
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

            <FormControl>
              <FormLabel fontSize="sm">Techniques</FormLabel>
              <Controller
                name="techniques"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="e.g. Teep, Low kick"
                  />
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Training Partner</FormLabel>
              <Controller
                name="training_partner"
                control={control}
                render={({ field }) => (
                  <Input {...field} placeholder="Partner name" maxLength={100} size="sm" />
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Gym</FormLabel>
              <Controller
                name="gym_name"
                control={control}
                render={({ field }) => (
                  <Input {...field} placeholder="Gym name" maxLength={100} size="sm" />
                )}
              />
            </FormControl>

            <FormControl>
              <Flex align="center" justify="space-between">
                <FormLabel fontSize="sm" mb={0}>Notes</FormLabel>
                {speech.isSupported && (
                  <IconButton
                    aria-label={speech.isListening ? 'Stop listening' : 'Voice input'}
                    icon={<Mic size={16} />}
                    variant="ghost"
                    color={speech.isListening ? 'brand.primary' : 'text.secondary'}
                    borderRadius="full"
                    size="xs"
                    _hover={{ bg: 'bg.muted' }}
                    onClick={speech.isListening ? speech.stopListening : speech.startListening}
                    animation={speech.isListening ? `${micPulse} 1.5s infinite` : undefined}
                  />
                )}
              </Flex>
              <Controller
                name="notes"
                control={control}
                render={({ field }) => (
                  <Textarea
                    {...field}
                    placeholder="How did it go?"
                    maxLength={5000}
                    size="sm"
                    rows={3}
                  />
                )}
              />
            </FormControl>
          </>
        )}

        <Button
          type="submit"
          colorScheme="brand"
          width="full"
          isLoading={isPending}
          size="md"
        >
          {isEditing ? 'Save Changes' : 'Log Session'}
        </Button>

        {onCancel && (
          <Button variant="ghost" width="full" onClick={onCancel} size="sm" color="text.secondary">
            Cancel
          </Button>
        )}
      </VStack>
    </Box>
  )
}
