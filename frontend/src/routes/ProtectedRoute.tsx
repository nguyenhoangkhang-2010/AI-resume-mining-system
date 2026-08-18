import type { ReactNode } from "react";

import { Navigate } from "react-router-dom";


interface ProtectedRouteProps {
  children: ReactNode;

  isAuthenticated?: boolean;
}


export function ProtectedRoute({
  children,
  isAuthenticated = false,
}: ProtectedRouteProps) {
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }


  return children;
}