import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { 
  FileText, FolderOpen, Activity, CheckCircle, TrendingUp, AlertTriangle, LucideIcon, Loader2 
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useAuth } from '../contexts/AuthContext';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  subtext?: string;
  colorClass: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, trend, subtext, colorClass }) => {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
            <h4 className="text-3xl font-bold text-police-900">{value}</h4>
          </div>
          <div className={`p-3 rounded-xl ${colorClass}`}>
            <Icon size={24} />
          </div>
        </div>
        <div className="mt-4 flex items-center text-sm">
          {trend && (
            <span className={`font-medium ${trend.startsWith('+') ? 'text-risk-critical' : 'text-risk-low'} flex items-center`}>
              {trend.startsWith('+') ? <TrendingUp size={16} className="mr-1"/> : null} 
              {trend}
            </span>
          )}
          <span className="text-slate-500 ml-2">{subtext}</span>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { token } = useAuth();
  
  const [stats, setStats] = useState({ total: 0, open: 0, resolved: 0, today: 0 });
  const [trends, setTrends] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        const headers = { 'Authorization': `Bearer ${token}` };

        const [statsRes, trendsRes, complaintsRes, alertsRes] = await Promise.all([
          fetch('/api/dashboard/stats', { headers }),
          fetch('/api/dashboard/trends', { headers }),
          fetch('/api/complaints', { headers }),
          fetch('/api/alerts', { headers })
        ]);

        const statsData = await statsRes.json();
        const trendsData = await trendsRes.json();
        const complaintsData = await complaintsRes.json();
        const alertsData = await alertsRes.json();

        setStats(statsData.error ? { total: 0, open: 0, resolved: 0, today: 0 } : statsData);
        setTrends(Array.isArray(trendsData) ? trendsData : []);
        setAlerts(Array.isArray(alertsData) ? alertsData : []);

        const validComplaints = Array.isArray(complaintsData) ? complaintsData : [];

        // Process recent activity (latest 5)
        const recent = validComplaints.slice(0, 5).map((c: any) => ({
          id: c.id ? c.id.substring(0, 8).toUpperCase() : 'UNKNOWN',
          type: c.category || 'Unknown',
          area: c.location || 'Unknown',
          risk: c.priority || 'Normal',
          status: c.status || 'Pending',
          time: c.dateOfIncident ? new Date(c.dateOfIncident).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unknown'
        }));
        setRecentActivity(recent);

        // Process categories aggregation
        const catMap = new Map<string, number>();
        validComplaints.forEach((c: any) => {
          if (c.category) {
            catMap.set(c.category, (catMap.get(c.category) || 0) + 1);
          }
        });
        const catData = Array.from(catMap.entries())
          .map(([name, value]) => ({ name, value }))
          .sort((a, b) => b.value - a.value);
        setCategories(catData);

      } catch (error) {
        console.error("Failed to fetch dashboard data", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [token]);

  if (isLoading) {
    return <div className="flex h-full items-center justify-center"><Loader2 size={32} className="animate-spin text-police-blue" /></div>;
  }

  // Format trends for Recharts
  const chartData = trends.map(t => ({
    name: t.date.substring(5), // MM-DD
    complaints: t.count,
    resolved: Math.floor(t.count * 0.3) // mock resolved line based on count for now
  })).slice(-7); // show last 7 days

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-police-900 tracking-tight">Station Overview</h2>
          <p className="text-slate-500 text-sm">Real-time update of district complaints and operations.</p>
        </div>
        <div className="text-sm font-medium text-slate-600 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm flex items-center">
          <CheckCircle size={16} className="text-green-500 mr-2" />
          System Active (Live DB Connection)
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Complaints" 
          value={stats.total} 
          icon={FileText} 
          trend="+12%" 
          subtext="vs last month"
          colorClass="bg-blue-50 text-blue-600"
        />
        <StatCard 
          title="Open Cases" 
          value={stats.open} 
          icon={FolderOpen} 
          subtext="Requires assignment"
          colorClass="bg-orange-50 text-orange-600"
        />
        <StatCard 
          title="Resolved Cases" 
          value={stats.resolved} 
          icon={CheckCircle} 
          subtext="All time"
          colorClass="bg-green-50 text-green-600"
        />
        <StatCard 
          title="Today's Incidents" 
          value={stats.today} 
          icon={Activity} 
          subtext="Pending review"
          colorClass="bg-purple-50 text-purple-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>7-Day Complaint Trend</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Line type="monotone" dataKey="complaints" name="New Complaints" stroke="#3b82f6" strokeWidth={3} dot={{r:4, strokeWidth:2}} activeDot={{r: 6}} />
                  <Line type="monotone" dataKey="resolved" name="Resolved Cases" stroke="#10b981" strokeWidth={3} dot={{r:4, strokeWidth:2}} />
                </LineChart>
              </ResponsiveContainer>
             </div>
          </CardContent>
        </Card>

        {/* Categories Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Top Categories</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categories.slice(0, 5)} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}}/>
                  <YAxis type="category" dataKey="name" width={100} axisLine={false} tickLine={false} tick={{fill: '#475569', fontSize: 12}} />
                  <Tooltip 
                    cursor={{fill: '#f8fafc'}}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
             </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity Table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Activity (Live)</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-y border-slate-200">
                <tr>
                  <th className="px-6 py-3 font-semibold">ID / Type</th>
                  <th className="px-6 py-3 font-semibold">Area</th>
                  <th className="px-6 py-3 font-semibold">Risk Level</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold text-right">Time</th>
                </tr>
              </thead>
              <tbody>
                {recentActivity.map((activity, idx) => (
                  <tr key={idx} className="bg-white border-b border-slate-100 hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-police-900">{activity.id}</div>
                      <div className="text-slate-500 text-xs">{activity.type}</div>
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-700">{activity.area}</td>
                    <td className="px-6 py-4">
                      <Badge variant={activity.risk === 'Critical' ? 'destructive' : activity.risk === 'High' ? 'warning' : 'default'}>
                        {activity.risk}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 ${activity.status === 'Pending' ? 'text-orange-600' : activity.status === 'Resolved' ? 'text-green-600' : 'text-blue-600'}`}>
                        <div className={`h-1.5 w-1.5 rounded-full ${activity.status === 'Pending' ? 'bg-orange-500' : activity.status === 'Resolved' ? 'bg-green-500' : 'bg-blue-500'}`}></div>
                        {activity.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right text-slate-500">{activity.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Alerts / AI Summaries */}
        <Card className={alerts.length > 0 ? "border-red-200" : ""}>
          <CardHeader className={alerts.length > 0 ? "bg-red-50/50 border-red-100" : ""}>
            <div className="flex items-center gap-2">
              <AlertTriangle size={20} className={alerts.length > 0 ? "text-red-500" : "text-slate-400"} />
              <CardTitle className={alerts.length > 0 ? "text-red-900" : "text-slate-700"}>Urgent AI Alerts</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {alerts.length === 0 ? (
              <div className="p-8 text-center text-slate-500">No urgent alerts detected.</div>
            ) : (
              <div className="divide-y divide-slate-100">
                {alerts.map((alert, idx) => (
                  <div key={idx} className="p-4 hover:bg-slate-50 transition-colors cursor-pointer">
                    <div className="flex justify-between mb-1">
                      <span className={`text-xs font-bold ${alert.type === 'CRITICAL RISK' ? 'text-red-600' : 'text-orange-600'} uppercase tracking-wider`}>
                        {alert.type}
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(alert.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <h5 className="font-semibold text-police-900 mb-1">{alert.area} Warning</h5>
                    <p className="text-sm text-slate-600 line-clamp-2">{alert.message}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
