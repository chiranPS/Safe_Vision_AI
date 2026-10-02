import { NextRequest } from 'next/server';
import { OfficerController } from '@/controllers/officer.controller';

const controller = new OfficerController();

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
