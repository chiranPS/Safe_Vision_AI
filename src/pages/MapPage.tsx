import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { MapContainer, TileLayer, Circle, CircleMarker, Popup, ZoomControl, Tooltip as LeafletTooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Layers, MapPin, Search, Loader2, Calendar, TrendingUp, TrendingDown, ChevronRight, Activity } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import HotspotAnalyticsModal from '../components/modals/HotspotAnalyticsModal';

export default function MapPage() {
  const { token } = useAuth();
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [individualIncidents, setIndividualIncidents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  const [viewMode, setViewMode] = useState<'heat' | 'pins'>('heat');
  const [timeframe, setTimeframe] = useState('month');
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [selectedHotspot, setSelectedHotspot] = useState<any>(null);

  const colomboCenter: [number, number] = [6.8971, 79.8712];

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const queryParams = new URLSearchParams({
          timeframe,
          ...(categoryFilter !== 'All' && { category: categoryFilter }),
          ...(statusFilter !== 'All' && { status: statusFilter })
        });

        // 1. Fetch Aggregated Hotspots
        const hotspotRes = await fetch(`/api/complaints/hotspots?${queryParams.toString()}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const hotspotData = await hotspotRes.json();
        setHotspots(Array.isArray(hotspotData) ? hotspotData : []);

        // 2. Fetch Individual Incidents (for pin mode)
        const incidentRes = await fetch(`/api/complaints?${queryParams.toString()}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const incidentData = await incidentRes.json();
        const validIncidents = Array.isArray(incidentData) ? incidentData : [];
        setIndividualIncidents(validIncidents.filter((c: any) => c.latitude && c.longitude));

      } catch (error) {
        console.error("Failed to fetch map data", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [token, timeframe, categoryFilter, statusFilter]);

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Critical': return '#ef4444';
      case 'High': return '#f97316';
      case 'Medium': return '#f59e0b';
      case 'Low': return '#10b981';
      default: return '#3b82f6';
    }
  };

  const filteredHotspots = hotspots.filter(h => 
    h.area.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header & Main Filters */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-6 shrink-0">
        <div>
          <h2 className="text-2xl font-bold text-police-900 tracking-tight flex items-center gap-2">
            Advanced Hotspot Intelligence
            <Badge variant="secondary" className="bg-blue-100 text-blue-700 font-bold">GIS v2.0</Badge>
          </h2>
          <p className="text-slate-500 text-sm">Predictive crime density mapping and operational resource visualization.</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
          {/* Timeframe Toggle */}
          <div className="flex items-center bg-white border border-slate-200 rounded-lg p-1 shadow-sm">
            {['week', 'month', '3months'].map((t) => (
              <button
                key={t}
                onClick={() => setTimeframe(t)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  timeframe === t ? 'bg-police-blue text-white shadow-sm' : 'text-slate-500 hover:text-police-blue'
                }`}
              >
                {t === '3months' ? '3 Months' : t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>

          <div className="flex gap-2 bg-white p-1 rounded-lg border border-slate-200 shadow-sm">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setViewMode('heat')}
              className={viewMode === 'heat' ? 'bg-slate-100' : ''}
            >
              <Layers size={16} className="mr-2"/> Density Zones
            </Button>
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setViewMode('pins')}
              className={viewMode === 'pins' ? 'bg-slate-100' : ''}
            >
              <MapPin size={16} className="mr-2"/> Case Markers
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col lg:flex-row gap-6 overflow-hidden">
        {/* Map Container */}
        <Card className="flex-1 overflow-hidden relative border-slate-300 shadow-lg">
           {/* Floating Map Controls */}
           <div className="absolute top-4 left-4 z-[400] bg-white rounded-lg shadow-xl border border-slate-200 p-2 flex flex-col sm:flex-row gap-2">
             <div className="relative">
              <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
              <input 
                type="text" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search zones..." 
                className="pl-9 pr-3 py-1.5 text-sm border border-slate-200 rounded focus:outline-none focus:ring-2 focus:ring-police-blue/20 w-full sm:w-48" 
              />
             </div>
             <select 
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="text-sm border border-slate-200 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-police-blue/20"
             >
               <option value="All">All Categories</option>
               <option value="Theft">Theft</option>
               <option value="Assault">Assault</option>
               <option value="Narcotics">Narcotics</option>
               <option value="Traffic">Traffic</option>
               <option value="Domestic Violence">Domestic Violence</option>
             </select>
             <select 
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-sm border border-slate-200 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-police-blue/20"
             >
               <option value="All">All Statuses</option>
               <option value="Pending">Pending</option>
               <option value="In Progress">In Progress</option>
               <option value="Resolved">Resolved</option>
             </select>
           </div>
           
           <div className="h-full w-full bg-slate-100 z-0 relative">
             <MapContainer center={colomboCenter} zoom={13} zoomControl={false} style={{ height: '100%', width: '100%', zIndex: 1 }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />
                <ZoomControl position="bottomright" />
                
                {viewMode === 'heat' ? (
                  // Hotspot Density Zones (Aggregated)
                  filteredHotspots.map((hotspot) => (
                    <React.Fragment key={hotspot.area}>
                      {/* Outer glow circle for density effect */}
                      <Circle
                        center={[hotspot.lat, hotspot.lng]}
                        pathOptions={{ 
                          color: getRiskColor(hotspot.riskLevel), 
                          fillColor: getRiskColor(hotspot.riskLevel),
                          fillOpacity: 0.15,
                          weight: 0
                        }}
                        radius={400 + (hotspot.count * 10)}
                        eventHandlers={{
                          click: () => setSelectedHotspot(hotspot)
                        }}
                      />
                      {/* Core density marker */}
                      <CircleMarker 
                        center={[hotspot.lat, hotspot.lng]} 
                        pathOptions={{ 
                          color: getRiskColor(hotspot.riskLevel), 
                          fillColor: getRiskColor(hotspot.riskLevel),
                          fillOpacity: 0.7,
                          weight: 3
                        }} 
                        radius={15 + Math.min(hotspot.count * 1.5, 20)}
                        eventHandlers={{
                          click: () => setSelectedHotspot(hotspot)
                        }}
                      >
                        <LeafletTooltip direction="top" offset={[0, -10]} opacity={1}>
                          <div className="font-bold">{hotspot.area}</div>
                          <div className="text-xs text-slate-500">{hotspot.count} cases • {hotspot.trend > 0 ? '+' : ''}{hotspot.trend}%</div>
                        </LeafletTooltip>
                      </CircleMarker>
                    </React.Fragment>
                  ))
                ) : (
                  // Individual Pin Mode
                  individualIncidents.map((complaint) => (
                    <CircleMarker 
                      key={complaint.id}
                      center={[complaint.latitude, complaint.longitude]} 
                      pathOptions={{ 
                        color: getRiskColor(complaint.priority), 
                        fillColor: getRiskColor(complaint.priority),
                        fillOpacity: 0.8,
                        weight: 2
                      }} 
                      radius={6}
                    >
                      <Popup>
                        <div className="p-1">
                          <h4 className="font-bold mb-1">{complaint.category}</h4>
                          <p className="text-xs text-slate-600 mb-2">{complaint.location}</p>
                          <Button 
                            onClick={() => window.location.href = `/complaint/${complaint.id}`}
                            variant="link" size="sm" className="p-0 h-auto text-blue-600"
                          >
                            View Details
                          </Button>
                        </div>
                      </Popup>
                    </CircleMarker>
                  ))
                )}

                {/* Mock Dispatch Units Overlay */}
                {[
                  { id: 'V-101', pos: [6.905, 79.865], status: 'Active' },
                  { id: 'V-204', pos: [6.885, 79.885], status: 'Responding' }
                ].map(unit => (
                  <CircleMarker 
                    key={unit.id}
                    center={unit.pos as [number, number]}
                    pathOptions={{ color: '#0f172a', fillColor: '#0f172a', fillOpacity: 1 }}
                    radius={4}
                  >
                    <LeafletTooltip permanent direction="right" className="bg-slate-900 text-white border-0 text-[10px] px-1 py-0 shadow-none">
                      {unit.id}
                    </LeafletTooltip>
                  </CircleMarker>
                ))}
             </MapContainer>
             
             {/* Map Stats HUD */}
             <div className="absolute top-4 right-4 z-[400] flex flex-col gap-2">
                <Card className="bg-white/90 backdrop-blur-sm shadow-lg border-slate-200">
                  <CardContent className="p-3 py-2 flex items-center gap-3">
                    <div className="bg-blue-100 p-1.5 rounded-full text-blue-600">
                      <Activity size={16} />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-500 uppercase leading-none mb-1">Active Cases</p>
                      <p className="text-lg font-bold text-police-900 leading-none">{individualIncidents.length}</p>
                    </div>
                  </CardContent>
                </Card>
             </div>

             {/* Legend */}
             <div className="absolute bottom-4 left-4 z-[400] bg-white/90 backdrop-blur-sm rounded-lg shadow-md border border-slate-200 p-3 text-xs min-w-[120px]">
                <div className="font-bold mb-2 text-slate-700 flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-police-blue animate-pulse"></div>
                  Risk Levels
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-red-500"></div> Critical</div>
                  <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-orange-500"></div> High</div>
                  <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-yellow-500"></div> Medium</div>
                  <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-green-500"></div> Low</div>
                </div>
             </div>
           </div>
        </Card>

        {/* Intelligence Sidebar */}
        <div className="w-full lg:w-96 flex flex-col gap-4 overflow-y-auto pr-1 shrink-0">
          <div className="flex justify-between items-center sticky top-0 bg-slate-50 py-1 z-10 border-b border-slate-200 mb-2">
            <h3 className="font-bold text-police-900 uppercase text-xs tracking-wider flex items-center gap-2">
              <TrendingUp size={14} className="text-police-blue" />
              Hotspot Analysis ({filteredHotspots.length})
            </h3>
            <Badge variant="outline" className="text-[10px]">{timeframe === 'week' ? 'Past 7 Days' : timeframe === 'month' ? 'Past 30 Days' : 'Past 90 Days'}</Badge>
          </div>
          
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400 bg-white rounded-2xl border border-slate-100 shadow-sm">
              <Loader2 className="animate-spin mb-4 text-police-blue" size={32} />
              <p className="text-sm font-medium">Analyzing spatiotemporal patterns...</p>
            </div>
          ) : filteredHotspots.length === 0 ? (
            <div className="text-sm text-slate-500 p-10 text-center bg-white rounded-2xl border border-dashed border-slate-300">
              <div className="bg-slate-50 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-300">
                <Search size={24} />
              </div>
              <p className="font-semibold text-slate-600">No Hotspots Detected</p>
              <p className="text-xs mt-1">Try adjusting the timeframe or category filters.</p>
            </div>
          ) : (
            <div className="space-y-3 pb-6">
              {filteredHotspots.map(spot => (
                <Card 
                  key={spot.area} 
                  className="group relative cursor-pointer border-slate-200 hover:border-police-blue hover:shadow-xl transition-all duration-300 overflow-hidden"
                  onClick={() => setSelectedHotspot(spot)}
                >
                  {/* Risk Level Vertical Accent */}
                  <div 
                    className="absolute left-0 top-0 bottom-0 w-1.5"
                    style={{ backgroundColor: getRiskColor(spot.riskLevel) }}
                  />
                  
                  <CardContent className="p-4 pl-5">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1 min-w-0 mr-2">
                        <h4 className="font-bold text-police-900 group-hover:text-police-blue transition-colors truncate text-sm">
                          {spot.area}
                        </h4>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <Badge variant="outline" className="text-[9px] font-bold px-1 py-0 h-4 bg-slate-50 text-slate-500 border-slate-200">
                            ID: {spot.area.substring(0,3).toUpperCase()}
                          </Badge>
                          <span className="text-[10px] text-slate-400 font-medium">
                            {spot.count} incidents
                          </span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end">
                        <Badge 
                          className="text-[9px] px-1.5 py-0 h-4 font-bold"
                          style={{ 
                            backgroundColor: getRiskColor(spot.riskLevel) + '20', 
                            color: getRiskColor(spot.riskLevel),
                            border: `1px solid ${getRiskColor(spot.riskLevel)}40` 
                          }}
                        >
                          {spot.riskLevel}
                        </Badge>
                        <div className={`flex items-center mt-1.5 text-[10px] font-bold ${spot.trend > 0 ? 'text-rose-500' : 'text-emerald-500'}`}>
                          {spot.trend > 0 ? <TrendingUp size={10} className="mr-0.5" /> : <TrendingDown size={10} className="mr-0.5" />}
                          {Math.abs(spot.trend)}%
                        </div>
                      </div>
                    </div>
                    
                    {/* Risk Bar Preview */}
                    <div className="mb-4">
                      <div className="flex justify-between text-[9px] text-slate-400 mb-1 font-bold uppercase tracking-wider">
                        <span>Cluster Risk Density</span>
                        <span>{(spot.avgRiskScore * 100).toFixed(0)}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full rounded-full transition-all duration-500"
                          style={{ 
                            width: `${spot.avgRiskScore * 100}%`,
                            backgroundColor: getRiskColor(spot.riskLevel)
                          }}
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex gap-1 overflow-hidden">
                        {spot.topCategories.map((cat: string) => (
                          <span key={cat} className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded font-medium whitespace-nowrap">
                            {cat}
                          </span>
                        ))}
                      </div>
                      <div className="bg-slate-50 group-hover:bg-police-blue/10 p-1 rounded-full transition-colors">
                        <ChevronRight size={14} className="text-slate-300 group-hover:text-police-blue group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          
          <div className="mt-auto pt-4 text-[10px] text-slate-400 border-t border-slate-200 leading-relaxed italic">
            * Hotspot detection is based on spatiotemporal density clustering within the selected {timeframe === 'week' ? '7' : timeframe === 'month' ? '30' : '90'} day window.
          </div>
        </div>
      </div>

      {/* Hotspot Analytics Modal */}
      {selectedHotspot && (
        <HotspotAnalyticsModal 
          hotspot={selectedHotspot} 
          timeframe={timeframe} 
          onClose={() => setSelectedHotspot(null)} 
        />
      )}
    </div>
  );
}
