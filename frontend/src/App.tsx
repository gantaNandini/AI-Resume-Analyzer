import { AnimatePresence } from "framer-motion";
import { Route, Routes, useLocation } from "react-router-dom";
import { lazy, Suspense } from "react";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";
import { Spinner } from "./components/ui";

const Home    = lazy(() => import("./pages/Home"));
const Login   = lazy(() => import("./pages/Login"));
const Signup  = lazy(() => import("./pages/Signup"));
const Upload  = lazy(() => import("./pages/Upload"));
const Results = lazy(() => import("./pages/Results"));
const History = lazy(() => import("./pages/History"));

function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950">
      <Spinner size="lg" />
    </div>
  );
}

export default function App() {
  const location = useLocation();
  const showNav = !["login", "signup"].some(p => location.pathname.includes(p));

  return (
    <>
      {showNav && <Navbar />}
      <Suspense fallback={<PageLoader />}>
        <AnimatePresence mode="wait" initial={false}>
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
            <Route path="/results/:jobId" element={<ProtectedRoute><Results /></ProtectedRoute>} />
            <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
          </Routes>
        </AnimatePresence>
      </Suspense>
    </>
  );
}
