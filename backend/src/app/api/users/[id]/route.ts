import { UserController } from '@/controllers/user.controller';
import { NextRequest } from 'next/server';

const userController = new UserController();

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  return userController.getUserById(request, { params });
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  return userController.updateUser(request, { params });
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  return userController.deleteUser(request, { params });
}
