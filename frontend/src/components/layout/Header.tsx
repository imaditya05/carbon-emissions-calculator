import { Link, useLocation } from 'react-router-dom';
import { Calculator, History, User, LogOut, Leaf } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { Button } from '../ui/Button';

export function Header() {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuthStore();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-6 lg:px-10">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-primary/10">
            <Leaf className="h-5 w-5 text-primary" />
          </div>
          <span className="font-semibold text-foreground">CarbonTrack</span>
        </Link>

        {/* Navigation */}
        {isAuthenticated && (
          <nav className="hidden md:flex items-center gap-1">
            <Link to="/calculator">
              <Button
                variant={isActive('/calculator') ? 'secondary' : 'ghost'}
                size="sm"
                className="gap-2"
              >
                <Calculator className="h-4 w-4" />
                Calculator
              </Button>
            </Link>
            <Link to="/history">
              <Button
                variant={isActive('/history') ? 'secondary' : 'ghost'}
                size="sm"
                className="gap-2"
              >
                <History className="h-4 w-4" />
                History
              </Button>
            </Link>
          </nav>
        )}

        {/* User Menu */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2 bg-transparent">
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">{user.full_name}</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Sign in
              </Button>
            </Link>
            <Link to="/register">
              <Button size="sm">Sign up</Button>
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}
