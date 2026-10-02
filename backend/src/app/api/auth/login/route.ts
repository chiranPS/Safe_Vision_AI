import { AuthController } from '@/controllers/auth.controller';
import { NextRequest } from 'next/server';

const authController = new AuthController();

export async function POST(request: NextRequest) {
  return authController.login(request);
}
