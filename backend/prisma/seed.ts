import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';
import * as path from 'path';
import bcrypt from 'bcrypt';

const prisma = new PrismaClient();

// Helpers
const randomItem = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];
const randomInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;
const randomFloat = (min: number, max: number) => Math.random() * (max - min) + min;

// Data pools for generating related entities
const firstNames = ['Amila', 'Kasun', 'Ruwan', 'Nimal', 'Chamara', 'Saman', 'Nuwan', 'Chathura', 'Roshan', 'Gayan', 'Tharindu', 'Lahiru', 'Dinesh', 'Asanka', 'Suranga', 'Nayani', 'Kamani', 'Dilani', 'Oshadi', 'Thilini'];
const lastNames = ['Perera', 'Silva', 'Fernando', 'De Silva', 'Bandara', 'Kumara', 'Rajapaksha', 'Jayawardena', 'Senanayake', 'Wickramasinghe', 'Peiris', 'Ratnayake', 'Dias', 'Dissanayake', 'Gunasekara'];
const locations = ['Grandpass', 'Pettah', 'Bambalapitiya', 'Wellawatte', 'Dehiwala', 'Mount Lavinia', 'Nugegoda', 'Maharagama', 'Kotte', 'Battaramulla', 'Malabe', 'Colombo 07', 'Maradana', 'Borella', 'Kollupitiya'];

const DISTRICT_COORDINATES: Record<string, { lat: number; lng: number }> = {
  'colombo': { lat: 6.9271, lng: 79.8612 },
  'gampaha': { lat: 7.0873, lng: 80.0144 },
  'kalutara': { lat: 6.5854, lng: 79.9607 },
  'kandy': { lat: 7.2906, lng: 80.6337 },
  'matale': { lat: 7.4675, lng: 80.6234 },
  'nuwara eliya': { lat: 6.9497, lng: 80.7891 },
  'galle': { lat: 6.0535, lng: 80.2210 },
  'matara': { lat: 5.9549, lng: 80.5550 },
  'hambantota': { lat: 6.1246, lng: 81.1244 },
  'jaffna': { lat: 9.6615, lng: 80.0255 },
  'kilinochchi': { lat: 9.3803, lng: 80.3992 },
  'mannar': { lat: 8.9810, lng: 79.9044 },
  'vavuniya': { lat: 8.7542, lng: 80.4982 },
  'mullaitivu': { lat: 9.2862, lng: 80.8144 },
  'batticaloa': { lat: 7.7170, lng: 81.7000 },
  'ampara': { lat: 7.2912, lng: 81.6747 },
  'trincomalee': { lat: 8.5873, lng: 81.2152 },
  'kurunegala': { lat: 7.4863, lng: 80.3647 },
  'puttalam': { lat: 8.0330, lng: 79.8258 },
  'anuradhapura': { lat: 8.3114, lng: 80.4037 },
  'polonnaruwa': { lat: 7.9403, lng: 81.0009 },
  'badulla': { lat: 6.9849, lng: 81.0565 },
  'moneragala': { lat: 6.8727, lng: 81.3507 },
  'ratnapura': { lat: 6.6828, lng: 80.3992 },
  'kegalle': { lat: 7.2513, lng: 80.3464 }
};

function parseCSV(content: string) {
  const lines = content.split('\n');
  const results = [];
  
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    const row: string[] = [];
    let insideQuote = false;
    let current = '';
    
    for (let j = 0; j < line.length; j++) {
      const char = line[j];
      if (char === '"') {
        insideQuote = !insideQuote;
      } else if (char === ',' && !insideQuote) {
        row.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    row.push(current.trim());
    results.push(row);
  }
  return results;
}

async function main() {
  console.log('Generating seed data from CSV with Time-Shift Offset...');

  // 0. Seed Demo Users
  console.log('Seeding demo users...');
  await prisma.user.deleteMany();
  
  const adminPasswordHash = await bcrypt.hash('admin123', 10);
  const officerPasswordHash = await bcrypt.hash('officer123', 10);
  const analystPasswordHash = await bcrypt.hash('analyst123', 10);

  await prisma.user.createMany({
    data: [
      {
        email: 'admin@police.lk',
        passwordHash: adminPasswordHash,
        name: 'Admin User',
        rank: 'Administrator',
        branch: 'IT & Operations',
        phoneNumber: '0112111111',
        assignedStation: 'Police Head Quarters',
      },
      {
        email: 'officer@police.lk',
        passwordHash: officerPasswordHash,
        name: 'Officer Silva',
        rank: 'Sergeant',
        branch: 'Crime Branch',
        phoneNumber: '0112222222',
        assignedStation: 'Colombo Central',
      },
      {
        email: 'analyst@police.lk',
        passwordHash: analystPasswordHash,
        name: 'Analyst Perera',
        rank: 'Chief Analyst',
        branch: 'Intelligence Division',
        phoneNumber: '0112333333',
        assignedStation: 'Nugegoda HQ',
      },
    ],
  });

  // 1. Generate Complainants (50)
  const complainants = [];
  for (let i = 0; i < 50; i++) {
    const fname = randomItem(firstNames);
    const lname = randomItem(lastNames);
    complainants.push({
      fullName: `${fname} ${lname}`,
      nicNumber: `${randomInt(100000000, 999999999)}v`,
      phone: `07${randomInt(0, 8)}${randomInt(1000000, 9999999)}`,
      address: `No ${randomInt(1, 200)}, Main Road, Colombo`,
    });
  }

  // 2. Generate Officers (15)
  const officers = [];
  const ranks = ['Constable', 'Constable', 'Constable', 'Sergeant', 'Sergeant', 'Sub-Inspector', 'Inspector'];
  const branches = ['Crime', 'Traffic', 'Narcotics', 'General Duties'];
  for (let i = 0; i < 15; i++) {
    const fname = randomItem(firstNames);
    const lname = randomItem(lastNames);
    officers.push({
      fullName: `${fname} ${lname}`,
      badgeNumber: `SLP-${randomInt(10000, 99999)}`,
      rank: randomItem(ranks),
      branch: randomItem(branches),
      assignedStation: randomItem(['Colombo Central', 'Colombo South', 'Nugegoda HQ', 'Mount Lavinia']),
      phone: `071${randomInt(1000000, 9999999)}`,
      status: randomFloat(0, 1) > 0.1 ? 'Active' : 'On Leave',
    });
  }

  // Clear old tables
  console.log('Clearing old database tables...');
  await prisma.complaintAssignment.deleteMany();
  await prisma.complaint.deleteMany();
  await prisma.complainant.deleteMany();
  await prisma.officer.deleteMany();

  console.log('Inserting Complainants and Officers...');
  await prisma.complainant.createMany({ data: complainants });
  await prisma.officer.createMany({ data: officers });

  // Fetch inserted IDs
  const insertedComplainants = await prisma.complainant.findMany();
  const insertedOfficers = await prisma.officer.findMany({ where: { status: 'Active' } });

  // Read and parse the CSV
  const csvPath = path.join(__dirname, '../../ai-service/model_training/synthetic_complaints_sl.csv');
  console.log(`Reading CSV file from: ${csvPath}`);
  const csvContent = fs.readFileSync(csvPath, 'utf-8');
  let parsedRows = parseCSV(csvContent);

  console.log(`Successfully parsed ${parsedRows.length} rows from CSV.`);

  // Sort rows chronologically by date/time (newest first)
  parsedRows.sort((a, b) => {
    const dateA = new Date(`${a[1]}T${a[2]}`).getTime();
    const dateB = new Date(`${b[1]}T${b[2]}`).getTime();
    return dateB - dateA;
  });

  // Limit to first 1500 records (which are now the most recent 1500)
  const maxToSeed = Math.min(parsedRows.length, 1500);
  console.log(`Seeding most recent ${maxToSeed} complaints with date offsets...`);

  // Time-Shift Calculation: Shift the dataset end date (2024-12-31) to match today (June 15, 2026)
  const csvMaxDate = new Date('2024-12-31T23:59:59').getTime();
  const today = new Date().getTime();
  const timeOffset = today - csvMaxDate;

  const complaintsData = [];
  
  for (let i = 0; i < maxToSeed; i++) {
    const row = parsedRows[i];
    
    // CSV mapping:
    // 0: Complaint_ID, 1: Date, 2: Time, 3: Day_of_Week, 4: District, 5: Latitude, 6: Longitude, 7: Category, 8: Priority, 9: Description
    const refNum = row[0];
    const dateStr = row[1];
    const timeStr = row[2];
    const district = row[4];
    const normalizedDistrict = district.toLowerCase().trim();
    const baseCoords = DISTRICT_COORDINATES[normalizedDistrict] || { lat: parseFloat(row[5]), lng: parseFloat(row[6]) };
    
    // Add small random offset to spread cases around the district center
    const lat = baseCoords.lat + (DISTRICT_COORDINATES[normalizedDistrict] ? randomFloat(-0.06, 0.06) : 0);
    const lng = baseCoords.lng + (DISTRICT_COORDINATES[normalizedDistrict] ? randomFloat(-0.06, 0.06) : 0);
    const category = row[7];
    const priority = row[8];
    const description = row[9];
    
    // Parse combined incident date and apply offset
    const originalDate = new Date(`${dateStr}T${timeStr}`);
    const dateOfIncident = new Date(originalDate.getTime() + timeOffset);
    
    // Calculate custom risk score
    let riskScore = randomFloat(0.1, 0.4);
    if (priority === 'High') riskScore += 0.35;
    if (category === 'Assault' || category === 'Child Abuse') riskScore += 0.2;
    riskScore = Math.min(Math.max(riskScore, 0), 1);
    const isHotspot = riskScore > 0.65;

    // Distribute status logically based on how long ago the incident happened (in shifted days)
    const daysAgo = Math.floor((new Date().getTime() - dateOfIncident.getTime()) / (24 * 60 * 60 * 1000));
    let status = 'Pending';
    if (daysAgo > 60) {
      status = randomFloat(0, 1) > 0.15 ? 'Resolved' : 'In Progress';
    } else if (daysAgo > 15) {
      status = randomFloat(0, 1) > 0.40 ? 'In Progress' : 'Pending';
    }

    const complainantId = randomItem(insertedComplainants).id;

    // Pick two random keywords from description
    const words = description.split(' ').filter(w => w.length > 4);
    const kw1 = words.length > 0 ? words[randomInt(0, words.length-1)].replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"") : "incident";
    const kw2 = words.length > 1 ? words[randomInt(0, words.length-1)].replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"") : "police";

    complaintsData.push({
      referenceNumber: refNum,
      title: `${category} incident at ${district}`,
      description: description,
      category: category,
      priority: priority,
      status: status,
      location: district,
      latitude: lat,
      longitude: lng,
      dateOfIncident: dateOfIncident,
      createdAt: dateOfIncident,
      riskScore: riskScore,
      keywords: [kw1.toLowerCase(), kw2.toLowerCase()],
      isHotspot: isHotspot,
      complainantId: complainantId,
    });
  }

  console.log('Inserting Complaints...');
  let assignmentCount = 0;
  for (const complaintData of complaintsData) {
    const complaint = await prisma.complaint.create({ data: complaintData });

    // Assign Lead Officers to resolved/in progress complaints
    if (complaint.status !== 'Pending' || randomFloat(0,1) > 0.6) {
      const leadOfficer = randomItem(insertedOfficers);
      await prisma.complaintAssignment.create({
        data: {
          complaintId: complaint.id,
          officerId: leadOfficer.id,
          role: 'Lead Officer',
          status: complaint.status === 'Resolved' ? 'Completed' : 'In Progress',
          assignedAt: new Date(complaint.createdAt.getTime() + 1000 * 60 * 30), // 30 mins later
        }
      });
      assignmentCount++;

      // 25% chance to assign a Supporting Officer
      if (randomFloat(0, 1) > 0.75) {
        let supportingOfficer = randomItem(insertedOfficers);
        while(supportingOfficer.id === leadOfficer.id) {
          supportingOfficer = randomItem(insertedOfficers);
        }
        await prisma.complaintAssignment.create({
          data: {
            complaintId: complaint.id,
            officerId: supportingOfficer.id,
            role: 'Supporting Officer',
            status: complaint.status === 'Resolved' ? 'Completed' : 'In Progress',
            assignedAt: new Date(complaint.createdAt.getTime() + 1000 * 60 * 45),
          }
        });
        assignmentCount++;
      }
    }
  }

  console.log(`Seeding complete!`);
  console.log(`- 50 Complainants`);
  console.log(`- 15 Officers`);
  console.log(`- ${maxToSeed} Complaints seeded from CSV (with date-shifting)`);
  console.log(`- ${assignmentCount} Officer Assignments`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
