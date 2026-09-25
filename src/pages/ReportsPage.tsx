import React from 'react';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { FileBarChart2, Download, Calendar as CalendarIcon, FileSpreadsheet, FileText } from 'lucide-react';

const availableReports = [
  { id: 1, name: 'Daily Station Briefing', type: 'PDF', date: 'Today, 08:00 AM', status: 'Ready' },
  { id: 2, name: 'Weekly Crime Trend Summary', type: 'PDF', date: 'Oct 23, 2023', status: 'Ready' },
  { id: 3, name: 'Monthly NLP Extracted Entity Data', type: 'CSV', date: 'Oct 01, 2023', status: 'Ready' },
  { id: 4, name: 'High Risk Zones Action Plan', type: 'PDF', date: 'Oct 24, 2023', status: 'Generating' },
  { id: 5, name: 'Officer Caseload Distribution', type: 'CSV', date: 'Oct 24, 2023', status: 'Ready' },
];

export default function ReportsPage() {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-police-900 tracking-tight">System Reports</h2>
          <p className="text-slate-500 text-sm">Download auto-generated insights and compliance documentation.</p>
        </div>
        <Button variant="primary">Generate Custom Report</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-700 text-white border-0">
           <CardContent className="p-6">
             <FileBarChart2 size={32} className="opacity-80 mb-4" />
             <h3 className="font-bold text-lg mb-1">Standard Briefings</h3>
             <p className="text-sm opacity-90 mb-4">Auto-generated daily and weekly overviews for shift commanders.</p>
             <Button variant="ghost" className="bg-white/20 text-white hover:bg-white/30 border-0 w-full justify-between">
               Browse Briefings <ArrowRightIcon size={16} />
             </Button>
           </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-slate-700 to-slate-900 text-white border-0">
           <CardContent className="p-6">
             <FileSpreadsheet size={32} className="opacity-80 mb-4 text-emerald-400" />
             <h3 className="font-bold text-lg mb-1">Raw Data Exports</h3>
             <p className="text-sm opacity-90 mb-4">Export CSVs of recognized entities, locations, and timestamps for localized analysis.</p>
             <Button variant="ghost" className="bg-white/20 text-white hover:bg-white/30 border-0 w-full justify-between">
               Data Exporter <ArrowRightIcon size={16} />
             </Button>
           </CardContent>
        </Card>

        <Card className="bg-white border-dashed border-2 flex flex-col items-center justify-center p-6 text-center text-slate-500 hover:bg-slate-50 cursor-pointer transition-colors">
            <CalendarIcon size={32} className="mb-2 text-slate-400" />
            <h3 className="font-bold text-slate-700 mb-1">Schedule Report</h3>
            <p className="text-sm">Set up automated email delivery to stakeholders.</p>
        </Card>
      </div>

      <Card>
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
           <h3 className="font-bold text-police-900">Recent Generated Reports</h3>
        </div>
        <div className="divide-y divide-slate-100">
          {availableReports.map((report) => (
            <div key={report.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors group">
              <div className="flex items-center gap-4">
                <div className={`p-2 rounded-lg ${report.type === 'PDF' ? 'bg-red-50 text-red-500' : 'bg-green-50 text-green-500'}`}>
                   {report.type === 'PDF' ? <FileText size={20} /> : <FileSpreadsheet size={20} />}
                </div>
                <div>
                  <h4 className="font-semibold text-police-900 group-hover:text-police-blue transition-colors">{report.name}</h4>
                  <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
                    <span>{report.date}</span>
                    <span>•</span>
                    <span className="font-medium">{report.type} File</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                 {report.status === 'Ready' 
                   ? <Badge variant="success">Ready Download</Badge>
                   : <Badge variant="warning" className="animate-pulse">Generating...</Badge>
                 }
                 <Button variant="outline" size="sm" className="bg-white" disabled={report.status !== 'Ready'}>
                   <Download size={16} />
                 </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

const ArrowRightIcon: React.FC<{size: number}> = ({size}) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
);
