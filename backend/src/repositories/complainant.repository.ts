import { prisma } from '@/lib/prisma';
import { Prisma, Complainant } from '@prisma/client';

export class ComplainantRepository {
  async findAll(): Promise<Complainant[]> {
    return prisma.complainant.findMany({
      orderBy: { createdAt: 'desc' }
    });
  }

  async findById(id: string): Promise<Complainant | null> {
    return prisma.complainant.findUnique({ where: { id } });
  }

  async findByNic(nicNumber: string): Promise<Complainant | null> {
    return prisma.complainant.findUnique({ where: { nicNumber } });
  }

  async create(data: Prisma.ComplainantCreateInput): Promise<Complainant> {
    return prisma.complainant.create({ data });
  }

  async update(id: string, data: Prisma.ComplainantUpdateInput): Promise<Complainant> {
    return prisma.complainant.update({ where: { id }, data });
  }

  async delete(id: string): Promise<Complainant> {
    return prisma.complainant.delete({ where: { id } });
  }
}
