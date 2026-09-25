import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, UserPlus, Fingerprint, Lock, User, Briefcase, BadgeAlert, FileText, Activity, Map as MapIcon } from 'lucide-react';
import { Button } from '../components/ui/Button';

export default function SignupPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    rank: '',
    branch: '',
    phoneNumber: '',
    assignedStation: '',
    profilePicture: ''
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          passwordHash: formData.password, // Sending as passwordHash as expected by our backend
          name: formData.name,
          rank: formData.rank,
          branch: formData.branch,
          phoneNumber: formData.phoneNumber,
          assignedStation: formData.assignedStation,
          profilePicture: formData.profilePicture
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to register');
      }

      // Success! Redirect to login so they can log in
      navigate('/login?registered=true');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Left side Form */}
      <div className="flex-1 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm lg:w-[450px]">
          <div className="flex items-center gap-3 mb-8">
            <div className="bg-police-blue p-2 rounded-xl text-white">
              <ShieldAlert size={32} />
            </div>
            <h2 className="text-3xl font-extrabold text-police-900 tracking-tight">Safe-Vision AI</h2>
          </div>
          
          <h3 className="mt-8 text-xl font-bold text-gray-900 mb-6">
            Register new personnel
          </h3>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSignup}>
            <div>
              <label className="block text-sm font-medium text-gray-700">Full Name</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="pl-10 block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 focus:ring-police-blue focus:border-police-blue"
                  placeholder="e.g. John Doe"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Email Address</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Fingerprint className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="pl-10 block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 focus:ring-police-blue focus:border-police-blue"
                  placeholder="e.g. user@police.lk"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="password"
                  name="password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="pl-10 block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 focus:ring-police-blue focus:border-police-blue"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Phone Number</label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <input
                    type="tel"
                    name="phoneNumber"
                    value={formData.phoneNumber}
                    onChange={handleChange}
                    className="block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 px-3 focus:ring-police-blue focus:border-police-blue"
                    placeholder="e.g. 0771234567"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Assigned Station</label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <input
                    type="text"
                    name="assignedStation"
                    value={formData.assignedStation}
                    onChange={handleChange}
                    className="block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 px-3 focus:ring-police-blue focus:border-police-blue"
                    placeholder="e.g. Colombo South"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Profile Picture URL (Optional)</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <input
                  type="url"
                  name="profilePicture"
                  value={formData.profilePicture}
                  onChange={handleChange}
                  className="block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 px-3 focus:ring-police-blue focus:border-police-blue"
                  placeholder="https://example.com/photo.jpg"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Rank</label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <BadgeAlert className="h-5 w-5 text-gray-400" />
                  </div>
                  <select
                    name="rank"
                    value={formData.rank}
                    onChange={handleChange}
                    className="pl-10 block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 focus:ring-police-blue focus:border-police-blue bg-white"
                  >
                    <option value="">Select Rank</option>
                    <option value="Constable">Constable</option>
                    <option value="Sergeant">Sergeant</option>
                    <option value="Inspector">Inspector</option>
                    <option value="Chief Inspector">Chief Inspector</option>
                    <option value="Superintendent">Superintendent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Branch</label>
                <div className="mt-1 relative rounded-md shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Briefcase className="h-5 w-5 text-gray-400" />
                  </div>
                  <select
                    name="branch"
                    value={formData.branch}
                    onChange={handleChange}
                    className="pl-10 block w-full sm:text-sm border-gray-300 rounded-md border py-2.5 focus:ring-police-blue focus:border-police-blue bg-white"
                  >
                    <option value="">Select Branch</option>
                    <option value="Crime">Crime</option>
                    <option value="Traffic">Traffic</option>
                    <option value="Admin">Admin</option>
                    <option value="Raid">Raid</option>
                    <option value="Narcotics">Narcotics</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="pt-2">
              <Button type="submit" className="w-full h-11 text-base" disabled={isLoading}>
                {isLoading ? 'Registering...' : 'Register Account'} <UserPlus className="ml-2 h-4 w-4" />
              </Button>
            </div>
            
            <div className="mt-6 text-center text-sm text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-police-blue hover:text-police-blue-light">
                Sign in instead
              </Link>
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
            Secure Police Network <br /> Access Provisioning
           </h1>
           <p className="max-w-xl text-lg text-slate-400 mt-2 font-medium">
             Authorized personnel only.<br />
             All registration requests are logged and monitored.
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
