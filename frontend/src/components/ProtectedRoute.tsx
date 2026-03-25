import { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Center, Spinner } from '@chakra-ui/react'
import i18n from 'i18next'
import { useAuth } from '../contexts/AuthContext'
import { useProfile } from '../hooks/use-profile'
import type { ReactNode } from 'react'
import type { AxiosError } from 'axios'

const PROFILE_COMPLETENESS_THRESHOLD = 50

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const location = useLocation()
  const {
    data: profile,
    isLoading: profileLoading,
    isError,
    error,
  } = useProfile({
    enabled: isAuthenticated && !!user?.is_verified,
    retry: false,
  })

  useEffect(() => {
    if (profile?.language_code) {
      i18n.changeLanguage(profile.language_code)
    }
  }, [profile?.language_code])

  if (authLoading) {
    return (
      <Center h="100vh">
        <Spinner size="xl" />
      </Center>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Verification gate — redirect unverified users to the OTP screen
  if (user && !user.is_verified) {
    return <Navigate to="/verify-email" replace />
  }

  // Don't gate the profile page itself — avoid redirect loop
  const isOnProfilePage = location.pathname === '/profile'

  if (!isOnProfilePage) {
    // Wait for profile fetch before deciding
    if (profileLoading) {
      return (
        <Center h="100vh">
          <Spinner size="xl" />
        </Center>
      )
    }

    const is404 = isError && (error as AxiosError)?.response?.status === 404

    if (is404 || (profile && profile.profile_completeness <= PROFILE_COMPLETENESS_THRESHOLD)) {
      return <Navigate to="/profile?onboarding=true" replace />
    }
  }

  return <>{children}</>
}
