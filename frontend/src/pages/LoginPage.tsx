import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Image,
  Input,
  Select,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const toast = useToast()
  const { t, i18n } = useTranslation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const from = (location.state as { from?: Location })?.from?.pathname || '/chat'

  if (isAuthenticated) return <Navigate to={from} replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Login failed'
      toast({ title: message, status: 'error', duration: 4000 })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Container maxW="sm" py={20}>
      <VStack spacing={6} align="stretch">
        <Box display="flex" justifyContent="flex-end">
          <Select
            size="sm"
            w="120px"
            value={i18n.language.startsWith('nl') ? 'nl' : 'en'}
            onChange={(e) => i18n.changeLanguage(e.target.value)}
          >
            <option value="en">English</option>
            <option value="nl">Nederlands</option>
          </Select>
        </Box>
        <Image src="/logo.png" alt="MMAi" h="64px" mx="auto" />
        <Box as="form" onSubmit={handleSubmit}>
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel>{t('login.email')}</FormLabel>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>{t('login.password')}</FormLabel>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </FormControl>
            <Button type="submit" colorScheme="brand" width="full" isLoading={isSubmitting}>
              {t('login.submit')}
            </Button>
          </VStack>
        </Box>
        <Text textAlign="center" fontSize="sm">
          {t('login.noAccount')}{' '}
          <Text as={Link} to="/register" color="brand.primary" fontWeight="medium">
            {t('login.register')}
          </Text>
        </Text>
      </VStack>
    </Container>
  )
}
