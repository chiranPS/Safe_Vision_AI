import { ComplaintController } from '@/controllers/complaint.controller';
import { NextRequest } from 'next/server';

const controller = new ComplaintController();

export async function POST(req: NextRequest) {
  return controller.extractAI(req);
}
