import { prisma } from '@/lib/prisma';
import { Prisma, Officer } from '@prisma/client';

export class OfficerRepository {
  async findAll(): Promise<any[]> {
    return prisma.officer.findMany({
      include: {
        _count: {
          select: { assignments: true }
        }
      },
      orderBy: { createdAt: 'desc' }
    });
  }

  async findById(id: string): Promise<Officer | null> {
    return prisma.officer.findUnique({ where: { id } });
  }

  async findByBadge(badgeNumber: string): Promise<Officer | null> {
    return prisma.officer.findUnique({ where: { badgeNumber } });
  }

  async create(data: Prisma.OfficerCreateInput): Promise<Officer> {
    return prisma.officer.create({ data });
  }

  async update(id: string, data: Prisma.OfficerUpdateInput): Promise<Officer> {
    return prisma.officer.update({ where: { id }, data });
  }

  async delete(id: string): Promise<Officer> {
    return prisma.officer.delete({ where: { id } });
  }
}
