import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const areaData = await req.json();
    
    const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';
    const aiResponse = await fetch(`${aiServiceUrl}/ai/single-insight`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(areaData)
    });
    
    if (!aiResponse.ok) {
      throw new Error(`AI service responded with status: ${aiResponse.status}`);
    }
    
    const data = await aiResponse.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error fetching hotspot insight:', error);
    // Provide a fallback response if the AI service fails
    return NextResponse.json(
      { recommendation: "Deploy additional units to the affected corridor." },
      { status: 200 } // Return 200 so the frontend doesn't crash, just shows fallback
    );
  }
}
