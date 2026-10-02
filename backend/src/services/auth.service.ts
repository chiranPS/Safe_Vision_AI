import { UserRepository } from '@/repositories/user.repository';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'super-secret-key-for-dev-only-please-change-in-prod';

export class AuthService {
  private userRepository: UserRepository;

  constructor() {
    this.userRepository = new UserRepository();
  }

  async login(email: string, passwordHash: string) {
    const user = await this.userRepository.findByEmail(email);

    if (!user) {
      throw new Error('Invalid email or password');
    }

    const isPasswordValid = await bcrypt.compare(passwordHash, user.passwordHash);

    if (!isPasswordValid) {
      throw new Error('Invalid email or password');
    }

    const token = jwt.sign(
      { 
        userId: user.id, 
        email: user.email, 
        rank: user.rank,
        branch: user.branch 
      },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    // Don't return password hash
    const { passwordHash: _, ...userWithoutPassword } = user;

    return {
      user: userWithoutPassword,
      token,
    };
  }
}
