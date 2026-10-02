import { ComplaintRepository } from '../repositories/complaint.repository';
import { ComplainantRepository } from '../repositories/complainant.repository';
import { AssignmentRepository } from '../repositories/assignment.repository';
import { complaintSchema } from '../lib/validations';
import { Prisma } from '@prisma/client';

const COLOMBO_LOCATIONS: Record<string, { lat: number; lng: number }> = {
  'colombo 07': { lat: 6.9056, lng: 79.8712 },
  'colombo 7': { lat: 6.9056, lng: 79.8712 },
  'colombo 03': { lat: 6.9145, lng: 79.8517 },
  'colombo 3': { lat: 6.9145, lng: 79.8517 },
  'colombo 04': { lat: 6.8967, lng: 79.8569 },
  'colombo 4': { lat: 6.8967, lng: 79.8569 },
  'colombo 11': { lat: 6.9389, lng: 79.8519 },
  'colombo 1': { lat: 6.9344, lng: 79.8428 },
  'colombo 2': { lat: 6.9205, lng: 79.8587 },
  'colombo 5': { lat: 6.8856, lng: 79.8712 },
  'colombo 05': { lat: 6.8856, lng: 79.8712 },
  'galle road': { lat: 6.8962, lng: 79.8565 },
  'bambalapitiya': { lat: 6.8967, lng: 79.8569 },
  'kollupitiya': { lat: 6.9145, lng: 79.8517 },
  'borella': { lat: 6.9142, lng: 79.8778 },
  'cinnamon gardens': { lat: 6.9056, lng: 79.8712 },
  'wellawatte': { lat: 6.8724, lng: 79.8622 },
  'kotte': { lat: 6.9010, lng: 79.9074 },
  'battaramulla': { lat: 6.8989, lng: 79.9223 },
  'nugegoda': { lat: 6.8728, lng: 79.8920 },
  'dehiwala': { lat: 6.8378, lng: 79.8801 },
  'mount lavinia': { lat: 6.8295, lng: 79.8659 },
  'rajagiriya': { lat: 6.9102, lng: 79.8978 },
  'dematagoda': { lat: 6.9329, lng: 79.8789 },
  'pettah': { lat: 6.9389, lng: 79.8519 },
  'fort': { lat: 6.9344, lng: 79.8428 },
  'colombo': { lat: 6.9271, lng: 79.8612 },
};

async function geocodeLocation(location: string): Promise<{ lat: number; lng: number }> {
  if (!location || location === 'Not specified') {
    return { lat: 6.9271, lng: 79.8612 };
  }

  const normalized = location.toLowerCase().trim();
  
  // 1. Try local dictionary lookup
  for (const [key, coords] of Object.entries(COLOMBO_LOCATIONS)) {
    if (normalized.includes(key)) {
      return coords;
    }
  }

  // 2. Try Nominatim Geocoding API with a timeout
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000); // 3 seconds timeout
    
    const query = `${location}, Sri Lanka`;
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`;
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Police-Compliant-Management-System/1.0'
      },
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    
    if (response.ok) {
      const data = (await response.json()) as any[];
      if (data && data.length > 0) {
        const lat = parseFloat(data[0].lat);
        const lng = parseFloat(data[0].lon);
        if (!isNaN(lat) && !isNaN(lng)) {
          return { lat, lng };
        }
      }
    }
  } catch (error) {
    console.error(`Geocoding failed for ${location}:`, error);
  }

  // 3. Fallback default to Colombo center
  return { lat: 6.9271, lng: 79.8612 };
}


interface ComplaintAlert {
  type: string;
  message: string;
  area: string;
  createdAt: string;
}

export class ComplaintService {
  private repository: ComplaintRepository;
  private complainantRepository: ComplainantRepository;
  private assignmentRepository: AssignmentRepository;

  constructor() {
    this.repository = new ComplaintRepository();
    this.complainantRepository = new ComplainantRepository();
    this.assignmentRepository = new AssignmentRepository();
  }

  async getComplaints(filter: any) {
    const where: Prisma.ComplaintWhereInput = {};
    
    if (filter.category) where.category = filter.category;
    if (filter.priority) where.priority = filter.priority;
    if (filter.location) where.location = filter.location;
    if (filter.status) where.status = filter.status;
    if (filter.officerId) {
      where.assignments = {
        some: { officerId: filter.officerId }
      };
    }

    // Increase limit to 2000 to ensure all seeded records are sent to the dashboard analytics
    return this.repository.findAll(where, 0, 2000, {
      assignments: { include: { officer: true } }
    });
  }

  async getById(id: string) {
    const complaint = await this.repository.findById(id);
    if (!complaint) throw new Error("Complaint not found");
    return complaint;
  }

  async getFullDetails(id: string) {
    const details = await this.repository.getFullDetails(id);
    if (!details) throw new Error("Complaint not found");
    return details;
  }

  async create(data: any) {
    const validated = complaintSchema.parse(data);
    
    let complainantId = validated.complainantId;

    // Handle nested complainant creation if id is not provided
    if (!complainantId && validated.complainant) {
      // Check if NIC already exists
      const existingComplainant = await this.complainantRepository.findByNic(validated.complainant.nicNumber);
      if (existingComplainant) {
        complainantId = existingComplainant.id;
      } else {
        const newComplainant = await this.complainantRepository.create(validated.complainant);
        complainantId = newComplainant.id;
      }
    }

    if (!complainantId) {
      throw new Error("Complainant resolution failed");
    }

    const { complainant, complainantId: _cid, ...complaintData } = validated;

    return this.repository.create({
      ...complaintData,
      dateOfIncident: new Date(complaintData.dateOfIncident),
      complainant: { connect: { id: complainantId } }
    });
  }

  async update(id: string, data: any) {
    return this.repository.update(id, data);
  }

  async delete(id: string) {
    return this.repository.delete(id);
  }

  async assignLeadOfficer(complaintId: string, officerId: string) {
    // Check if there is an existing lead
    const existingLead = await this.assignmentRepository.findLeadOfficer(complaintId);
    
    if (existingLead) {
      // Demote existing lead to supporting
      await this.assignmentRepository.update(existingLead.id, { role: 'Supporting Officer' });
    }

    // Assign new lead
    return this.assignmentRepository.create({
      role: 'Lead Officer',
      complaint: { connect: { id: complaintId } },
      officer: { connect: { id: officerId } }
    });
  }

  async getDashboardStats() {
    return this.repository.getDashboardStats();
  }

  async getTrends() {
    const rawData = await this.repository.getTrendsData(30);
    
    // Group by date string (YYYY-MM-DD)
    const trendMap = new Map<string, { date: string; riskScoreTotal: number; count: number }>();
    
    rawData.forEach((record: any) => {
      const dateStr = record.dateOfIncident.toISOString().split('T')[0];
      if (!trendMap.has(dateStr)) {
        trendMap.set(dateStr, { date: dateStr, riskScoreTotal: 0, count: 0 });
      }
      const entry = trendMap.get(dateStr)!;
      entry.riskScoreTotal += record.riskScore;
      entry.count += 1;
    });

    // Format for frontend charts
    return Array.from(trendMap.values()).map(entry => ({
      date: entry.date,
      count: entry.count,
      avgRiskScore: parseFloat((entry.riskScoreTotal / entry.count).toFixed(2))
    })).sort((a, b) => a.date.localeCompare(b.date));
  }

  async getHotspots(filters: any = {}) {
    const { timeframe = 'month', category, priority, status } = filters;
    
    // 1. Define time range
    const now = new Date();
    const currentRangeStart = new Date();
    const prevRangeStart = new Date();
    
    let days = 30;
    if (timeframe === 'week') days = 7;
    if (timeframe === '3months') days = 90;
    
    currentRangeStart.setDate(now.getDate() - days);
    prevRangeStart.setDate(now.getDate() - (days * 2));

    const where: Prisma.ComplaintWhereInput = {};
    if (category) where.category = category;
    if (priority) where.priority = priority;
    if (status) where.status = status;
    
    // Get data for current and previous period for trend calculation
    const allData = await this.repository.getHotspotData({
      ...where,
      dateOfIncident: { gte: prevRangeStart }
    });

    const currentPeriodData = allData.filter(d => d.dateOfIncident >= currentRangeStart);
    const prevPeriodData = allData.filter(d => d.dateOfIncident < currentRangeStart);

    // 2. Cluster logic
    const clusterMap = new Map<string, any>();
    
    currentPeriodData.forEach((spot: any) => {
      const key = spot.location;
      if (!clusterMap.has(key)) {
        clusterMap.set(key, {
          area: key,
          lat: spot.latitude,
          lng: spot.longitude,
          count: 0,
          riskLevel: 'Low',
          categories: {} as Record<string, number>,
          totalRiskScore: 0,
          trend: 0
        });
      }
      
      const cluster = clusterMap.get(key)!;
      cluster.count++;
      cluster.totalRiskScore += spot.riskScore;
      cluster.categories[spot.category] = (cluster.categories[spot.category] || 0) + 1;
      
      if (spot.priority === 'Critical') cluster.riskLevel = 'Critical';
      else if (spot.priority === 'High' && cluster.riskLevel !== 'Critical') cluster.riskLevel = 'High';
      else if (spot.priority === 'Medium' && !['Critical', 'High'].includes(cluster.riskLevel)) cluster.riskLevel = 'Medium';
    });

    // 3. Finalize stats and calculate trends
    return Array.from(clusterMap.values()).map(cluster => {
      // Top 3 categories
      const topCategories = Object.entries(cluster.categories)
        .sort((a, b) => (b[1] as number) - (a[1] as number))
        .slice(0, 3)
        .map(entry => entry[0]);

      // Trend calculation
      const prevCount = prevPeriodData.filter(d => d.location === cluster.area).length;
      if (prevCount > 0) {
        cluster.trend = Math.round(((cluster.count - prevCount) / prevCount) * 100);
      } else {
        cluster.trend = cluster.count > 0 ? 100 : 0;
      }

      return {
        ...cluster,
        topCategories,
        avgRiskScore: parseFloat((cluster.totalRiskScore / cluster.count).toFixed(2))
      };
    });
  }

  async generateAlerts() {
    const alerts: ComplaintAlert[] = [];
    
    try {
      // Fetch hotspot aggregations over the last 30 days to ensure enough data volume
      const hotspots = await this.getHotspots(30);
      
      // POST the data to our new AI Insights Endpoint
      const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';
      const aiResponse = await fetch(`${aiServiceUrl}/ai/dashboard-insights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ areas: hotspots })
      });
      
      if (aiResponse.ok) {
        const aiAlerts = await aiResponse.json();
        alerts.push(...aiAlerts);
      } else {
        console.error("Failed to generate AI insights:", await aiResponse.text());
      }
    } catch (e) {
      console.error("Could not connect to AI service for insights:", e);
    }

    return alerts;
  }

  async processAIComplaint(formData: FormData) {
    let aiData: any;
    
    // Check if user provided manual corrections from the UI
    const manualDataStr = formData.get('manualData') as string;
    
    if (manualDataStr) {
      try {
        aiData = JSON.parse(manualDataStr);
        console.log("Using manual corrections for complaint creation");
      } catch (e) {
        console.error("Failed to parse manualData, falling back to AI extraction");
        aiData = await this.extractAIComplaint(formData);
      }
    } else {
      // 1. Forward the file to FastAPI if no manual data
      aiData = await this.extractAIComplaint(formData);
    }

    // 2. Auto-create or find Complainant
    let complainantId: string;
    const { complainant, complaint: complaintDetails, category, riskScore, urgencyLevel, alerts } = aiData;
    
    const existingComplainant = await this.complainantRepository.findByNic(complainant.nic || "UNKNOWN");
    
    if (existingComplainant) {
      complainantId = existingComplainant.id;
    } else {
      const newComplainant = await this.complainantRepository.create({
        fullName: complainant.name || "Unknown",
        nicNumber: complainant.nic || `AUTO-${Date.now()}`,
        phone: complainant.phone || "0000000000",
        address: complainant.address || "Not specified",
        dateOfBirth: complainant.dob,
        gender: complainant.gender,
        occupation: complainant.occupation,
        employerAddress: complainant.employerAddress,
        email: complainant.email
      });
      complainantId = newComplainant.id;
    }

    // Geocode the location from name to coordinate values
    const coords = await geocodeLocation(complaintDetails.location || "Not specified");

    // 3. Create Complaint
    const newComplaint = await this.repository.create({
      referenceNumber: complaintDetails.referenceNumber,
      title: `${category} Incident at ${complaintDetails.location || 'Unknown Location'}`,
      description: complaintDetails.description,
      category: category,
      priority: urgencyLevel,
      status: "Pending",
      location: complaintDetails.location || "Not specified",
      latitude: coords.lat,
      longitude: coords.lng,
      dateOfIncident: this.parseDate(complaintDetails.date),
      timeOfIncident: complaintDetails.time,
      personsInvolved: complaintDetails.personsInvolved,
      suspectedIndividuals: complaintDetails.suspectedIndividuals,
      vehicleDetails: complaintDetails.vehicleDetails,
      
      // Evidence
      hasPhotos: complaintDetails.hasPhotos || false,
      hasMedicalReport: complaintDetails.hasMedicalReport || false,
      hasCctv: complaintDetails.hasCctv || false,
      hasWitnessStatement: complaintDetails.hasWitnessStatement || false,
      hasAudioRecording: complaintDetails.hasAudioRecording || false,
      hasOtherEvidence: complaintDetails.hasOtherEvidence || false,
      evidenceNotes: complaintDetails.evidenceNotes,

      // Officer Use
      receivingOfficerName: complaintDetails.receivingOfficerName,
      receivingOfficerBadge: complaintDetails.badgeNumber,
      receivingOfficerRank: complaintDetails.rank,
      receivingOfficerBranch: complaintDetails.branch,
      assignedStation: complaintDetails.assignedStation,
      officerSignature: complaintDetails.signaturePresent ? "Digitally Captured" : null,
      dateReceived: this.parseDate(complaintDetails.dateReceived),
      manualNotes: complaintDetails.manualNotes,

      riskScore: riskScore,
      keywords: alerts.map((a: any) => a.alertType),
      isHotspot: riskScore > 0.6,
      complainant: { connect: { id: complainantId } }
    } as any);

    // 4. Auto-assignment (Logic: Assign a random active officer for now)
    const officers = await this.assignmentRepository.findActiveOfficers();
    if (officers.length > 0) {
      const randomOfficer = officers[Math.floor(Math.random() * officers.length)];
      await this.assignmentRepository.create({
        role: "Lead Officer",
        complaint: { connect: { id: newComplaint.id } },
        officer: { connect: { id: randomOfficer.id } }
      });
    }

    return {
      complaint: newComplaint,
      aiMetadata: aiData
    };
  }

  async extractAIComplaint(formData: FormData) {
    const aiServiceUrl = process.env.AI_SERVICE_URL || "http://localhost:8000";
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 300000); // 5 minute timeout

    try {
      const aiResponse = await fetch(`${aiServiceUrl}/ai/process-complaint`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (!aiResponse.ok) {
        const errorText = await aiResponse.text();
        throw new Error(`AI Service Error: ${errorText}`);
      }

      return aiResponse.json();
    } catch (error: any) {
      clearTimeout(timeout);
      if (error.name === 'AbortError') {
        throw new Error("AI Service timed out while processing. This usually happens during the first run while models are downloading. Please try again in a moment.");
      }
      throw error;
    }
  }

  private parseDate(dateStr: string | null | undefined): Date {
    if (!dateStr) return new Date();
    
    // Try standard parsing
    const date = new Date(dateStr);
    if (!isNaN(date.getTime())) return date;
    
    // Try DD/MM/YYYY parsing
    const parts = dateStr.split(/[/\-.]/);
    if (parts.length === 3) {
      const day = parseInt(parts[0]);
      const month = parseInt(parts[1]) - 1; // 0-indexed
      const year = parseInt(parts[2]);
      
      // Handle 2-digit years if necessary
      const fullYear = year < 100 ? (year > 50 ? 1900 + year : 2000 + year) : year;
      
      const parsed = new Date(fullYear, month, day);
      if (!isNaN(parsed.getTime())) return parsed;
    }
    
    return new Date();
  }
}
