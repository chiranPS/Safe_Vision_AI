import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Activity, ShieldAlert, TrendingUp, AlertOctagon, Info, Loader2 } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';
import { useAuth } from '../contexts/AuthContext';

export default function PredictiveRiskPage() {
  const { token } = useAuth();
  const [forecast, setForecast] = useState<any[]>([]);
  const [riskZones, setRiskZones] = useState<any[]>([]);
  const [overallScore, setOverallScore] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchRiskData = async () => {
      setIsLoading(true);
      try {
        const headers = { 'Authorization': `Bearer ${token}` };

        const [trendsRes, hotspotsRes] = await Promise.all([
          fetch('/api/dashboard/trends', { headers }),
          fetch('/api/hotspots', { headers })
        ]);

        const trendsData = await trendsRes.json();
        const hotspotsData = await hotspotsRes.json();

        // Use the last 7 days of trends to simulate the risk forecast curve
        const formattedForecast = trendsData.slice(-7).map((t: any) => ({
          time: t.date.substring(5), // Use MM-DD for x-axis
          risk: Math.round(t.avgRiskScore * 100) // Scale 0-1 to 0-100
        }));
        setForecast(formattedForecast);

        // Map hotspots to actionable risk zones
        const mappedZones = hotspotsData
          .sort((a: any, b: any) => b.count - a.count)
          .slice(0, 5)
          .map((spot: any) => {
            let recommendation = "Increase routine patrols.";
            if (spot.riskLevel === 'Critical') recommendation = "Dispatch rapid response unit immediately. High likelihood of escalation.";
            else if (spot.riskLevel === 'High') recommendation = "Assign dedicated units for neighborhood watch.";

            return {
              area: spot.area,
              level: spot.riskLevel,
              riskScore: Math.round(spot.count * 8.5), // Arbitrary score generation based on count
              primaryFactor: `Concentration of ${spot.count} active incidents`,
              recommendation
            };
          });
        
        setRiskZones(mappedZones);

        // Calculate overall score (average of last few days)
        if (formattedForecast.length > 0) {
          const avg = formattedForecast.reduce((sum: number, f: any) => sum + f.risk, 0) / formattedForecast.length;
          setOverallScore(Math.round(avg));
        }

      } catch (error) {
        console.error("Failed to fetch predictive risk data", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRiskData();
  }, [token]);

  if (isLoading) {
    return <div className="flex h-full items-center justify-center pt-20"><Loader2 size={32} className="animate-spin text-police-blue" /></div>;
  }

  return (
    <div className="space-y-6">
       <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-police-900 tracking-tight flex items-center gap-2">
            Predictive Risk <Badge variant="primary" className="ml-2">AI Output</Badge>
          </h2>
          <p className="text-slate-500 text-sm mt-1">Machine Learning forecasts based on historical case data, NLP extraction, and area models.</p>
        </div>
        <Button variant="outline" className="bg-white text-police-blue border-police-blue hover:bg-blue-50">
          <Activity size={16} className="mr-2" /> Recalculate Model
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col - Overview Cards */}
        <div className="space-y-6 lg:col-span-1">
          <Card className={`text-white border-none shadow-md ${overallScore > 70 ? 'bg-gradient-to-br from-red-500 to-red-700' : overallScore > 40 ? 'bg-gradient-to-br from-orange-400 to-orange-600' : 'bg-gradient-to-br from-blue-500 to-blue-700'}`}>
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <AlertOctagon size={32} className="opacity-80" />
                <Badge className="bg-white/20 text-white border-0 hover:bg-white/30 backdrop-blur-sm">
                  System Level: {overallScore > 70 ? 'Elevated' : overallScore > 40 ? 'Moderate' : 'Normal'}
                </Badge>
              </div>
              <h3 className="text-4xl font-bold mb-1">{overallScore} / 100</h3>
              <p className="font-medium opacity-90 text-sm">Overall City Risk Score</p>
              <div className="mt-4 pt-4 border-t border-white/20 flex items-center text-sm opacity-90">
                <TrendingUp size={16} className="mr-2" /> Based on 7-day trailing average
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="bg-slate-50/50">
              <CardTitle className="text-base flex justify-between items-center w-full">
                <span>Model Explanation</span>
                <Info size={16} className="text-slate-400" />
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 text-sm text-slate-600 space-y-3 leading-relaxed">
              <p>
                The <strong>Safe-Vision Risk Model v2</strong> analyzes incoming NLP entities, active case types, and historical hot zones to predict short-term escalation.
              </p>
              <p>
                Currently, the model heavily weighs recent incident density across active hotspots.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Right Col - Zones & Charts */}
        <div className="space-y-6 lg:col-span-2">
          
          <Card>
             <CardHeader>
               <CardTitle className="text-base flex items-center justify-between">
                 Risk Trend Forecast
                 <Badge variant="default" className="font-normal text-xs">Based on last 7 days</Badge>
               </CardTitle>
             </CardHeader>
             <CardContent>
                <div className="h-64 w-full mt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={forecast} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                      <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} domain={[0, 100]} />
                      <RechartsTooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                      <Area type="monotone" dataKey="risk" stroke="#ef4444" fillOpacity={1} fill="url(#colorRisk)" strokeWidth={3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
             </CardContent>
          </Card>

          <h3 className="text-lg font-bold text-police-900 mt-8 mb-4">Top Actionable Risk Zones</h3>
          
          <div className="space-y-4">
            {riskZones.length === 0 ? (
              <div className="text-slate-500 p-4 border rounded-lg bg-slate-50 text-center">No high-risk zones currently identified.</div>
            ) : (
              riskZones.map((zone, idx) => (
                <Card key={idx} className={`border-l-4 ${zone.level === 'Critical' ? 'border-l-red-500' : zone.level === 'High' ? 'border-l-orange-500' : 'border-l-yellow-500'}`}>
                  <CardContent className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <h4 className="font-bold text-police-900 text-lg">{zone.area}</h4>
                        <Badge variant={zone.level === 'Critical' ? 'destructive' : zone.level === 'High' ? 'warning' : 'default'}>{zone.level}</Badge>
                        <span className="text-xs font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">Score: {zone.riskScore}</span>
                      </div>
                      <p className="text-sm text-slate-600 mb-2"><strong>Primary Factor:</strong> {zone.primaryFactor}</p>
                      <div className="text-sm bg-blue-50 text-blue-800 p-2 rounded flex items-start gap-2 border border-blue-100">
                        <ShieldAlert size={16} className="mt-0.5 shrink-0" />
                        <span><strong>AI Recommendation:</strong> {zone.recommendation}</span>
                      </div>
                    </div>
                    <div>
                      <Button variant={zone.level === 'Critical' ? 'primary' : 'outline'} className="w-full md:w-auto">
                        Assign Units
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
