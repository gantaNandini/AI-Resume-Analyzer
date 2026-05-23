import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

interface ProtectedRouteProps {
  children: ReactNode;
}

/**
 * ProtectedRoute wraps routes that require authentication.
 * Unauthenticated users are redirected to /login with `replace`
 * so the login page doesn't appear in the browser history stack.
 *
 * Requirements: 2.3, 2.4, 2.5
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
