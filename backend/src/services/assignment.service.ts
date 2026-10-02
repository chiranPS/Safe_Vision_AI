import { AssignmentRepository } from '../repositories/assignment.repository';
import { assignmentSchema } from '../lib/validations';

export class AssignmentService {
  private repository: AssignmentRepository;

  constructor() {
    this.repository = new AssignmentRepository();
  }

  async getAll(complaintId?: string) {
    return this.repository.findAll(complaintId);
  }

  async getById(id: string) {
    const assignment = await this.repository.findById(id);
    if (!assignment) throw new Error("Assignment not found");
    return assignment;
  }

  async create(data: any) {
    const validated = assignmentSchema.parse(data);
    
    // Enforce single lead officer
    if (validated.role === 'Lead Officer') {
      const existingLead = await this.repository.findLeadOfficer(validated.complaintId);
      if (existingLead) {
        throw new Error("Complaint already has a Lead Officer. Demote them first or update their role.");
      }
    }

    return this.repository.create({
      role: validated.role,
      status: validated.status,
      complaint: { connect: { id: validated.complaintId } },
      officer: { connect: { id: validated.officerId } }
    });
  }

  async update(id: string, data: any) {
    // If setting to lead, ensure no other lead exists
    if (data.role === 'Lead Officer') {
      const assignment = await this.getById(id);
      const existingLead = await this.repository.findLeadOfficer(assignment.complaintId);
      if (existingLead && existingLead.id !== id) {
        throw new Error("Complaint already has a Lead Officer.");
      }
    }

    return this.repository.update(id, data);
  }

  async delete(id: string) {
    return this.repository.delete(id);
  }
}
