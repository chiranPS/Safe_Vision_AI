import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { X, TrendingUp, TrendingDown, MapPin, AlertCircle, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface HotspotAnalyticsModalProps {
  hotspot: any;
  onClose: () => void;
  timeframe: string;
}

export default function HotspotAnalyticsModal({ hotspot, onClose, timeframe }: HotspotAnalyticsModalProps) {
  const [recommendation, setRecommendation] = React.useState('');
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    if (!hotspot) return;
    
    let isMounted = true;
    setLoading(true);
    
    // Fallback recommendation
    const fallback = `Deploy additional ${hotspot.topCategories[0] === 'Traffic' ? 'Traffic Units' : 'Patrol Units'} to the ${hotspot.area} corridor during peak evening hours.`;
    
    fetch('/api/hotspots/insight', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        area: hotspot.area,
        count: hotspot.count,
        topCategories: hotspot.topCategories,
        totalRiskScore: hotspot.totalRiskScore,
        trend: hotspot.trend,
        lat: hotspot.lat,
        lng: hotspot.lng
      })
    })
    .then(res => res.json())
    .then(data => {
      if (isMounted) {
        setRecommendation(data.recommendation || fallback);
        setLoading(false);
      }
    })
    .catch(err => {
      console.error(err);
      if (isMounted) {
        setRecommendation(fallback);
        setLoading(false);
      }
    });

    return () => { isMounted = false; };
  }, [hotspot]);

  if (!hotspot) return null;

  const categoryData = Object.entries(hotspot.categories).map(([name, count]) => ({
    name,
    count: count as number
  })).sort((a, b) => b.count - a.count);

  const colors = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#f43f5e'];

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        <CardHeader className="bg-police-900 text-white shrink-0">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="bg-white/20 p-2 rounded-lg">
                <MapPin size={24} />
              </div>
              <div>
                <CardTitle className="text-xl text-white">{hotspot.area} Hotspot Analytics</CardTitle>
                <p className="text-slate-300 text-sm">Zone Analysis • Last {timeframe.replace('3months', '3 Months')}</p>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} className="text-white hover:bg-white/10">
              <X size={24} />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="overflow-y-auto p-6 bg-slate-50">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-white shadow-sm border-slate-200">
              <CardContent className="p-4">
                <p className="text-xs font-bold text-slate-500 uppercase mb-1">Total Incidents</p>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-bold text-police-900">{hotspot.count}</span>
                  <div className={`flex items-center text-xs mb-1 ${hotspot.trend > 0 ? 'text-red-500' : 'text-green-500'}`}>
                    {hotspot.trend > 0 ? <TrendingUp size={14} className="mr-0.5" /> : <TrendingDown size={14} className="mr-0.5" />}
                    {Math.abs(hotspot.trend)}%
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white shadow-sm border-slate-200">
              <CardContent className="p-4">
                <p className="text-xs font-bold text-slate-500 uppercase mb-1">Risk Severity</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant={hotspot.riskLevel === 'Critical' ? 'destructive' : hotspot.riskLevel === 'High' ? 'warning' : 'default'} className="px-3 py-1 text-sm">
                    {hotspot.riskLevel}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white shadow-sm border-slate-200">
              <CardContent className="p-4">
                <p className="text-xs font-bold text-slate-500 uppercase mb-1">Avg Risk Score</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-2xl font-bold">{(hotspot.avgRiskScore * 100).toFixed(0)}%</span>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${hotspot.avgRiskScore > 0.7 ? 'bg-red-500' : hotspot.avgRiskScore > 0.4 ? 'bg-orange-500' : 'bg-green-500'}`}
                      style={{ width: `${hotspot.avgRiskScore * 100}%` }}
                    ></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white shadow-sm border-slate-200">
              <CardContent className="p-4">
                <p className="text-xs font-bold text-slate-500 uppercase mb-1">Primary Type</p>
                <span className="text-lg font-bold text-slate-800 truncate block mt-1">{hotspot.topCategories[0]}</span>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-white shadow-sm border-slate-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <BarChart3 size={16} className="text-police-blue" />
                  Incident Distribution
                </CardTitle>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={categoryData} layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                    <XAxis type="number" hide />
                    <YAxis 
                      dataKey="name" 
                      type="category" 
                      tick={{ fontSize: 11, fontWeight: 500 }} 
                      width={100}
                    />
                    <Tooltip 
                      cursor={{ fill: '#f1f5f9' }}
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={24}>
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="space-y-4">
              <Card className="bg-white shadow-sm border-slate-200">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-bold flex items-center gap-2 text-slate-700">
                    <AlertCircle size={16} className="text-amber-500" />
                    Operational Insights
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="p-3 bg-amber-50 rounded-lg border border-amber-100 text-sm text-amber-900">
                    <strong>Trend Warning:</strong> {hotspot.trend > 0 
                      ? `Incidents have increased by ${hotspot.trend}% compared to the previous period.` 
                      : `Incidents have decreased by ${Math.abs(hotspot.trend)}% compared to the previous period.`}
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-100 text-sm text-blue-900">
                    <strong>Recommendation:</strong> {loading ? <span className="animate-pulse">Analyzing hotspot data...</span> : recommendation}
                  </div>
                </CardContent>
              </Card>

              <div className="flex gap-2">
                <Button className="flex-1 bg-police-blue hover:bg-police-900" size="lg">Generate Detail Report</Button>
                <Button variant="outline" className="flex-1 border-slate-300" size="lg">Dispatch Task Force</Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
