import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  ShieldAlert, 
  LayoutDashboard, 
  FileText, 
  Files, 
  PieChart, 
  Activity, 
  Map as MapIcon, 
  FileBarChart2, 
  Settings,
  LogOut,
  LucideIcon
} from 'lucide-react';
import { cn } from '../../utils/cn';

interface NavItem {
  path: string;
  icon: LucideIcon;
  label: string;
}

const navItems: NavItem[] = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/intake', icon: FileText, label: 'Complaint Intake OCR' },
  { path: '/management', icon: Files, label: 'Case Management' },
  { path: '/analytics', icon: PieChart, label: 'Analytics Insights' },
  { path: '/risk', icon: Activity, label: 'Predictive Risk' },
  { path: '/map', icon: MapIcon, label: 'GIS Map Hotspots' },
  { path: '/reports', icon: FileBarChart2, label: 'Reports' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

const Sidebar: React.FC = () => {
  return (
    <div className="w-64 bg-police-900 border-r border-police-800 flex flex-col h-full text-slate-300">
      {/* Brand */}
      <div className="h-16 flex items-center px-6 border-b border-police-800">
        <div className="flex items-center gap-3 text-white">
          <div className="bg-police-blue p-1.5 rounded-lg">
            <ShieldAlert size={20} className="text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight">Safe-Vision AI</span>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto py-6 flex flex-col gap-1 px-3">
        <div className="px-3 md:mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Main Menu
        </div>
        
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group",
                isActive 
                  ? "bg-police-800/80 text-white shadow-sm" 
                  : "hover:bg-police-800/50 hover:text-white"
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon 
                  size={18} 
                  className={cn("transition-colors", isActive ? "text-police-blue-light" : "text-slate-400 group-hover:text-slate-300")} 
                />
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </div>

      {/* Footer Nav */}
      <div className="p-4 border-t border-police-800 pb-6">
        <NavLink
            to="/login"
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all hover:bg-police-800/50 hover:text-white text-slate-400 group"
        >
          <LogOut size={18} className="group-hover:text-red-400 transition-colors" />
          Logout
        </NavLink>
      </div>
    </div>
  );
}

export default Sidebar;
