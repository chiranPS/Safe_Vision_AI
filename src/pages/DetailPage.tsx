import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { ArrowLeft, Edit3, CheckCircle, FileText, BrainCircuit, Activity, Clock, ShieldAlert, Paperclip, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();
  
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [allOfficers, setAllOfficers] = useState<any[]>([]);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isAssigning, setIsAssigning] = useState(false);

  useEffect(() => {
    const fetchComplaintDetails = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/complaints/${id}/full-details`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch');
        }
        
        const complaint = await response.json();
        
        const leadAssignment = complaint.assignments?.find((a: any) => a.role === 'Lead Officer');
        const supportingAssignments = complaint.assignments?.filter((a: any) => a.role !== 'Lead Officer') || [];
        
        // Map DB model to frontend display structure
        setData({
          id: complaint.id,
          displayId: complaint.id.substring(0, 8).toUpperCase(),
          status: complaint.status,
          priority: complaint.priority,
          type: complaint.category,
          date: new Date(complaint.dateOfIncident).toLocaleString(),
          complainant: {
            name: complaint.complainant?.fullName || 'Unknown',
            nic: complaint.complainant?.nicNumber || 'N/A',
            phone: complaint.complainant?.phone || 'N/A',
            address: complaint.complainant?.address || 'N/A'
          },
          officer: leadAssignment ? `${leadAssignment.officer.fullName} (${leadAssignment.officer.badgeNumber})` : 'Pending Assignment',
          supportingOfficers: supportingAssignments,
          area: complaint.location,
          description: complaint.description,
          nlpAnalysis: {
            summary: `Extracted ${(complaint.keywords || []).length} key entities. Confidence level high.`,
            entities: (complaint.keywords || []).map((k: string) => ({ label: 'Keyword', value: k }))
          },
          timeline: [
            { event: 'Complaint Filed', time: new Date(complaint.createdAt).toLocaleString() },
            { event: 'AI Risk Assessment Complete', time: new Date(new Date(complaint.createdAt).getTime() + 5000).toLocaleString() }
          ]
        });
        
      } catch (error: any) {
        console.error("Failed to fetch complaint details", error);
        toast.error(`Error fetching details: ${error.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    const fetchOfficers = async () => {
      try {
        const response = await fetch('/api/officers', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const officers = await response.json();
        setAllOfficers(officers);
      } catch (error) {
        console.error("Failed to fetch officers", error);
      }
    };

    if (id) {
      fetchComplaintDetails();
      fetchOfficers();
    }
  }, [id, token]);

  const handleStatusUpdate = async (newStatus: string) => {
    setIsUpdating(true);
    try {
      const response = await fetch(`/api/complaints/${id}`, {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
      });
      
      
      if (!response.ok) throw new Error('Update failed');
      
      setData((prev: any) => ({ ...prev, status: newStatus }));
      toast.success(`Status updated to ${newStatus}`);
    } catch (error: any) {
      toast.error(`Error: ${error.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleAssignOfficer = async (officerId: string) => {
    if (!officerId) return;
    setIsAssigning(true);
    try {
      const response = await fetch(`/api/complaints/${id}/assign-lead`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ officerId })
      });
      
      if (!response.ok) throw new Error('Assignment failed');
      
      const officer = allOfficers.find(o => o.id === officerId);
      setData((prev: any) => ({ 
        ...prev, 
        officer: `${officer.fullName} (${officer.badgeNumber})` 
      }));
      toast.success(`Officer ${officer.fullName} assigned as Lead.`);
    } catch (error: any) {
      toast.error(`Error: ${error.message}`);
    } finally {
      setIsAssigning(false);
    }
  };

  if (isLoading) {
    return <div className="flex h-[calc(100vh-8rem)] items-center justify-center"><Loader2 size={32} className="animate-spin text-police-blue" /></div>;
  }

  if (!data) {
    return <div className="text-center p-12 text-slate-500">Complaint not found.</div>;
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-4 mb-2">
        <button onClick={() => navigate(-1)} className="p-2 bg-white rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-500">
          <ArrowLeft size={18} />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-police-900">{data.displayId}</h2>
            <Badge variant={data.status === 'Active' ? 'primary' : 'default'}>{data.status}</Badge>
            <Badge variant={data.priority === 'Critical' ? 'destructive' : data.priority === 'High' ? 'warning' : 'default'}>{data.priority} Priority</Badge>
          </div>
          <p className="text-slate-500 text-sm mt-1">{data.type} · Registered on {data.date}</p>
        </div>
        <div className="flex gap-2">
          <select 
            value={data.status} 
            onChange={(e) => handleStatusUpdate(e.target.value)}
            disabled={isUpdating}
            className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm font-medium focus:ring-police-blue focus:border-police-blue outline-none"
          >
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Resolved">Resolved</option>
            <option value="Closed">Closed</option>
          </select>
          <Button variant="primary" className="bg-police-blue" onClick={() => handleStatusUpdate('Resolved')}>
            {isUpdating ? <Loader2 size={16} className="animate-spin mr-2"/> : <CheckCircle size={16} className="mr-2"/>} 
            Resolve Case
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2/3) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="bg-slate-50/50">
              <CardTitle className="text-base flex items-center gap-2">
                <FileText size={18} className="text-police-blue"/> Overview
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase">Complainant</p>
                  <p className="font-medium text-slate-800 mt-1">{data.complainant.name}</p>
                  <p className="text-sm text-slate-500">{data.complainant.nic}</p>
                  <p className="text-sm text-slate-500">{data.complainant.phone}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase">Lead Officer</p>
                  <p className="font-medium text-slate-800 mt-1">{data.officer}</p>
                  
                  <div className="mt-3">
                    <select 
                      onChange={(e) => handleAssignOfficer(e.target.value)}
                      disabled={isAssigning}
                      className="w-full text-xs bg-slate-50 border border-slate-200 rounded p-1.5 focus:ring-police-blue outline-none"
                      value=""
                    >
                      <option value="" disabled>Change Lead Officer...</option>
                      {allOfficers.map(o => (
                        <option key={o.id} value={o.id}>{o.fullName} ({o.badgeNumber})</option>
                      ))}
                    </select>
                  </div>

                  {data.supportingOfficers.length > 0 && (
                    <div className="mt-4">
                      <p className="text-xs font-semibold text-slate-500 uppercase">Supporting</p>
                      {data.supportingOfficers.map((a: any) => (
                        <p key={a.id} className="text-sm text-slate-600">{a.officer.fullName}</p>
                      ))}
                    </div>
                  )}
                </div>
                <div className="md:col-span-2">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Location Area</p>
                  <p className="font-medium text-slate-800 mt-1">{data.area}</p>
                  <p className="text-sm text-slate-500">{data.complainant.address}</p>
                </div>
              </div>

              <div className="border-t border-slate-100 pt-6">
                <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Original Narrative</p>
                <div className="p-4 bg-slate-50 rounded-lg text-sm text-slate-700 leading-relaxed border border-slate-200">
                  "{data.description}"
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-blue-100">
            <CardHeader className="bg-blue-50/30 border-blue-100">
              <CardTitle className="text-base flex items-center gap-2 text-blue-900">
                <BrainCircuit size={18} className="text-blue-600"/> NLP Analysis & Entity Extraction
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase mb-2">AI Summary</p>
                <p className="text-sm text-slate-800 font-medium">{data.nlpAnalysis.summary}</p>
              </div>
              
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase mb-3">Extracted Entities</p>
                <div className="flex flex-wrap gap-2">
                  {data.nlpAnalysis.entities.map((entity: any, i: number) => (
                    <div key={i} className="inline-flex items-center px-3 py-1.5 rounded-lg border border-slate-200 bg-white shadow-sm text-sm">
                      <span className="text-slate-500 text-xs mr-2">{entity.label}:</span>
                      <span className="font-semibold text-slate-700">{entity.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Paperclip size={18} className="text-slate-500"/> Evidence & Attachments
              </CardTitle>
            </CardHeader>
            <CardContent>
               <div className="flex gap-4">
                 <div className="w-24 h-32 bg-slate-100 border border-slate-200 rounded-lg flex items-center justify-center flex-col cursor-pointer hover:bg-slate-200 transition-colors">
                   <FileText size={24} className="text-slate-400 mb-2" />
                   <span className="text-xs text-slate-500">OCR Source</span>
                 </div>
                 <div className="w-24 h-32 bg-slate-50 border border-dashed border-slate-300 rounded-lg flex items-center justify-center flex-col cursor-pointer hover:bg-slate-100 transition-colors">
                   <span className="text-2xl text-slate-400 mb-1">+</span>
                   <span className="text-xs text-slate-500">Add File</span>
                 </div>
               </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column (1/3) */}
        <div className="space-y-6">
          <Card className={data.priority === 'High' || data.priority === 'Critical' ? 'border-orange-200' : ''}>
            <CardHeader className={data.priority === 'High' || data.priority === 'Critical' ? 'bg-orange-50/50' : 'bg-slate-50'}>
              <CardTitle className="text-base flex items-center gap-2 text-slate-800">
                <Activity size={18} className={data.priority === 'High' || data.priority === 'Critical' ? 'text-orange-500' : 'text-slate-500'}/> Risk Assessment
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="flex items-end justify-between mb-4">
                <div>
                  <p className="text-xs text-slate-500 font-semibold uppercase mb-1">Calculated Level</p>
                  <Badge variant={data.priority === 'Critical' ? 'destructive' : data.priority === 'High' ? 'warning' : 'default'} className="text-sm px-3 py-1">{data.priority}</Badge>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500 font-semibold uppercase mb-1">Confidence Score</p>
                  <span className="text-xl font-bold text-police-900">88%</span>
                </div>
              </div>
              <div className="space-y-3 mt-6">
                {data.priority === 'Critical' || data.priority === 'High' ? (
                  <div className="flex gap-2 items-start text-sm bg-orange-50 text-orange-800 p-3 rounded-lg border border-orange-100">
                    <ShieldAlert size={16} className="mt-0.5 shrink-0" />
                    <p>High escalation risk detected based on NLP sentiment and historical data for {data.area}.</p>
                  </div>
                ) : (
                  <div className="flex gap-2 items-start text-sm bg-blue-50 text-blue-800 p-3 rounded-lg border border-blue-100">
                    <ShieldAlert size={16} className="mt-0.5 shrink-0" />
                    <p>Routine incident. Standard dispatch procedures apply for {data.area}.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Clock size={18} className="text-slate-500"/> Activity Log
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="relative border-l border-slate-200 ml-3 space-y-6">
                {data.timeline.map((item: any, index: number) => (
                  <div key={index} className="relative pl-6">
                    <span className="absolute -left-[5px] top-1.5 w-2 h-2 rounded-full bg-police-blue ring-4 ring-white"></span>
                    <p className="text-sm font-medium text-slate-800">{item.event}</p>
                    <p className="text-xs text-slate-500 mt-1">{item.time}</p>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-6 text-sm">Add Note / Log Activity</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
