import { ComplaintController } from "@/controllers/complaint.controller";
import { NextRequest } from "next/server";

const controller = new ComplaintController();

export async function GET(req: NextRequest) {
  return controller.getHotspots(req);
}
