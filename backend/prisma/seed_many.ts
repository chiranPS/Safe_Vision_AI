import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Helpers
const randomItem = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];
const randomInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;
const randomFloat = (min: number, max: number) => Math.random() * (max - min) + min;

// Data pools
const firstNames = ['Amila', 'Kasun', 'Ruwan', 'Nimal', 'Chamara', 'Saman', 'Nuwan', 'Chathura', 'Roshan', 'Gayan', 'Tharindu', 'Lahiru', 'Dinesh', 'Asanka', 'Suranga', 'Nayani', 'Kamani', 'Dilani', 'Oshadi', 'Thilini', 'Aruna', 'Bandula', 'Chandana', 'Deepal', 'Eranga', 'Fatima', 'Geeth', 'Harsha', 'Ishara', 'Janaka'];
const lastNames = ['Perera', 'Silva', 'Fernando', 'De Silva', 'Bandara', 'Kumara', 'Rajapaksha', 'Jayawardena', 'Senanayake', 'Wickramasinghe', 'Peiris', 'Ratnayake', 'Dias', 'Dissanayake', 'Gunasekara', 'Herath', 'Iriyagolla', 'Jayasinghe', 'Kulatunga', 'Liyanage'];
const locations = ['Grandpass', 'Pettah', 'Bambalapitiya', 'Wellawatte', 'Dehiwala', 'Mount Lavinia', 'Nugegoda', 'Maharagama', 'Kotte', 'Battaramulla', 'Malabe', 'Colombo 07', 'Maradana', 'Borella', 'Kollupitiya', 'Piliyandala', 'Ratmalana', 'Kohuwala', 'Dehiwala', 'Attidiya'];
const baseCoordinates = {
  'Grandpass': { lat: 6.9452, lng: 79.8705 },
  'Pettah': { lat: 6.9360, lng: 79.8499 },
  'Bambalapitiya': { lat: 6.8922, lng: 79.8550 },
  'Wellawatte': { lat: 6.8741, lng: 79.8598 },
  'Dehiwala': { lat: 6.8407, lng: 79.8712 },
  'Mount Lavinia': { lat: 6.8306, lng: 79.8665 },
  'Nugegoda': { lat: 6.8708, lng: 79.8906 },
  'Maharagama': { lat: 6.8511, lng: 79.9212 },
  'Kotte': { lat: 6.8941, lng: 79.9025 },
  'Battaramulla': { lat: 6.9000, lng: 79.9167 },
  'Malabe': { lat: 6.9044, lng: 79.9620 },
  'Colombo 07': { lat: 6.9066, lng: 79.8687 },
  'Maradana': { lat: 6.9281, lng: 79.8656 },
  'Borella': { lat: 6.9150, lng: 79.8770 },
  'Kollupitiya': { lat: 6.9135, lng: 79.8500 },
  'Piliyandala': { lat: 6.8017, lng: 79.9224 },
  'Ratmalana': { lat: 6.8188, lng: 79.8856 },
  'Kohuwala': { lat: 6.8700, lng: 79.8700 },
  'Attidiya': { lat: 6.8300, lng: 79.8900 },
};

const complaintTypes = [
  { cat: 'Theft', p: 'Medium', kw: ['stolen', 'broken', 'window', 'wallet', 'suspect'] },
  { cat: 'Assault', p: 'High', kw: ['fight', 'injuries', 'alcohol', 'argument', 'weapon'] },
  { cat: 'Narcotics', p: 'High', kw: ['drugs', 'suspicious', 'packages', 'deal', 'night'] },
  { cat: 'Traffic', p: 'Low', kw: ['accident', 'speeding', 'damage', 'vehicle', 'intersection'] },
  { cat: 'Domestic Violence', p: 'Critical', kw: ['screaming', 'spouse', 'children', 'danger', 'crying'] },
  { cat: 'Suspicious Activity', p: 'Low', kw: ['lurking', 'unknown', 'shadows', 'alley', 'photographing'] },
  { cat: 'Robbery', p: 'Critical', kw: ['weapon', 'threat', 'money', 'mask', 'fled'] },
  { cat: 'Fraud', p: 'Medium', kw: ['scam', 'money', 'bank', 'transfer', 'fake'] },
  { cat: 'Cyber Crime', p: 'Medium', kw: ['hacking', 'phishing', 'social media', 'identity theft'] },
  { cat: 'Child Abuse', p: 'Critical', kw: ['neglect', 'harm', 'school', 'protection'] },
];

async function main() {
  console.log('Seeding 200 complaints...');

  // 1. Fetch or Generate Officers (ensure we have enough)
  let officers = await prisma.officer.findMany();
  if (officers.length < 20) {
    console.log('Generating additional officers...');
    const ranks = ['Constable', 'Sergeant', 'Sub-Inspector', 'Inspector'];
    const branches = ['Crime', 'Traffic', 'Narcotics', 'General Duties', 'Cyber Crime'];
    const newOfficers = [];
    for (let i = 0; i < 20; i++) {
        newOfficers.push({
            fullName: `${randomItem(firstNames)} ${randomItem(lastNames)}`,
            badgeNumber: `SLP-${randomInt(60000, 99999)}`,
            rank: randomItem(ranks),
            branch: randomItem(branches),
            assignedStation: randomItem(['Colombo Central', 'Colombo South', 'Nugegoda HQ', 'Mount Lavinia']),
            phone: `071${randomInt(1000000, 9999999)}`,
            status: 'Active',
        });
    }
    await prisma.officer.createMany({ data: newOfficers, skipDuplicates: true });
    officers = await prisma.officer.findMany();
  }

  // 2. Fetch or Generate Complainants
  let complainants = await prisma.complainant.findMany();
  if (complainants.length < 50) {
    console.log('Generating additional complainants...');
    const newComplainants = [];
    for (let i = 0; i < 50; i++) {
        newComplainants.push({
            fullName: `${randomItem(firstNames)} ${randomItem(lastNames)}`,
            nicNumber: `${randomInt(1970, 2005)}${randomInt(10000000, 99999999)}`,
            phone: `07${randomInt(0, 8)}${randomInt(1000000, 9999999)}`,
            address: `No ${randomInt(1, 300)}, ${randomItem(locations)}`,
            gender: randomItem(['Male', 'Female']),
            occupation: randomItem(['Teacher', 'Engineer', 'Driver', 'Shop Owner', 'Student', 'Unemployed']),
        });
    }
    await prisma.complainant.createMany({ data: newComplainants, skipDuplicates: true });
    complainants = await prisma.complainant.findMany();
  }

  // 3. Generate 200 Complaints
  console.log('Generating 200 complaints....');
  const now = new Date();
  
  for (let i = 0; i < 200; i++) {
    const type = randomItem(complaintTypes);
    const locName = randomItem(locations);
    const baseCoord = baseCoordinates[locName as keyof typeof baseCoordinates] || { lat: 6.9271, lng: 79.8612 };
    
    const lat = baseCoord.lat + randomFloat(-0.015, 0.015);
    const lng = baseCoord.lng + randomFloat(-0.015, 0.015);

    const daysAgo = randomInt(0, 60);
    const hoursAgo = randomInt(0, 23);
    const dateOfIncident = new Date(now.getTime() - (daysAgo * 24 * 60 * 60 * 1000) - (hoursAgo * 60 * 60 * 1000));

    let riskScore = randomFloat(0.1, 0.5);
    if (type.p === 'High') riskScore += 0.25;
    if (type.p === 'Critical') riskScore += 0.45;
    riskScore = Math.min(Math.max(riskScore, 0), 1);

    const isHotspot = riskScore > 0.6;
    const status = daysAgo > 30 ? randomItem(['Resolved', 'In Progress']) : randomItem(['Pending', 'In Progress']);

    const complainant = randomItem(complainants);
    const officer = randomItem(officers);

    const complaint = await prisma.complaint.create({
        data: {
            referenceNumber: `SLP-2026-${randomInt(100000, 999999)}`,
            title: `${type.cat} incident at ${locName}`,
            description: `Auto-generated: A ${type.cat.toLowerCase()} was reported at ${locName}. The incident occurred around ${hoursAgo}:00. Witnesses mentioned ${randomItem(type.kw)}.`,
            category: type.cat,
            priority: type.p,
            status: status,
            location: locName,
            latitude: lat,
            longitude: lng,
            dateOfIncident: dateOfIncident,
            timeOfIncident: `${randomInt(1, 12)}:${randomInt(10, 59)} ${randomItem(['AM', 'PM'])}`,
            riskScore: riskScore,
            keywords: [type.cat, ...type.kw.slice(0, 2)],
            isHotspot: isHotspot,
            complainant: { connect: { id: complainant.id } },
            hasPhotos: randomFloat(0,1) > 0.7,
            hasCctv: randomFloat(0,1) > 0.6,
            receivingOfficerName: officer.fullName,
            receivingOfficerBadge: officer.badgeNumber,
            receivingOfficerRank: officer.rank,
            dateReceived: new Date(dateOfIncident.getTime() + 3600000), // 1 hour later
        }
    });

    // Assign an officer
    if (status !== 'Pending') {
        await prisma.complaintAssignment.create({
            data: {
                complaintId: complaint.id,
                officerId: officer.id,
                role: 'Lead Officer',
                status: status === 'Resolved' ? 'Completed' : 'In Progress',
            }
        });
    }
  }

  console.log('Seeding complete! 200 complaints added.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
