import { NextRequest } from 'next/server';
import { ComplaintController } from '@/controllers/complaint.controller';

const controller = new ComplaintController();

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return controller.getFullDetails(req, id);
}
