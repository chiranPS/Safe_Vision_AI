import { NextRequest } from 'next/server';
import { ComplaintController } from '@/controllers/complaint.controller';

const controller = new ComplaintController();

export async function GET(req: NextRequest) {
  return controller.getComplaints(req);
}

export async function POST(req: NextRequest) {
  return controller.create(req);
}
