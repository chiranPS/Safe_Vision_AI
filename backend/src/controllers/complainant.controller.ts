import { ComplainantService } from '../services/complainant.service';
import { NextRequest, NextResponse } from 'next/server';

export class ComplainantController {
  private service: ComplainantService;

  constructor() {
    this.service = new ComplainantService();
  }

  async getAll(req: NextRequest) {
    try {
      const complainants = await this.service.getAll();
      return NextResponse.json(complainants, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async getById(req: NextRequest, id: string) {
    try {
      const complainant = await this.service.getById(id);
      return NextResponse.json(complainant, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 404 });
    }
  }

  async create(req: NextRequest) {
    try {
      const body = await req.json();
      const complainant = await this.service.create(body);
      return NextResponse.json(complainant, { status: 201 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async update(req: NextRequest, id: string) {
    try {
      const body = await req.json();
      const complainant = await this.service.update(id, body);
      return NextResponse.json(complainant, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async delete(req: NextRequest, id: string) {
    try {
      await this.service.delete(id);
      return NextResponse.json({ message: "Complainant deleted" }, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }
}
