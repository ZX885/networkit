import ThemeProvider from './providers/ThemeProvider.jsx';
import ToastProvider from '../components/ui/ToastProvider.jsx';
import AppRouter from './router.jsx';

// Корень приложения: глобальные провайдеры + маршруты
export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AppRouter />
      </ToastProvider>
    </ThemeProvider>
  );
}
