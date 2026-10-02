import { prisma } from '@/lib/prisma';
import { Prisma, Complaint } from '@prisma/client';

export class ComplaintRepository {
  async findAll(filter?: Prisma.ComplaintWhereInput, skip?: number, take?: number, include?: Prisma.ComplaintInclude): Promise<Complaint[]> {
    return prisma.complaint.findMany({
      where: filter,
      skip,
      take,
      include,
      orderBy: { dateOfIncident: 'desc' }
    });
  }

  async findById(id: string): Promise<Complaint | null> {
    return prisma.complaint.findUnique({ where: { id } });
  }

  async getFullDetails(id: string) {
    return prisma.complaint.findUnique({
      where: { id },
      include: {
        complainant: true,
        assignments: {
          include: {
            officer: true
          }
        }
      }
    });
  }

  async create(data: Prisma.ComplaintCreateInput): Promise<Complaint> {
    return prisma.complaint.create({ data });
  }

  async update(id: string, data: Prisma.ComplaintUpdateInput): Promise<Complaint> {
    return prisma.complaint.update({ where: { id }, data });
  }

  async delete(id: string): Promise<Complaint> {
    return prisma.complaint.delete({ where: { id } });
  }

  async count(filter?: Prisma.ComplaintWhereInput): Promise<number> {
    return prisma.complaint.count({ where: filter });
  }

  // Get aggregated stats
  async getDashboardStats() {
    const total = await prisma.complaint.count();
    const open = await prisma.complaint.count({ where: { status: { in: ['Pending', 'In Progress'] } } });
    const resolved = await prisma.complaint.count({ where: { status: 'Resolved' } });
    
    // Complaints from today
    const startOfToday = new Date();
    startOfToday.setHours(0, 0, 0, 0);
    const todayCount = await prisma.complaint.count({
      where: { dateOfIncident: { gte: startOfToday } }
    });

    return { total, open, resolved, today: todayCount };
  }

  // Group by date for trends chart
  async getTrendsData(days: number = 30) {
    const dateLimit = new Date();
    dateLimit.setDate(dateLimit.getDate() - days);

    const recentComplaints = await prisma.complaint.findMany({
      where: { dateOfIncident: { gte: dateLimit } },
      select: { dateOfIncident: true, category: true, riskScore: true }
    });

    return recentComplaints;
  }

  async getHotspotData(filter: Prisma.ComplaintWhereInput) {
    return prisma.complaint.findMany({
      where: filter,
      select: { 
        id: true, 
        location: true, 
        latitude: true, 
        longitude: true, 
        category: true, 
        priority: true, 
        riskScore: true,
        dateOfIncident: true
      }
    });
  }
}
