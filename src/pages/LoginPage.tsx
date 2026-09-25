import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { ShieldAlert, LogIn, Fingerprint, Lock, FileText, Activity, Map as MapIcon } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Check if just registered
  const searchParams = new URLSearchParams(location.search);
  const justRegistered = searchParams.get('registered') === 'true';

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }

      // Update auth context
      login(data.token, data.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (role: string) => {
    // We will attempt to login with a predefined demo user, or simply
    // if the user wants to test real auth, they can create one.
    // Let's autofill for the demo instead of auto-submitting.
    if (role === 'Admin') {
      setEmail('admin@police.lk');
      setPassword('admin123');
    } else if (role === 'Officer') {
      setEmail('officer@police.lk');
      setPassword('officer123');
    } else if (role === 'Analyst') {
      setEmail('analyst@police.lk');
      setPassword('analyst123');
    }
    setError('Demo credentials filled. Please click Secure Login.');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Left side Form */}
      <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm lg:w-[400px]">
          <div className="flex items-center gap-3 mb-8">
            <div className="bg-police-blue p-2 rounded-xl text-white">
              <ShieldAlert size={32} />
            </div>
            <h2 className="text-3xl font-extrabold text-police-900 tracking-tight">Safe-Vision AI</h2>
          </div>
          
          <h3 className="mt-8 text-xl font-bold text-gray-900 mb-6">
            Sign in to operations
          </h3>

          {justRegistered && (
            <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md text-sm">
              Account created successfully. Please log in.
            </div>
          )}

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          <form className="space-y-5" onSubmit={handleLogin}>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Fingerprint className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 focus:ring-police-blue focus:border-police-blue"
                  placeholder="e.g. user@police.lk"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 focus:ring-police-blue focus:border-police-blue"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  defaultChecked
                  className="h-4 w-4 text-police-blue focus:ring-police-blue border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                  Remember me
                </label>
              </div>

              <div className="text-sm">
                <a href="#" className="font-medium text-police-blue-light hover:text-police-blue">
                  Forgot your password?
                </a>
              </div>
            </div>

            <div>
              <Button type="submit" className="w-full h-11 text-base" disabled={isLoading}>
                {isLoading ? 'Authenticating...' : 'Secure Login'} <LogIn className="ml-2 h-4 w-4" />
              </Button>
            </div>
            
            <div className="mt-4 text-center text-sm text-gray-600">
              Don't have an account?{' '}
              <Link to="/signup" className="font-medium text-police-blue hover:text-police-blue-light">
                Register here
              </Link>
            </div>

            <div className="mt-6 border-t border-gray-200 pt-6">
              <p className="text-sm text-gray-600 mb-4 text-center">Demo Auto-Fill (Testing)</p>
              <div className="grid grid-cols-3 gap-3">
                <Button variant="outline" size="sm" type="button" onClick={() => handleDemoLogin('Admin')}>Admin</Button>
                <Button variant="outline" size="sm" type="button" onClick={() => handleDemoLogin('Officer')}>Officer</Button>
                <Button variant="outline" size="sm" type="button" onClick={() => handleDemoLogin('Analyst')}>Analyst</Button>
              </div>
            </div>
          </form>
        </div>
      </div>
      
      {/* Right side Image/Branding */}
      <div className="hidden lg:block relative w-0 flex-1 bg-police-900 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-police-900 to-police-800 opacity-90 z-10" />
        <div className="absolute inset-0 opacity-20 pointer-events-none select-none z-0" 
             style={{ backgroundImage: 'radial-gradient(#475569 1px, transparent 1px)', backgroundSize: '16px 16px' }} />
        
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center p-12 text-slate-300">
           <ShieldAlert size={80} className="text-police-blue-light mb-8 opacity-80" />
           <h1 className="text-4xl font-bold text-white tracking-tight mb-4 shadow-sm">
            AI-Powered Case Handling & <br /> Predictive Analysis System
           </h1>
           <p className="max-w-xl text-lg text-slate-400 mt-2 font-medium">
             Sri Lanka Police Station-Level Intelligence Platform.<br />
             Digitize complaints, automate NLP extraction, and leverage real-time spatial analytics.
           </p>
           
           <div className="mt-16 grid grid-cols-3 gap-8 max-w-2xl mx-auto w-full px-8 opacity-80">
            <div className="flex flex-col items-center gap-2">
              <div className="p-3 bg-white/5 shadow border border-white/10 rounded-xl"><FileText className="text-blue-400" /></div>
              <span className="text-sm font-semibold text-slate-300">Smart OCR</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="p-3 bg-white/5 shadow border border-white/10 rounded-xl"><Activity className="text-orange-400" /></div>
              <span className="text-sm font-semibold text-slate-300">Predictive Risk</span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="p-3 bg-white/5 shadow border border-white/10 rounded-xl"><MapIcon className="text-green-400" /></div>
              <span className="text-sm font-semibold text-slate-300">GIS Hotspots</span>
            </div>
           </div>
        </div>
      </div>
    </div>
  );
}
