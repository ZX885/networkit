import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from '../components/layout/AppLayout.jsx';
import PublicLayout from '../components/layout/PublicLayout.jsx';
import GuestRoute from './routes/GuestRoute.jsx';
import NotFoundRoute from './routes/NotFoundRoute.jsx';
import ProtectedRoute from './routes/ProtectedRoute.jsx';
import AccountTab from '../features/settings/components/AccountTab.jsx';
import PrivacyTab from '../features/settings/components/PrivacyTab.jsx';
import ComingSoonPage from '../pages/ComingSoonPage.jsx';
import DiscoverPage from '../pages/DiscoverPage.jsx';
import EditProfilePage from '../pages/EditProfilePage.jsx';
import LandingPage from '../pages/LandingPage.jsx';
import LoginPage from '../pages/LoginPage.jsx';
import MessagesPage from '../pages/MessagesPage.jsx';
import MyProfilePage from '../pages/MyProfilePage.jsx';
import ProfilePage from '../pages/ProfilePage.jsx';
import RegisterPage from '../pages/RegisterPage.jsx';
import ResendVerificationPage from '../pages/ResendVerificationPage.jsx';
import SavedPage from '../pages/SavedPage.jsx';
import SettingsPage from '../pages/SettingsPage.jsx';
import VerifyEmailPage from '../pages/VerifyEmailPage.jsx';
import { texts } from '../texts/en.js';

// Страница /styleguide нужна только разработчику: в production-сборку она не попадает
const StyleguidePage = import.meta.env.DEV
  ? lazy(() => import('../pages/styleguide/StyleguidePage.jsx'))
  : null;

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Suspense fallback={null}>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route path="/" element={<LandingPage />} />
            <Route
              path="/login"
              element={
                <GuestRoute>
                  <LoginPage />
                </GuestRoute>
              }
            />
            <Route
              path="/register"
              element={
                <GuestRoute>
                  <RegisterPage />
                </GuestRoute>
              }
            />
            <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
            <Route path="/resend-verification" element={<ResendVerificationPage />} />
            <Route path="/terms" element={<ComingSoonPage title={texts.legal.termsTitle} />} />
            <Route path="/privacy" element={<ComingSoonPage title={texts.legal.privacyTitle} />} />
          </Route>
          {/* Приложение для вошедшего: сайдбар + страницы */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/discover" element={<DiscoverPage />} />
            <Route path="/me" element={<MyProfilePage />} />
            <Route path="/me/edit" element={<EditProfilePage />} />
            <Route path="/u/:username" element={<ProfilePage />} />
            <Route path="/saved" element={<SavedPage />} />
            <Route path="/messages" element={<MessagesPage />} />
            <Route path="/messages/:conversationId" element={<MessagesPage />} />
            <Route path="/settings" element={<SettingsPage />}>
              <Route index element={<Navigate to="account" replace />} />
              <Route path="account" element={<AccountTab />} />
              <Route path="privacy" element={<PrivacyTab />} />
            </Route>
          </Route>
          <Route path="*" element={<NotFoundRoute />} />
          {StyleguidePage && <Route path="/styleguide" element={<StyleguidePage />} />}
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
