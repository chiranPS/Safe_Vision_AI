import { UserRepository } from '@/repositories/user.repository';
import { Prisma, User } from '@prisma/client';
import bcrypt from 'bcrypt';

export class UserService {
  private userRepository: UserRepository;

  constructor() {
    this.userRepository = new UserRepository();
  }

  async getUserById(id: string): Promise<User | null> {
    return this.userRepository.findById(id);
  }

  async getAllUsers(): Promise<User[]> {
    return this.userRepository.findAll();
  }

  async createUser(data: Prisma.UserCreateInput): Promise<User> {
    const existingUser = await this.userRepository.findByEmail(data.email);
    if (existingUser) {
      throw new Error('User with this email already exists');
    }

    const hashedPassword = await bcrypt.hash(data.passwordHash, 10);
    
    return this.userRepository.create({
      ...data,
      passwordHash: hashedPassword,
    });
  }

  async updateUser(id: string, data: Prisma.UserUpdateInput): Promise<User> {
    // If password is being updated, hash it
    if (data.passwordHash && typeof data.passwordHash === 'string') {
      data.passwordHash = await bcrypt.hash(data.passwordHash, 10);
    }
    return this.userRepository.update(id, data);
  }

  async deleteUser(id: string): Promise<User> {
    return this.userRepository.delete(id);
  }
}
