import { Outlet } from 'react-router-dom';
import Navbar from './Navbar.jsx';

// Оболочка публичных страниц: верхняя панель + содержимое маршрута.
export default function PublicLayout() {
  return (
    <>
      <Navbar />
      <Outlet />
    </>
  );
}
