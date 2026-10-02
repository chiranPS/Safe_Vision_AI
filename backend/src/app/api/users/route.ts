import { UserController } from '@/controllers/user.controller';
import { NextRequest } from 'next/server';

const userController = new UserController();

export async function GET(request: NextRequest) {
  return userController.getAllUsers(request);
}

export async function POST(request: NextRequest) {
  return userController.createUser(request);
}
