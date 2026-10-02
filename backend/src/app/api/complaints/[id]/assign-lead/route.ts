import { NextRequest } from 'next/server';
import { ComplaintController } from '@/controllers/complaint.controller';

const controller = new ComplaintController();

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return controller.assignLeadOfficer(req, id);
}
