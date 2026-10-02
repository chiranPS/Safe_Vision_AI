import { NextRequest, NextResponse } from 'next/server';
import { UserService } from '@/services/user.service';

export class UserController {
  private userService: UserService;

  constructor() {
    this.userService = new UserService();
  }

  async getAllUsers(req: NextRequest) {
    try {
      const users = await this.userService.getAllUsers();
      // Remove passwordHash from response
      const safeUsers = users.map(({ passwordHash, ...user }) => user);
      return NextResponse.json(safeUsers, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async getUserById(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    try {
      const { id } = await params;
      const user = await this.userService.getUserById(id);
      if (!user) {
        return NextResponse.json({ error: 'User not found' }, { status: 404 });
      }
      const { passwordHash, ...safeUser } = user;
      return NextResponse.json(safeUser, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
  }

  async createUser(req: NextRequest) {
    try {
      const body = await req.json();
      const user = await this.userService.createUser(body);
      const { passwordHash, ...safeUser } = user;
      return NextResponse.json(safeUser, { status: 201 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async updateUser(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    try {
      const { id } = await params;
      const body = await req.json();
      const user = await this.userService.updateUser(id, body);
      const { passwordHash, ...safeUser } = user;
      return NextResponse.json(safeUser, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }

  async deleteUser(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    try {
      const { id } = await params;
      await this.userService.deleteUser(id);
      return NextResponse.json({ message: 'User deleted successfully' }, { status: 200 });
    } catch (error: any) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
  }
}
