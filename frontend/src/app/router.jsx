import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import PublicLayout from '../components/layout/PublicLayout.jsx';
import ComingSoonPage from '../pages/ComingSoonPage.jsx';
import LandingPage from '../pages/LandingPage.jsx';
import LoginPage from '../pages/LoginPage.jsx';
import NotFoundPage from '../pages/NotFoundPage.jsx';
import RegisterPage from '../pages/RegisterPage.jsx';
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
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/terms" element={<ComingSoonPage title={texts.legal.termsTitle} />} />
            <Route path="/privacy" element={<ComingSoonPage title={texts.legal.privacyTitle} />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
          {StyleguidePage && <Route path="/styleguide" element={<StyleguidePage />} />}
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
