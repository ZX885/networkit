import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Footer from '../components/layout/Footer.jsx';
import Cta from '../features/landing/components/Cta.jsx';
import Faq from '../features/landing/components/Faq.jsx';
import Features from '../features/landing/components/Features.jsx';
import Hero from '../features/landing/components/Hero.jsx';
import HowItWorks from '../features/landing/components/HowItWorks.jsx';

// Главная страница. Ссылки навигации ведут на «/#features», «/#how», «/#faq» — здесь прокручиваем
// к нужной секции (плавно, scroll-behavior задан в base.css; key нужен, чтобы повторный клик работал).
export default function LandingPage() {
  const { hash, key } = useLocation();

  useEffect(() => {
    if (!hash) return;
    document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: 'smooth' });
  }, [hash, key]);

  return (
    <main>
      <Hero />
      <Features />
      <HowItWorks />
      <Faq />
      <Cta />
      <Footer />
    </main>
  );
}
