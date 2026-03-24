import { useEffect, useState } from 'react'
import { useForm, useWatch, Controller } from 'react-hook-form'
import { useSearchParams } from 'react-router-dom'
import {
  Box,
  Button,
  Center,
  Container,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Progress,
  SimpleGrid,
  Spinner,
  Text,
  Textarea,
  VStack,
  useToast,
} from '@chakra-ui/react'
import { useProfile, useCreateProfile, useUpdateProfile } from '../hooks/use-profile'
import { ChoiceChipGroup } from '../components/ChoiceChipGroup'
import { TagInput } from '../components/TagInput'
import type { ProfileUpdate } from '../types'
import type { AxiosError } from 'axios'

const SKILL_OPTIONS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
  { value: 'professional', label: 'Professional' },
]

const WEIGHT_CLASS_OPTIONS = [
  { value: 'Flyweight', label: 'Flyweight' },
  { value: 'Bantamweight', label: 'Bantamweight' },
  { value: 'Featherweight', label: 'Featherweight' },
  { value: 'Lightweight', label: 'Lightweight' },
  { value: 'Welterweight', label: 'Welterweight' },
  { value: 'Heavyweight', label: 'Heavyweight' },
  { value: '__other__', label: 'Other' },
]

const WEIGHT_CLASS_KNOWN = WEIGHT_CLASS_OPTIONS.filter((o) => o.value !== '__other__').map(
  (o) => o.value,
)

const WEIGHT_UNIT_OPTIONS = [
  { value: 'kg', label: 'kg' },
  { value: 'lb', label: 'lb' },
]

const GAME_STYLE_OPTIONS = [
  { value: 'Pressure', label: 'Pressure' },
  { value: 'Counter', label: 'Counter' },
  { value: 'Volume', label: 'Volume' },
  { value: 'Submission', label: 'Submission' },
]

const ROLE_OPTIONS = [
  { value: 'fighter', label: 'Fighter' },
  { value: 'coach', label: 'Coach' },
  { value: 'hobbyist', label: 'Hobbyist' },
]

const TRAINING_FREQ_OPTIONS = [
  { value: '1-2x/week', label: '1-2x/week' },
  { value: '3-4x/week', label: '3-4x/week' },
  { value: '5-6x/week', label: '5-6x/week' },
  { value: 'Daily', label: 'Daily' },
]

const PRIMARY_DOMAIN_OPTIONS = [
  { value: 'Striking', label: 'Striking' },
  { value: 'Grappling', label: 'Grappling' },
  { value: 'MMA', label: 'MMA' },
  { value: 'Wrestling', label: 'Wrestling' },
]

const EMPTY_DEFAULTS: ProfileUpdate = {
  role: 'fighter',
  skill_level: null,
  weight_unit: 'kg',
  martial_arts: [],
  injuries: [],
  strategic_leaks: [],
  goals: '',
  training_frequency: '',
  weight_class: '',
  primary_domain: '',
  game_style: '',
  language_code: 'en',
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'No sessions yet'
  return new Date(dateStr).toLocaleDateString()
}

export function ProfilePage() {
  const toast = useToast()
  const [searchParams] = useSearchParams()
  const { data: profile, isLoading, isError, error } = useProfile()
  const createMutation = useCreateProfile()
  const updateMutation = useUpdateProfile()

  const is404 = isError && (error as AxiosError)?.response?.status === 404
  const hasProfile = !!profile

  const { control, handleSubmit, reset } = useForm<ProfileUpdate>({
    defaultValues: EMPTY_DEFAULTS,
  })

  const weightClassValue = useWatch({ control, name: 'weight_class' }) ?? ''
  const isCustomWeightClass =
    weightClassValue !== '' && !WEIGHT_CLASS_KNOWN.includes(weightClassValue)
  const [showCustomWeight, setShowCustomWeight] = useState(false)

  useEffect(() => {
    if (profile) {
      reset({
        role: (profile.role as ProfileUpdate['role']) ?? 'fighter',
        skill_level: (profile.skill_level as ProfileUpdate['skill_level']) ?? null,
        weight_unit: (profile.weight_unit as ProfileUpdate['weight_unit']) ?? 'kg',
        martial_arts: profile.martial_arts ?? [],
        injuries: profile.injuries ?? [],
        strategic_leaks: profile.strategic_leaks ?? [],
        goals: profile.goals ?? '',
        training_frequency: profile.training_frequency ?? '',
        weight_class: profile.weight_class ?? '',
        primary_domain: profile.primary_domain ?? '',
        game_style: profile.game_style ?? '',
        language_code: profile.language_code ?? 'en',
      })
    }
  }, [profile, reset])

  function onSubmit(values: ProfileUpdate) {
    const cleaned: ProfileUpdate = {
      ...values,
      skill_level: values.skill_level || null,
      goals: values.goals || null,
      training_frequency: values.training_frequency || null,
      weight_class: values.weight_class || null,
      primary_domain: values.primary_domain || null,
      game_style: values.game_style || null,
      martial_arts: values.martial_arts?.length ? values.martial_arts : null,
      injuries: values.injuries?.length ? values.injuries : null,
      strategic_leaks: values.strategic_leaks?.length ? values.strategic_leaks : null,
    }

    const mutation = hasProfile ? updateMutation : createMutation
    mutation.mutate(cleaned, {
      onSuccess: () => {
        toast({
          title: hasProfile ? 'Profile updated' : 'Profile created',
          status: 'success',
          duration: 4000,
        })
      },
      onError: (err) => {
        const message =
          (err as AxiosError<{ detail?: string }>)?.response?.data?.detail || 'Save failed'
        toast({ title: message, status: 'error', duration: 4000 })
      },
    })
  }

  if (isLoading) {
    return (
      <Center h="100vh">
        <Spinner size="xl" />
      </Center>
    )
  }

  if (isError && !is404) {
    return (
      <Container maxW="container.md" py={6}>
        <Text color="red.400">Failed to load profile.</Text>
      </Container>
    )
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  // Derive the chip value for Weight Class
  const weightChipValue = showCustomWeight || isCustomWeightClass ? '__other__' : weightClassValue

  const isOnboarding = searchParams.get('onboarding') === 'true'
  const isIncomplete = (profile?.profile_completeness ?? 0) <= 50

  let pageHeading = 'Profile'
  let pageSubtext: string | null = null
  if (!hasProfile || (isOnboarding && is404)) {
    pageHeading = 'Welcome!'
    pageSubtext = 'Set up your training profile to get started.'
  } else if (isOnboarding || isIncomplete) {
    pageHeading = 'Almost there'
    pageSubtext = 'Fill in a few more details to unlock the coach.'
  }

  return (
    <Container maxW="container.md" py={6}>
      <Heading size="lg" mb={pageSubtext ? 1 : 6}>
        {pageHeading}
      </Heading>
      {pageSubtext && (
        <Text color="text.muted" mb={6}>
          {pageSubtext}
        </Text>
      )}

      {/* Completeness Bar — always visible, 0% when no profile */}
      <Box bg="bg.subtle" p={4} borderRadius="lg" mb={8}>
        <Box mb={profile ? 3 : 0}>
          <Text
            fontSize="xs"
            color="text.muted"
            textTransform="uppercase"
            letterSpacing="wide"
            mb={1}
          >
            Profile Completeness
          </Text>
          <Box display="flex" alignItems="center" gap={3}>
            <Progress
              value={profile?.profile_completeness ?? 0}
              flex={1}
              size="sm"
              borderRadius="full"
              colorScheme="brand"
            />
            <Text
              fontFamily="mono"
              fontSize="sm"
              fontWeight="semibold"
              sx={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {profile?.profile_completeness ?? 0}%
            </Text>
          </Box>
        </Box>

        {profile && (
          <>
            <SimpleGrid columns={3} spacing={4} mb={3}>
              <Box>
                <Text
                  fontFamily="mono"
                  fontSize="2xl"
                  fontWeight="semibold"
                  sx={{ fontVariantNumeric: 'tabular-nums' }}
                >
                  {profile.current_streak}
                </Text>
                <Text
                  fontSize="xs"
                  color="text.muted"
                  textTransform="uppercase"
                  letterSpacing="wide"
                >
                  Current Streak
                </Text>
              </Box>
              <Box>
                <Text
                  fontFamily="mono"
                  fontSize="2xl"
                  fontWeight="semibold"
                  sx={{ fontVariantNumeric: 'tabular-nums' }}
                >
                  {profile.longest_streak}
                </Text>
                <Text
                  fontSize="xs"
                  color="text.muted"
                  textTransform="uppercase"
                  letterSpacing="wide"
                >
                  Longest Streak
                </Text>
              </Box>
              <Box>
                <Text
                  fontFamily="mono"
                  fontSize="2xl"
                  fontWeight="semibold"
                  sx={{ fontVariantNumeric: 'tabular-nums' }}
                >
                  {profile.grace_days_remaining}
                </Text>
                <Text
                  fontSize="xs"
                  color="text.muted"
                  textTransform="uppercase"
                  letterSpacing="wide"
                >
                  Grace Days
                </Text>
              </Box>
            </SimpleGrid>

            <Text fontSize="sm" color="text.secondary">
              Last Active: {formatDate(profile.last_active_date)}
            </Text>
          </>
        )}
      </Box>

      {/* Form */}
      <Box as="form" onSubmit={handleSubmit(onSubmit)}>
        <VStack spacing={8} align="stretch">
          {/* ── Experience ── */}
          <Box bg="bg.subtle" p={5} borderRadius="lg">
            <Text fontSize="md" fontWeight="semibold" color="text.primary" mb={4}>
              Experience
            </Text>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Skill Level</FormLabel>
                <Controller
                  name="skill_level"
                  control={control}
                  render={({ field }) => (
                    <ChoiceChipGroup
                      options={SKILL_OPTIONS}
                      value={field.value ?? null}
                      onChange={field.onChange}
                      columns={2}
                    />
                  )}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Martial Arts</FormLabel>
                <Controller
                  name="martial_arts"
                  control={control}
                  render={({ field }) => (
                    <TagInput
                      value={field.value ?? []}
                      onChange={field.onChange}
                      placeholder="e.g. Muay Thai, BJJ"
                    />
                  )}
                />
              </FormControl>
            </VStack>
          </Box>

          {/* ── Biometrics ── */}
          <Box bg="bg.subtle" p={5} borderRadius="lg">
            <Text fontSize="md" fontWeight="semibold" color="text.primary" mb={4}>
              Biometrics
            </Text>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Weight Class</FormLabel>
                <Controller
                  name="weight_class"
                  control={control}
                  render={({ field }) => (
                    <VStack align="stretch" spacing={2}>
                      <ChoiceChipGroup
                        options={WEIGHT_CLASS_OPTIONS}
                        value={weightChipValue || null}
                        onChange={(val) => {
                          if (val === '__other__') {
                            setShowCustomWeight(true)
                            // Keep existing custom value or clear to let user type
                            if (WEIGHT_CLASS_KNOWN.includes(field.value ?? '')) {
                              field.onChange('')
                            }
                          } else {
                            setShowCustomWeight(false)
                            field.onChange(val)
                          }
                        }}
                        columns={2}
                      />
                      {(showCustomWeight || isCustomWeightClass) && (
                        <Input
                          value={field.value ?? ''}
                          onChange={(e) => field.onChange(e.target.value)}
                          placeholder="Enter weight class"
                          maxLength={30}
                          size="sm"
                          autoFocus
                        />
                      )}
                    </VStack>
                  )}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Weight Unit</FormLabel>
                <Controller
                  name="weight_unit"
                  control={control}
                  render={({ field }) => (
                    <ChoiceChipGroup
                      options={WEIGHT_UNIT_OPTIONS}
                      value={field.value ?? null}
                      onChange={field.onChange}
                      columns={2}
                    />
                  )}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Injuries</FormLabel>
                <Controller
                  name="injuries"
                  control={control}
                  render={({ field }) => (
                    <TagInput
                      value={field.value ?? []}
                      onChange={field.onChange}
                      placeholder="e.g. Left knee, Right shoulder"
                    />
                  )}
                />
              </FormControl>
            </VStack>
          </Box>

          {/* ── Style ── */}
          <Box bg="bg.subtle" p={5} borderRadius="lg">
            <Text fontSize="md" fontWeight="semibold" color="text.primary" mb={4}>
              Style
            </Text>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Game Style</FormLabel>
                <Controller
                  name="game_style"
                  control={control}
                  render={({ field }) => (
                    <ChoiceChipGroup
                      options={GAME_STYLE_OPTIONS}
                      value={field.value ?? null}
                      onChange={field.onChange}
                      columns={2}
                    />
                  )}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Strategic Leaks</FormLabel>
                <Controller
                  name="strategic_leaks"
                  control={control}
                  render={({ field }) => (
                    <TagInput
                      value={field.value ?? []}
                      onChange={field.onChange}
                      placeholder="e.g. Dropping hands after jab"
                    />
                  )}
                />
              </FormControl>
            </VStack>
          </Box>

          {/* ── Goals & Preferences ── */}
          <Box bg="bg.subtle" p={5} borderRadius="lg">
            <Text fontSize="md" fontWeight="semibold" color="text.primary" mb={4}>
              Goals & Preferences
            </Text>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Role</FormLabel>
                <Controller
                  name="role"
                  control={control}
                  render={({ field }) => (
                    <ChoiceChipGroup
                      options={ROLE_OPTIONS}
                      value={field.value ?? null}
                      onChange={field.onChange}
                      columns={3}
                    />
                  )}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Training Frequency</FormLabel>
                <Controller
                  name="training_frequency"
                  control={control}
                  render={({ field }) => (
                    <ChoiceChipGroup
                      options={TRAINING_FREQ_OPTIONS}
                      value={field.value ?? null}
                      onChange={field.onChange}
                      columns={2}
                    />
                  )}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Primary Domain</FormLabel>
                <Controller
                  name="primary_domain"
                  control={control}
                  render={({ field }) => (
                    <ChoiceChipGroup
                      options={PRIMARY_DOMAIN_OPTIONS}
                      value={field.value ?? null}
                      onChange={field.onChange}
                      columns={2}
                    />
                  )}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Goals</FormLabel>
                <Controller
                  name="goals"
                  control={control}
                  render={({ field }) => (
                    <Textarea
                      {...field}
                      value={field.value ?? ''}
                      placeholder="What are you working towards?"
                      maxLength={2000}
                      size="sm"
                      rows={4}
                    />
                  )}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Language Code</FormLabel>
                <Controller
                  name="language_code"
                  control={control}
                  render={({ field }) => (
                    <Input
                      {...field}
                      value={field.value ?? ''}
                      placeholder="en"
                      maxLength={10}
                      size="sm"
                    />
                  )}
                />
              </FormControl>
            </VStack>
          </Box>

          {/* Save */}
          <Button type="submit" colorScheme="brand" width="full" isLoading={isPending} size="lg">
            {hasProfile ? 'Save Changes' : 'Create Profile'}
          </Button>
        </VStack>
      </Box>
    </Container>
  )
}
