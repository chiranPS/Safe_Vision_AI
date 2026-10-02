import { ComplaintController } from '@/controllers/complaint.controller';

const complaintController = new ComplaintController();

export async function GET() {
  return complaintController.getDashboardStats();
}
