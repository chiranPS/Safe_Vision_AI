import React from 'react';
import { Search, Bell, Menu, UserCircle } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { useAuth } from '../../contexts/AuthContext';

const TopHeader: React.FC = () => {
  const { user, logout } = useAuth();
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 z-10 sticky top-0">
      <div className="flex items-center gap-4">
        {/* Mobile menu button (placeholder) */}
        <button className="md:hidden text-slate-500 hover:text-slate-700">
          <Menu size={20} />
        </button>
        
        {/* Search */}
        <div className="hidden md:flex relative group">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search size={16} className="text-slate-400 group-focus-within:text-police-blue" />
          </div>
          <input 
            type="text" 
            placeholder="Search cases, officers, or locations..." 
            className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-police-blue focus:border-transparent w-64 lg:w-96 transition-all bg-slate-50 hover:bg-white focus:bg-white"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Notifications */}
        <button className="relative p-2 text-slate-500 hover:bg-slate-100 rounded-full transition-colors">
          <Bell size={20} />
          <span className="absolute top-1.5 right-1.5 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-risk-critical opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-risk-critical"></span>
          </span>
        </button>

        <div className="w-px h-6 bg-slate-200 hidden md:block"></div>

        {/* Profile */}
        <div className="flex items-center gap-3">
          <div className="hidden md:flex flex-col items-end">
            <span className="text-sm font-semibold text-slate-700">
              {user?.rank ? `${user.rank}. ` : ''}{user?.name || 'Officer'}
            </span>
            <Badge variant="default" className="text-[10px] px-1.5 py-0 h-4 mt-0.5 border-slate-300 text-slate-500">
              {user?.branch || 'General'}
            </Badge>
          </div>
          <UserCircle size={32} className="text-slate-400" />
          
          <button 
            onClick={() => logout()}
            className="ml-2 text-xs font-medium text-red-500 hover:text-red-700 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

export default TopHeader;
