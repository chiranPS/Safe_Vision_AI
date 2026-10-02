import { NextRequest, NextResponse } from 'next/server';
import { AuthService } from '@/services/auth.service';
import { UserService } from '@/services/user.service';

export class AuthController {
  private authService: AuthService;
  private userService: UserService;

  constructor() {
    this.authService = new AuthService();
    this.userService = new UserService();
  }

  async login(req: NextRequest) {
    try {
      const { email, password } = await req.json();
      
      if (!email || !password) {
        return NextResponse.json({ error: 'Email and password are required' }, { status: 400 });
      }

      const result = await this.authService.login(email, password);
      return NextResponse.json(result, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 401 });
    }
  }

  async register(req: NextRequest) {
    try {
      const body = await req.json();
      
      if (!body.email || !body.passwordHash) {
        return NextResponse.json({ error: 'Email and passwordHash are required' }, { status: 400 });
      }

      const user = await this.userService.createUser(body);
      const { passwordHash, ...safeUser } = user;
      
      return NextResponse.json(safeUser, { status: 201 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }
}
