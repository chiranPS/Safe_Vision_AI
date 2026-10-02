import { NextRequest } from 'next/server';
import { AssignmentController } from '@/controllers/assignment.controller';

const controller = new AssignmentController();

export async function GET(req: NextRequest) {
  return controller.getAll(req);
}

export async function POST(req: NextRequest) {
  return controller.create(req);
}
