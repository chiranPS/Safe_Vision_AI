import { AssignmentService } from '../services/assignment.service';
import { NextRequest, NextResponse } from 'next/server';

export class AssignmentController {
  private service: AssignmentService;

  constructor() {
    this.service = new AssignmentService();
  }

  async getAll(req: NextRequest) {
    try {
      const { searchParams } = new URL(req.url);
      const complaintId = searchParams.get('complaintId') || undefined;
      
      const assignments = await this.service.getAll(complaintId);
      return NextResponse.json(assignments, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async getById(req: NextRequest, id: string) {
    try {
      const assignment = await this.service.getById(id);
      return NextResponse.json(assignment, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 404 });
    }
  }

  async create(req: NextRequest) {
    try {
      const body = await req.json();
      const assignment = await this.service.create(body);
      return NextResponse.json(assignment, { status: 201 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async update(req: NextRequest, id: string) {
    try {
      const body = await req.json();
      const assignment = await this.service.update(id, body);
      return NextResponse.json(assignment, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async delete(req: NextRequest, id: string) {
    try {
      await this.service.delete(id);
      return NextResponse.json({ message: "Assignment deleted" }, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }
}
