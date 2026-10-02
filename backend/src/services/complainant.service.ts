import { ComplainantRepository } from '../repositories/complainant.repository';
import { complainantSchema } from '../lib/validations';
import { Prisma } from '@prisma/client';

export class ComplainantService {
  private repository: ComplainantRepository;

  constructor() {
    this.repository = new ComplainantRepository();
  }

  async getAll() {
    return this.repository.findAll();
  }

  async getById(id: string) {
    const complainant = await this.repository.findById(id);
    if (!complainant) throw new Error("Complainant not found");
    return complainant;
  }

  async create(data: any) {
    const validated = complainantSchema.parse(data);
    
    // Check for duplicate NIC
    const existing = await this.repository.findByNic(validated.nicNumber);
    if (existing) {
      throw new Error(`Complainant with NIC ${validated.nicNumber} already exists`);
    }

    return this.repository.create(validated);
  }

  async update(id: string, data: any) {
    // Partial validation for updates could be used, but keeping it simple
    return this.repository.update(id, data);
  }

  async delete(id: string) {
    return this.repository.delete(id);
  }
}
