import { OfficerService } from '../services/officer.service';
import { NextRequest, NextResponse } from 'next/server';

export class OfficerController {
  private service: OfficerService;

  constructor() {
    this.service = new OfficerService();
  }

  async getAll(req: NextRequest) {
    try {
      const officers = await this.service.getAll();
      return NextResponse.json(officers, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async getById(req: NextRequest, id: string) {
    try {
      const officer = await this.service.getById(id);
      return NextResponse.json(officer, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 404 });
    }
  }

  async create(req: NextRequest) {
    try {
      const body = await req.json();
      const officer = await this.service.create(body);
      return NextResponse.json(officer, { status: 201 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async update(req: NextRequest, id: string) {
    try {
      const body = await req.json();
      const officer = await this.service.update(id, body);
      return NextResponse.json(officer, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async delete(req: NextRequest, id: string) {
    try {
      await this.service.delete(id);
      return NextResponse.json({ message: "Officer deleted" }, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }
}
