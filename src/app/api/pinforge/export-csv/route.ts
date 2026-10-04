import { NextRequest, NextResponse } from "next/server";

interface ScheduleItem {
  board_name: string;
  title: string;
  description: string;
  link: string;
  image_url: string;
  published_at?: string;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const items: ScheduleItem[] = body.items || [];
    const intervalHours: number = body.interval_hours || 4;

    if (!items.length) {
      return NextResponse.json({ error: "No items provided in export payload" }, { status: 400 });
    }

    // Headers strictly required by Pinterest bulk upload in lowercase
    let csvString = "board_name,title,description,link,image_url,published_at\n";

    const now = new Date();

    items.forEach((item, idx) => {
      // Calculate staggered publishing time
      const pubDate = new Date(now.getTime() + (idx + 1) * intervalHours * 3600 * 1000);
      const isoTime = item.published_at || pubDate.toISOString();

      // Escape quotes for RFC CSV standard
      const cleanBoard = `"${(item.board_name || "Smart Finds").replace(/"/g, '""')}"`;
      const cleanTitle = `"${(item.title || "Curated Find").slice(0, 100).replace(/"/g, '""')}"`;
      const cleanDesc = `"${(item.description || "").slice(0, 500).replace(/"/g, '""')}"`;
      const cleanLink = `"${(item.link || "").replace(/"/g, '""')}"`;
      const cleanImage = `"${(item.image_url || "").replace(/"/g, '""')}"`;
      const cleanDate = `"${isoTime}"`;

      csvString += `${cleanBoard},${cleanTitle},${cleanDesc},${cleanLink},${cleanImage},${cleanDate}\n`;
    });

    return new NextResponse(csvString, {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": 'attachment; filename="pinterest_bulk_pins.csv"',
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
