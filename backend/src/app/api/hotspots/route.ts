import { NextRequest } from 'next/server';
import { ComplaintController } from '@/controllers/complaint.controller';

const complaintController = new ComplaintController();

export async function GET(req: NextRequest) {
  return complaintController.getHotspots(req);
}
