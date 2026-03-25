import { lazy, Suspense } from 'react'
import { ChakraProvider, ColorModeScript, Spinner, Center } from '@chakra-ui/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { RootLayout } from './components/layout/RootLayout'
import theme from './theme'

const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })))
const RegisterPage = lazy(() =>
  import('./pages/RegisterPage').then((m) => ({ default: m.RegisterPage })),
)
const VerifyEmailPage = lazy(() =>
  import('./pages/VerifyEmailPage').then((m) => ({ default: m.VerifyEmailPage })),
)
const ChatPage = lazy(() => import('./pages/ChatPage').then((m) => ({ default: m.ChatPage })))
const JournalPage = lazy(() =>
  import('./pages/JournalPage').then((m) => ({ default: m.JournalPage })),
)
const NotesPage = lazy(() => import('./pages/NotesPage').then((m) => ({ default: m.NotesPage })))
const StatsPage = lazy(() => import('./pages/StatsPage').then((m) => ({ default: m.StatsPage })))
const RecoveryPage = lazy(() =>
  import('./pages/RecoveryPage').then((m) => ({ default: m.RecoveryPage })),
)
const ProfilePage = lazy(() =>
  import('./pages/ProfilePage').then((m) => ({ default: m.ProfilePage })),
)

const queryClient = new QueryClient()

function PageSpinner() {
  return (
    <Center h="100vh">
      <Spinner size="xl" color="orange.400" thickness="3px" />
    </Center>
  )
}

function App() {
  return (
    <ChakraProvider theme={theme}>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <Suspense fallback={<PageSpinner />}>
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/verify-email" element={<VerifyEmailPage />} />

                {/* Protected routes */}
                <Route
                  element={
                    <ProtectedRoute>
                      <RootLayout />
                    </ProtectedRoute>
                  }
                >
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="/chat/:conversationId" element={<ChatPage />} />
                  <Route path="/journal" element={<JournalPage />} />
                  <Route path="/notes" element={<NotesPage />} />
                  <Route path="/stats" element={<StatsPage />} />
                  <Route path="/recovery" element={<RecoveryPage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                </Route>

                {/* Default redirect */}
                <Route path="*" element={<Navigate to="/chat" replace />} />
              </Routes>
            </Suspense>
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ChakraProvider>
  )
}

export default App
