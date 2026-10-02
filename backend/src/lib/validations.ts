import { z } from 'zod';

export const complainantSchema = z.object({
  fullName: z.string().min(2, "Name must be at least 2 characters"),
  nicNumber: z.string().min(10, "Invalid NIC"),
  phone: z.string().min(10, "Invalid phone number"),
  address: z.string().min(5, "Address must be at least 5 characters"),
  dateOfBirth: z.string().optional().nullable(),
  gender: z.string().optional().nullable(),
  occupation: z.string().optional().nullable(),
  employerAddress: z.string().optional().nullable(),
  email: z.string().email().optional().nullable().or(z.literal(''))
});

export const officerSchema = z.object({
  fullName: z.string().min(2),
  badgeNumber: z.string().min(3),
  rank: z.string(),
  branch: z.string(),
  assignedStation: z.string(),
  phone: z.string(),
  status: z.enum(['Active', 'On Leave', 'Suspended']).default('Active')
});

export const complaintSchema = z.object({
  referenceNumber: z.string().optional().nullable(),
  title: z.string().min(5),
  description: z.string().min(10),
  category: z.string(),
  priority: z.enum(['Low', 'Medium', 'High', 'Critical']),
  status: z.enum(['Pending', 'In Progress', 'Resolved']).default('Pending'),
  location: z.string(),
  latitude: z.number(),
  longitude: z.number(),
  dateOfIncident: z.string().datetime().or(z.string().transform(s => new Date(s).toISOString())),
  timeOfIncident: z.string().optional().nullable(),
  personsInvolved: z.string().optional().nullable(),
  suspectedIndividuals: z.string().optional().nullable(),
  vehicleDetails: z.string().optional().nullable(),
  
  // Evidence
  hasPhotos: z.boolean().default(false),
  hasMedicalReport: z.boolean().default(false),
  hasCctv: z.boolean().default(false),
  hasWitnessStatement: z.boolean().default(false),
  hasAudioRecording: z.boolean().default(false),
  hasOtherEvidence: z.boolean().default(false),
  evidenceNotes: z.string().optional().nullable(),

  // Officer Use
  receivingOfficerName: z.string().optional().nullable(),
  receivingOfficerBadge: z.string().optional().nullable(),
  receivingOfficerRank: z.string().optional().nullable(),
  receivingOfficerBranch: z.string().optional().nullable(),
  assignedStation: z.string().optional().nullable(),
  officerSignature: z.string().optional().nullable(),
  dateReceived: z.string().datetime().optional().nullable().or(z.string().transform(s => s ? new Date(s).toISOString() : null)),
  manualNotes: z.string().optional().nullable(),

  riskScore: z.number().default(0),
  keywords: z.array(z.string()).default([]),
  isHotspot: z.boolean().default(false),
  complainantId: z.string().uuid().optional(),
  // For creating a new complainant alongside the complaint
  complainant: complainantSchema.optional()
}).refine(data => data.complainantId || data.complainant, {
  message: "Either complainantId or complainant details must be provided"
});

export const assignmentSchema = z.object({
  complaintId: z.string().uuid(),
  officerId: z.string().uuid(),
  role: z.enum(['Lead Officer', 'Supporting Officer']),
  status: z.enum(['Assigned', 'In Progress', 'Completed']).default('Assigned')
});
