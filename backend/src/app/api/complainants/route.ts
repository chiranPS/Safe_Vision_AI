import { NextRequest } from 'next/server';
import { ComplainantController } from '@/controllers/complainant.controller';

const controller = new ComplainantController();

export async function GET(req: NextRequest) {
  return controller.getAll(req);
}

export async function POST(req: NextRequest) {
  return controller.create(req);
}
