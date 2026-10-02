import { NextRequest } from 'next/server';
import { ComplaintController } from '@/controllers/complaint.controller';

const controller = new ComplaintController();

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
