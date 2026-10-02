import { OfficerRepository } from '../repositories/officer.repository';
import { officerSchema } from '../lib/validations';

export class OfficerService {
  private repository: OfficerRepository;

  constructor() {
    this.repository = new OfficerRepository();
  }

  async getAll() {
    return this.repository.findAll();
  }

  async getById(id: string) {
    const officer = await this.repository.findById(id);
    if (!officer) throw new Error("Officer not found");
    return officer;
  }

  async create(data: any) {
    const validated = officerSchema.parse(data);
    
    // Check for duplicate badge
    const existing = await this.repository.findByBadge(validated.badgeNumber);
    if (existing) {
      throw new Error(`Officer with badge ${validated.badgeNumber} already exists`);
    }

    return this.repository.create(validated);
  }

  async update(id: string, data: any) {
    return this.repository.update(id, data);
  }

  async delete(id: string) {
    return this.repository.delete(id);
  }
}
