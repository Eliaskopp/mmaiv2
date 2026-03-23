import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Button,
  Container,
  Heading,
  HStack,
  Image,
  PinInput,
  PinInputField,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import * as authApi from '../services/auth'

const COOLDOWN_SECONDS = 60

export function VerifyEmailPage() {
  const { user, isAuthenticated, refreshUser } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()

  const [code, setCode] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [cooldown, setCooldown] = useState(0)
  const cooldownRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Start cooldown timer on mount (code was just sent during registration)
  useEffect(() => {
    setCooldown(COOLDOWN_SECONDS)
  }, [])

  useEffect(() => {
    if (cooldown <= 0) {
      if (cooldownRef.current) clearInterval(cooldownRef.current)
      return
    }
    cooldownRef.current = setInterval(() => {
      setCooldown((c) => {
        if (c <= 1) {
          if (cooldownRef.current) clearInterval(cooldownRef.current)
          return 0
        }
        return c - 1
      })
    }, 1000)
    return () => {
      if (cooldownRef.current) clearInterval(cooldownRef.current)
    }
  }, [cooldown])

  const handleVerify = useCallback(
    async (value: string) => {
      if (!user?.email || value.length !== 6) return
      setIsSubmitting(true)
      try {
        await authApi.verifyEmail(user.email, value)
        toast({ title: 'Email verified!', status: 'success', duration: 3000 })
        await refreshUser()
        navigate('/chat', { replace: true })
      } catch (err: unknown) {
        const detail =
          (err as { response?: { data?: { detail?: string } } })?.response?.data
            ?.detail
        toast({
          title: typeof detail === 'string' ? detail : 'Verification failed',
          status: 'error',
          duration: 4000,
        })
        setCode('')
      } finally {
        setIsSubmitting(false)
      }
    },
    [user?.email, navigate, toast, refreshUser],
  )

  async function handleResend() {
    if (!user?.email || cooldown > 0) return
    try {
      await authApi.resendVerification(user.email)
      toast({ title: 'New code sent — check your email', status: 'info', duration: 3000 })
      setCooldown(COOLDOWN_SECONDS)
      setCode('')
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast({
        title: typeof detail === 'string' ? detail : 'Failed to resend code',
        status: 'error',
        duration: 4000,
      })
    }
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (user?.is_verified) return <Navigate to="/chat" replace />

  return (
    <Container maxW="sm" py={20}>
      <VStack spacing={6} align="stretch">
        <Image src="/logo.png" alt="MMAi" h="40px" mx="auto" />
        <Heading textAlign="center" size="lg">
          Check your email
        </Heading>
        <Text textAlign="center" color="text.secondary" fontSize="sm">
          We sent a 6-digit code to{' '}
          <Text as="span" fontWeight="bold" color="text.primary">
            {user?.email}
          </Text>
        </Text>

        <HStack justify="center" spacing={3}>
          <PinInput
            otp
            size="lg"
            value={code}
            onChange={setCode}
            onComplete={handleVerify}
            isDisabled={isSubmitting}
            autoFocus
          >
            <PinInputField />
            <PinInputField />
            <PinInputField />
            <PinInputField />
            <PinInputField />
            <PinInputField />
          </PinInput>
        </HStack>

        <Button
          colorScheme="brand"
          width="full"
          isLoading={isSubmitting}
          isDisabled={code.length !== 6}
          onClick={() => handleVerify(code)}
        >
          Verify
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleResend}
          isDisabled={cooldown > 0}
          mx="auto"
        >
          {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend Code'}
        </Button>

        <Text textAlign="center" fontSize="sm" color="text.muted">
          Wrong email?{' '}
          <Text as={Link} to="/register" color="brand.primary" fontWeight="medium">
            Go back
          </Text>
        </Text>
      </VStack>
    </Container>
  )
}
