import { NextRequest } from 'next/server';
import { AssignmentController } from '@/controllers/assignment.controller';

const controller = new AssignmentController();

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return controller.getById(req, id);
}

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return controller.update(req, id);
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return controller.delete(req, id);
}
