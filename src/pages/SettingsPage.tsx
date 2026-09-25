import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { User as UserIcon, Bell, Shield, Database, LayoutTemplate, Save, Loader2, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function SettingsPage() {
  const { user, token, updateUser } = useAuth();
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phoneNumber: '',
    assignedStation: '',
    profilePicture: '',
    rank: '',
    branch: ''
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState('');

  // Populate form when user data is available
  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || '',
        email: user.email || '',
        phoneNumber: user.phoneNumber || '',
        assignedStation: user.assignedStation || '',
        profilePicture: user.profilePicture || '',
        rank: user.rank || '',
        branch: user.branch || ''
      });
    }
  }, [user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    // Reset success message when user starts typing again
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    if (!user || !token) return;
    
    setIsSaving(true);
    setError('');
    setSaveSuccess(false);

    try {
      const response = await fetch(`/api/users/${user.id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          phoneNumber: formData.phoneNumber,
          assignedStation: formData.assignedStation,
          profilePicture: formData.profilePicture,
          rank: formData.rank,
          branch: formData.branch
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to update profile');
      }

      // Update local auth context
      updateUser(data);
      setSaveSuccess(true);
      
      // Auto-hide success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000);
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  // Extract initials for avatar
  const initials = formData.name
    ? formData.name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
    : 'U';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-police-900 tracking-tight">System Settings</h2>
        <p className="text-slate-500 text-sm">Configure your station preferences and user profile.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        
        {/* Settings Navigation */}
        <div className="md:col-span-1 space-y-1">
          <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-lg bg-blue-50 text-blue-700">
             <UserIcon size={18} /> Profiling & Account
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors">
             <Bell size={18} /> Notifications
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors">
             <Shield size={18} /> Security & Access
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors">
             <Database size={18} /> Data Management
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors">
             <LayoutTemplate size={18} /> Appearance
          </button>
        </div>

        {/* Settings Content Area */}
        <div className="md:col-span-3 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
                  {error}
                </div>
              )}
              
              {saveSuccess && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md text-sm flex items-center gap-2">
                  <CheckCircle2 size={16} /> Profile updated successfully
                </div>
              )}

              <div className="flex items-center gap-6">
                {formData.profilePicture ? (
                  <img 
                    src={formData.profilePicture} 
                    alt="Profile" 
                    className="h-20 w-20 rounded-full object-cover border border-slate-200"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                      // Optionally, you could show the initials fallback here, but it requires more complex state management
                    }}
                  />
                ) : (
                  <div className="h-20 w-20 bg-slate-200 rounded-full flex items-center justify-center text-slate-500 text-xl font-bold uppercase">
                    {initials}
                  </div>
                )}
                
                <div>
                  <h3 className="font-bold text-lg text-police-900">
                    {formData.rank ? `${formData.rank}. ` : ''}{formData.name || 'Officer'}
                  </h3>
                  <p className="text-sm text-slate-500">
                    {formData.branch ? `${formData.branch} Branch` : 'General Branch'} · {formData.assignedStation || 'Unassigned Station'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-100">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                  <input 
                    type="text" 
                    name="name"
                    value={formData.name} 
                    onChange={handleChange}
                    className="w-full border-slate-300 rounded-lg text-sm focus:ring-police-blue bg-white border px-3 py-2" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                  <input 
                    type="email" 
                    name="email"
                    value={formData.email} 
                    onChange={handleChange}
                    className="w-full border-slate-300 rounded-lg text-sm focus:ring-police-blue bg-white border px-3 py-2" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number</label>
                  <input 
                    type="tel" 
                    name="phoneNumber"
                    value={formData.phoneNumber} 
                    onChange={handleChange}
                    className="w-full border-slate-300 rounded-lg text-sm focus:ring-police-blue bg-white border px-3 py-2" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Assigned Station</label>
                  <input 
                    type="text" 
                    name="assignedStation"
                    value={formData.assignedStation} 
                    onChange={handleChange}
                    className="w-full border-slate-300 rounded-lg text-sm focus:ring-police-blue bg-white border px-3 py-2" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Rank</label>
                  <select 
                    name="rank"
                    value={formData.rank}
                    onChange={handleChange}
                    className="w-full border-slate-300 rounded-lg text-sm focus:ring-police-blue bg-white border px-3 py-2"
                  >
                    <option value="">Select Rank</option>
                    <option value="Constable">Constable</option>
                    <option value="Sergeant">Sergeant</option>
                    <option value="Inspector">Inspector</option>
                    <option value="Chief Inspector">Chief Inspector</option>
                    <option value="Superintendent">Superintendent</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Branch</label>
                  <select 
                    name="branch"
                    value={formData.branch}
                    onChange={handleChange}
                    className="w-full border-slate-300 rounded-lg text-sm focus:ring-police-blue bg-white border px-3 py-2"
                  >
                    <option value="">Select Branch</option>
                    <option value="Crime">Crime</option>
                    <option value="Traffic">Traffic</option>
                    <option value="Admin">Admin</option>
                    <option value="Raid">Raid</option>
                    <option value="Narcotics">Narcotics</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-slate-700 mb-1">Profile Picture URL</label>
                  <input 
                    type="url" 
                    name="profilePicture"
                    value={formData.profilePicture} 
                    onChange={handleChange}
                    className="w-full border-slate-300 rounded-lg text-sm focus:ring-police-blue bg-white border px-3 py-2" 
                    placeholder="https://example.com/your-photo.jpg"
                  />
                </div>
              </div>
              
              <div className="pt-2 flex justify-end">
                <Button 
                  variant="primary" 
                  onClick={handleSave} 
                  disabled={isSaving}
                  className="flex items-center gap-2"
                >
                  {isSaving ? (
                    <><Loader2 size={16} className="animate-spin" /> Saving...</>
                  ) : (
                    <><Save size={16} /> Save Changes</>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Station Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
               <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Predictive Analytics Retraining Interval</label>
                  <select className="w-full md:w-1/2 border-slate-300 rounded-lg text-sm focus:ring-police-blue bg-white border px-3 py-2">
                    <option>Every 24 Hours</option>
                    <option>Every 12 Hours</option>
                    <option>Real-time (High resource usage)</option>
                  </select>
                  <p className="text-xs text-slate-500 mt-2">Adjusting this impacts the GIS hotspot calculation and predictive model up-to-date accuracy.</p>
                </div>
            </CardContent>
          </Card>

        </div>
      </div>
    </div>
  );
}
