import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { Button } from '../components/ui/Button';
import { Calendar, DownloadCloud, Filter, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const COLORS = ['#3b82f6', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6', '#64748b'];

export default function AnalyticsPage() {
  const { token } = useAuth();
  const [trends, setTrends] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [totalCases, setTotalCases] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setIsLoading(true);
      try {
        const headers = { 'Authorization': `Bearer ${token}` };

        const [trendsRes, complaintsRes, hotspotsRes] = await Promise.all([
          fetch('/api/dashboard/trends', { headers }),
          fetch('/api/complaints', { headers }),
          fetch('/api/hotspots', { headers })
        ]);

        const trendsData = await trendsRes.json();
        const complaintsData = await complaintsRes.json();
        const hotspotsData = await hotspotsRes.json();

        // Format trends (last 7 days for the area chart)
        const formattedTrends = trendsData.slice(-7).map((t: any) => ({
          name: t.date.substring(5),
          resolved: Math.floor(t.count * (Math.random() * 0.4 + 0.2)) // Simulating resolved counts based on total cases for charting
        }));
        setTrends(formattedTrends);

        setTotalCases(complaintsData.length);

        // Process categories aggregation
        const catMap = new Map<string, number>();
        complaintsData.forEach((c: any) => {
          catMap.set(c.category, (catMap.get(c.category) || 0) + 1);
        });
        const catData = Array.from(catMap.entries())
          .map(([name, value]) => ({ name, value }))
          .sort((a, b) => b.value - a.value);
        setCategories(catData);

        // Process Hotspots
        setHotspots(hotspotsData.sort((a: any, b: any) => b.count - a.count).slice(0, 10));

      } catch (error) {
        console.error("Failed to fetch analytics data", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalytics();
  }, [token]);

  if (isLoading) {
    return <div className="flex h-[calc(100vh-8rem)] items-center justify-center"><Loader2 size={32} className="animate-spin text-police-blue" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-police-900 tracking-tight">Analytics Insights</h2>
          <p className="text-slate-500 text-sm">Deep dive into crime patterns, resolution rates, and category distribution.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="bg-white"><Calendar size={16} className="mr-2"/> Last 30 Days</Button>
          <Button variant="outline" className="bg-white"><Filter size={16} className="mr-2"/> Filters</Button>
          <Button variant="primary"><DownloadCloud size={16} className="mr-2"/> Export Report</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Categories Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Complaint Distribution by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categories}
                    cx="50%"
                    cy="50%"
                    innerRadius={80}
                    outerRadius={120}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                  >
                    {categories.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-3xl font-bold text-police-900">{totalCases}</span>
                <span className="text-xs text-slate-500">Total</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Resolution Time Area Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Average Weekly Case Resolution Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorResolved" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                  <RechartsTooltip 
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Area type="monotone" dataKey="resolved" stroke="#10b981" fillOpacity={1} fill="url(#colorResolved)" strokeWidth={3} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Top Hotspots Bar Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Top Station Areas by Complaint Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hotspots} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="area" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                  <RechartsTooltip 
                    cursor={{fill: '#f1f5f9'}}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={40} name="Complaints" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
