import { prisma } from '@/lib/prisma';
import { Prisma, ComplaintAssignment } from '@prisma/client';

export class AssignmentRepository {
  async findAll(complaintId?: string): Promise<ComplaintAssignment[]> {
    return prisma.complaintAssignment.findMany({
      where: complaintId ? { complaintId } : undefined,
      include: {
        officer: true
      },
      orderBy: { assignedAt: 'desc' }
    });
  }

  async findById(id: string): Promise<ComplaintAssignment | null> {
    return prisma.complaintAssignment.findUnique({ 
      where: { id },
      include: { officer: true }
    });
  }

  async findLeadOfficer(complaintId: string): Promise<ComplaintAssignment | null> {
    return prisma.complaintAssignment.findFirst({
      where: { complaintId, role: 'Lead Officer' }
    });
  }

  async create(data: Prisma.ComplaintAssignmentCreateInput): Promise<ComplaintAssignment> {
    return prisma.complaintAssignment.create({ data, include: { officer: true } });
  }

  async update(id: string, data: Prisma.ComplaintAssignmentUpdateInput): Promise<ComplaintAssignment> {
    return prisma.complaintAssignment.update({ where: { id }, data, include: { officer: true } });
  }

  async findActiveOfficers() {
    return prisma.officer.findMany({
      where: { status: "Active" }
    });
  }

  async delete(id: string): Promise<ComplaintAssignment> {
    return prisma.complaintAssignment.delete({ where: { id } });
  }
}
