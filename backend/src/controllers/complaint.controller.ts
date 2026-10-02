import { ComplaintService } from '../services/complaint.service';
import { NextRequest, NextResponse } from 'next/server';

export class ComplaintController {
  private service: ComplaintService;

  constructor() {
    this.service = new ComplaintService();
  }

  async getComplaints(req: NextRequest) {
    try {
      const { searchParams } = new URL(req.url);
      const filter: any = {};
      
      const category = searchParams.get('category');
      if (category) filter.category = category;
      
      const priority = searchParams.get('priority');
      if (priority) filter.priority = priority;

      const location = searchParams.get('location');
      if (location) filter.location = location;

      const status = searchParams.get('status');
      if (status) filter.status = status;
      
      const officerId = searchParams.get('officerId');
      if (officerId) filter.officerId = officerId;

      const complaints = await this.service.getComplaints(filter);
      return NextResponse.json(complaints, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async getById(req: NextRequest, id: string) {
    try {
      const complaint = await this.service.getById(id);
      return NextResponse.json(complaint, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 404 });
    }
  }

  async getFullDetails(req: NextRequest, id: string) {
    try {
      const complaint = await this.service.getFullDetails(id);
      return NextResponse.json(complaint, { status: 200 });
    } catch (error: any) {
      console.error("getFullDetails error:", error);
      return NextResponse.json({ error: error.message }, { status: 404 });
    }
  }

  async create(req: NextRequest) {
    try {
      const body = await req.json();
      const complaint = await this.service.create(body);
      return NextResponse.json(complaint, { status: 201 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async update(req: NextRequest, id: string) {
    try {
      const body = await req.json();
      const complaint = await this.service.update(id, body);
      return NextResponse.json(complaint, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async delete(req: NextRequest, id: string) {
    try {
      await this.service.delete(id);
      return NextResponse.json({ message: "Complaint deleted" }, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async assignLeadOfficer(req: NextRequest, id: string) {
    try {
      const { officerId } = await req.json();
      if (!officerId) throw new Error("officerId is required");
      const assignment = await this.service.assignLeadOfficer(id, officerId);
      return NextResponse.json(assignment, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async getDashboardStats() {
    try {
      const stats = await this.service.getDashboardStats();
      return NextResponse.json(stats, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async getDashboardTrends() {
    try {
      const trends = await this.service.getTrends();
      return NextResponse.json(trends, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async getHotspots(req: NextRequest) {
    try {
      const { searchParams } = new URL(req.url);
      const filters: any = {
        timeframe: searchParams.get('timeframe') || 'month',
        category: searchParams.get('category'),
        priority: searchParams.get('priority'),
        status: searchParams.get('status')
      };
      
      const hotspots = await this.service.getHotspots(filters);
      return NextResponse.json(hotspots, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async getAlerts() {
    try {
      const alerts = await this.service.generateAlerts();
      return NextResponse.json(alerts, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async processAI(req: NextRequest) {
    try {
      const formData = await req.formData();
      const file = formData.get('file');
      
      if (!file) {
        return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
      }

      const result = await this.service.processAIComplaint(formData);
      return NextResponse.json(result, { status: 200 });
    } catch (error: any) {
      console.error("AI Process error:", error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async extractAI(req: NextRequest) {
    try {
      const formData = await req.formData();
      const file = formData.get('file');
      
      if (!file) {
        return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
      }

      const result = await this.service.extractAIComplaint(formData);
      return NextResponse.json(result, { status: 200 });
    } catch (error: any) {
      console.error("AI Extract error:", error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }
}
