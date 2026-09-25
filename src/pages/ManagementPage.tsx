import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Search, Filter, Download, MoreHorizontal, Eye, Loader2, Plus, Trash2, Edit, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

export default function ManagementPage() {
  const navigate = useNavigate();
  const { token } = useAuth();
  
  const [complaints, setComplaints] = useState<any[]>([]);
  const [filteredComplaints, setFilteredComplaints] = useState<any[]>([]);
  const [view, setView] = useState<'complaints' | 'officers'>('complaints');
  const [officers, setOfficers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isOfficersLoading, setIsOfficersLoading] = useState(false);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All Statuses');
  const [priorityFilter, setPriorityFilter] = useState('All Risk Levels');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingOfficer, setEditingOfficer] = useState<any>(null);
  const [formData, setFormData] = useState({
    fullName: '',
    badgeNumber: '',
    rank: 'Constable',
    branch: 'General Duties',
    assignedStation: 'Colombo Central',
    phone: '',
    status: 'Active'
  });

  useEffect(() => {
    const fetchComplaints = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('/api/complaints', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        setComplaints(data);
        setFilteredComplaints(data);
      } catch (error) {
        console.error("Failed to fetch complaints", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchComplaints();
    fetchOfficers();
  }, [token]);

  const fetchOfficers = async () => {
    setIsOfficersLoading(true);
    try {
      const response = await fetch('/api/officers', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setOfficers(data);
    } catch (error) {
      console.error("Failed to fetch officers", error);
    } finally {
      setIsOfficersLoading(false);
    }
  };

  const handleOpenModal = (officer: any = null) => {
    if (officer) {
      setEditingOfficer(officer);
      setFormData({
        fullName: officer.fullName,
        badgeNumber: officer.badgeNumber,
        rank: officer.rank,
        branch: officer.branch,
        assignedStation: officer.assignedStation,
        phone: officer.phone,
        status: officer.status
      });
    } else {
      setEditingOfficer(null);
      setFormData({
        fullName: '',
        badgeNumber: '',
        rank: 'Constable',
        branch: 'General Duties',
        assignedStation: 'Colombo Central',
        phone: '',
        status: 'Active'
      });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const url = editingOfficer ? `/api/officers/${editingOfficer.id}` : '/api/officers';
    const method = editingOfficer ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Operation failed');
      }

      toast.success(`Officer ${editingOfficer ? 'updated' : 'created'} successfully`);
      setIsModalOpen(false);
      fetchOfficers();
    } catch (error: any) {
      toast.error(`Error: ${error.message}`);
    }
  };

  const handleDeleteOfficer = async (id: string) => {
    if (!confirm('Are you sure you want to delete this officer record?')) return;

    try {
      const response = await fetch(`/api/officers/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Delete failed');
      
      toast.success('Officer record deleted');
      fetchOfficers();
    } catch (error: any) {
      toast.error(`Error: ${error.message}`);
    }
  };

  // Apply filters locally
  useEffect(() => {
    let result = complaints;

    if (searchQuery) {
      const lowerQuery = searchQuery.toLowerCase();
      result = result.filter(c => 
        c.id.toLowerCase().includes(lowerQuery) || 
        (c.referenceNumber && c.referenceNumber.toLowerCase().includes(lowerQuery)) ||
        c.location.toLowerCase().includes(lowerQuery) ||
        c.category.toLowerCase().includes(lowerQuery)
      );
    }

    if (statusFilter !== 'All Statuses') {
      result = result.filter(c => c.status === statusFilter);
    }

    if (priorityFilter !== 'All Risk Levels') {
      result = result.filter(c => c.priority === priorityFilter);
    }

    setFilteredComplaints(result);
  }, [searchQuery, statusFilter, priorityFilter, complaints]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-police-900 tracking-tight">System Management</h2>
          <p className="text-slate-500 text-sm">Monitor complaints and manage police personnel.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="bg-white"><Download size={16} className="mr-2"/> Export CSV</Button>
          <Button onClick={() => navigate('/intake')}>+ New Case (OCR)</Button>
        </div>
      </div>

      <div className="flex gap-1 bg-slate-100 p-1 rounded-lg w-fit">
        <button 
          onClick={() => setView('complaints')}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${view === 'complaints' ? 'bg-white text-police-blue shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Complaints Directory
        </button>
        <button 
          onClick={() => setView('officers')}
          className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${view === 'officers' ? 'bg-white text-police-blue shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
        >
          Officers Directory
        </button>
      </div>

      <Card>
        {view === 'complaints' ? (
          <>
            <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row gap-4 justify-between bg-slate-50/50">
              <div className="relative w-full sm:w-80">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search size={16} className="text-slate-400" />
                </div>
                <input 
                  type="text" 
                  placeholder="Search by ID, area, or category..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-police-blue focus:border-transparent w-full bg-white shadow-sm"
                />
              </div>
              
              <div className="flex gap-3 flex-wrap">
                <select 
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="border-slate-300 rounded-lg text-sm pl-3 pr-8 py-2 focus:ring-police-blue border bg-white shadow-sm font-medium text-slate-700"
                >
                  <option>All Statuses</option>
                  <option>Pending</option>
                  <option>In Progress</option>
                  <option>Resolved</option>
                </select>
                <select 
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="border-slate-300 rounded-lg text-sm pl-3 pr-8 py-2 focus:ring-police-blue border bg-white shadow-sm font-medium text-slate-700"
                >
                  <option>All Risk Levels</option>
                  <option>Critical</option>
                  <option>High</option>
                  <option>Medium</option>
                  <option>Low</option>
                </select>
              </div>
            </div>
            
            {isLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 size={32} className="animate-spin text-police-blue" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-500 uppercase bg-white border-y border-slate-200">
                    <tr>
                      <th className="px-6 py-4 font-semibold text-police-900">Ref / Case ID</th>
                      <th className="px-6 py-4 font-semibold">Date & Time</th>
                      <th className="px-6 py-4 font-semibold">Category</th>
                      <th className="px-6 py-4 font-semibold">Location Area</th>
                      <th className="px-6 py-4 font-semibold">Risk / Priority</th>
                      <th className="px-6 py-4 font-semibold">Status</th>
                      <th className="px-6 py-4 font-semibold">Assigned Officer</th>
                      <th className="px-6 py-4 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredComplaints.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="px-6 py-8 text-center text-slate-500">
                          No complaints found matching your filters.
                        </td>
                      </tr>
                    ) : (
                      filteredComplaints.map((complaint) => (
                        <tr key={complaint.id} className="bg-white hover:bg-slate-50/70 transition-colors group cursor-pointer" onClick={() => navigate(`/complaint/${complaint.id}`)}>
                          <td className="px-6 py-4 font-semibold text-police-blue">
                            <div className="flex flex-col">
                              <span>{complaint.referenceNumber || 'N/A'}</span>
                              <span className="text-[10px] font-normal text-slate-400">ID: {complaint.id.substring(0, 8).toUpperCase()}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                            {new Date(complaint.dateOfIncident).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                          </td>
                          <td className="px-6 py-4 font-medium text-slate-700">{complaint.category}</td>
                          <td className="px-6 py-4 text-slate-600">{complaint.location}</td>
                          <td className="px-6 py-4">
                            <Badge variant={complaint.priority === 'Critical' ? 'destructive' : complaint.priority === 'High' ? 'warning' : 'default'}>
                              {complaint.priority}
                            </Badge>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center gap-1.5 font-medium ${
                                complaint.status === 'Pending' ? 'text-orange-600' : 
                                complaint.status === 'Resolved' ? 'text-green-600' : 'text-blue-600'
                              }`}>
                                <div className={`h-1.5 w-1.5 rounded-full ${
                                  complaint.status === 'Pending' ? 'bg-orange-500' : 
                                  complaint.status === 'Resolved' ? 'bg-green-500' : 'bg-blue-500'
                                }`}></div>
                                {complaint.status}
                              </span>
                          </td>
                          <td className="px-6 py-4 text-slate-600">
                            {complaint.assignments?.find((a: any) => a.role === 'Lead Officer')?.officer?.fullName || 'Unassigned'}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex justify-end gap-2 text-slate-400 group-hover:text-police-blue transition-colors">
                              <button className="p-1 hover:bg-blue-50 rounded" title="View Details" onClick={(e) => { e.stopPropagation(); navigate(`/complaint/${complaint.id}`); }}>
                                <Eye size={18} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <h3 className="text-sm font-semibold text-slate-700">Police Personnel Directory</h3>
              <Button size="sm" onClick={() => handleOpenModal()}>
                <Plus size={16} className="mr-2"/> Add Officer
              </Button>
            </div>
            {isOfficersLoading ? (
              <div className="flex h-64 items-center justify-center">
                <Loader2 size={32} className="animate-spin text-police-blue" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-500 uppercase bg-white border-y border-slate-200">
                    <tr>
                      <th className="px-6 py-4 font-semibold text-police-900">Officer Name</th>
                      <th className="px-6 py-4 font-semibold">Badge ID</th>
                      <th className="px-6 py-4 font-semibold">Rank</th>
                      <th className="px-6 py-4 font-semibold">Branch</th>
                      <th className="px-6 py-4 font-semibold">Station</th>
                      <th className="px-6 py-4 font-semibold">Cases</th>
                      <th className="px-6 py-4 font-semibold">Status</th>
                      <th className="px-6 py-4 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {officers.map((officer) => (
                      <tr key={officer.id} className="bg-white hover:bg-slate-50/70 transition-colors">
                        <td className="px-6 py-4 font-semibold text-slate-800">{officer.fullName}</td>
                        <td className="px-6 py-4 text-police-blue font-medium">{officer.badgeNumber}</td>
                        <td className="px-6 py-4 text-slate-600">{officer.rank}</td>
                        <td className="px-6 py-4 text-slate-600">{officer.branch}</td>
                        <td className="px-6 py-4 text-slate-600">{officer.assignedStation}</td>
                        <td className="px-6 py-4 font-bold text-police-900">{officer._count.assignments}</td>
                        <td className="px-6 py-4">
                          <Badge variant={officer.status === 'Active' ? 'primary' : 'default'}>
                            {officer.status}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex justify-end gap-2 text-slate-400">
                            <button className="p-1 hover:text-blue-600 transition-colors" onClick={() => handleOpenModal(officer)}>
                              <Edit size={16} />
                            </button>
                            <button className="p-1 hover:text-red-600 transition-colors" onClick={() => handleDeleteOfficer(officer.id)}>
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </Card>

      {/* Officer CRUD Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <Card className="w-full max-w-md shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-police-900">{editingOfficer ? 'Edit Officer' : 'Add New Officer'}</h3>
                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors">
                  <X size={20} />
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Full Name</label>
                  <input 
                    type="text" 
                    required
                    value={formData.fullName}
                    onChange={(e) => setFormData({...formData, fullName: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-police-blue focus:border-transparent outline-none"
                    placeholder="e.g. Kasun Perera"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Badge Number</label>
                    <input 
                      type="text" 
                      required
                      value={formData.badgeNumber}
                      onChange={(e) => setFormData({...formData, badgeNumber: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-police-blue focus:border-transparent outline-none"
                      placeholder="SLP-XXXXX"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Rank</label>
                    <select 
                      value={formData.rank}
                      onChange={(e) => setFormData({...formData, rank: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-police-blue outline-none"
                    >
                      <option>Constable</option>
                      <option>Sergeant</option>
                      <option>Sub-Inspector</option>
                      <option>Inspector</option>
                      <option>Chief Inspector</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Branch</label>
                    <select 
                      value={formData.branch}
                      onChange={(e) => setFormData({...formData, branch: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-police-blue outline-none"
                    >
                      <option>General Duties</option>
                      <option>Crime</option>
                      <option>Traffic</option>
                      <option>Narcotics</option>
                      <option>Intelligence</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Phone</label>
                    <input 
                      type="text" 
                      required
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-police-blue outline-none"
                      placeholder="07XXXXXXXX"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Status</label>
                  <select 
                    value={formData.status}
                    onChange={(e) => setFormData({...formData, status: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-police-blue outline-none"
                  >
                    <option value="Active">Active</option>
                    <option value="On Leave">On Leave</option>
                    <option value="Suspended">Suspended</option>
                  </select>
                </div>

                <div className="pt-4 flex gap-3">
                  <Button type="button" variant="outline" className="flex-1" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                  <Button type="submit" variant="primary" className="flex-1 bg-police-blue">
                    {editingOfficer ? 'Update Officer' : 'Save Officer'}
                  </Button>
                </div>
              </form>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
