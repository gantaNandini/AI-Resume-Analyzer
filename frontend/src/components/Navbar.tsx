import { Link, useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui";

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) =>
    location.pathname === path ? "text-primary-400" : "text-slate-400 hover:text-slate-200";

  return (
    <motion.nav
      className="sticky top-0 z-50 glass border-b border-white/5"
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link to={isAuthenticated ? "/upload" : "/"} className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-600 to-violet-600 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span className="font-bold text-slate-100 text-sm">ResumeAI</span>
        </Link>

        {/* Nav links */}
        {isAuthenticated && (
          <div className="hidden sm:flex items-center gap-6">
            <Link to="/upload" className={`text-sm font-medium transition-colors ${isActive("/upload")}`}>Analyze</Link>
            <Link to="/history" className={`text-sm font-medium transition-colors ${isActive("/history")}`}>History</Link>
          </div>
        )}

        {/* Auth actions */}
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <span className="text-xs text-slate-500 hidden sm:block truncate max-w-[140px]">{user?.email}</span>
              <Button variant="ghost" size="sm" onClick={logout}>Sign out</Button>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate("/login")}>Sign in</Button>
              <Button variant="primary" size="sm" onClick={() => navigate("/signup")}>Get started</Button>
            </>
          )}
        </div>
      </div>
    </motion.nav>
  );
}
