import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { TopBar } from "./components/TopBar";
import { Onboarding } from "./pages/Onboarding";
import { Discover } from "./pages/Discover";
import { Recommendations } from "./pages/Recommendations";
import { Profile } from "./pages/Profile";
import { Register } from "./pages/Register";
import { Login } from "./pages/Login";
import { storage } from "./app/storage";
import React from "react";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = storage.getToken();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const location = useLocation();
  const hideTopbar = location.pathname === "/login" || location.pathname === "/register";

  return (
    <div className="min-h-screen text-white bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950">
      <div className="pointer-events-none fixed inset-0 opacity-40">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-emerald-500 blur-[120px]" />
        <div className="absolute top-40 -right-40 h-96 w-96 rounded-full bg-sky-500 blur-[140px]" />
      </div>

      {!hideTopbar && <TopBar />}

      <Routes>
        {/* Auth pages (no TopBar) */}
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />

        {/* Protected pages */}
        <Route
          path="/"
          element={
            <RequireAuth>
              <Onboarding />
            </RequireAuth>
          }
        />
        <Route
          path="/discover"
          element={
            <RequireAuth>
              <Discover />
            </RequireAuth>
          }
        />
        <Route
          path="/recommendations"
          element={
            <RequireAuth>
              <Recommendations />
            </RequireAuth>
          }
        />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
