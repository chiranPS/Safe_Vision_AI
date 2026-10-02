import { NextRequest } from 'next/server';
import { OfficerController } from '@/controllers/officer.controller';

const controller = new OfficerController();

export async function GET(req: NextRequest) {
  return controller.getAll(req);
}

export async function POST(req: NextRequest) {
  return controller.create(req);
}
