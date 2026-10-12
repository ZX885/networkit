import { useContext } from 'react';
import { AuthContext } from './AuthContext.js';

// const { status, user, login, logout, refresh } = useAuth();
export default function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
