import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { exec } from "child_process";
import { promisify } from "util";

const execPromise = promisify(exec);

const DATA_DIR = path.join(process.cwd(), "python_engine", "data");
const OVERVIEW_FILE = path.join(DATA_DIR, "account_overview.json");
const LEDGER_FILE = path.join(DATA_DIR, "performance_ledger.json");
const BOARD_FILE = path.join(DATA_DIR, "board_analytics.json");
const PYTHON_URL = process.env.PINFORGE_ENGINE_URL || "http://127.0.0.1:8000";

export async function GET(req: NextRequest) {
  try {
    // 1. Try querying Python engine first
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1500);
      const res = await fetch(`${PYTHON_URL}/api/analytics/overview`, {
        signal: controller.signal,
        cache: "no-store",
      });
      clearTimeout(timeoutId);
      if (res.ok) {
        const overview = await res.json();
        const ledgerRes = await fetch(`${PYTHON_URL}/api/analytics/ledger`, { cache: "no-store" });
        const ledger = ledgerRes.ok ? await ledgerRes.json() : null;
        return NextResponse.json({
          source: "live_engine",
          overview,
          boards: ledger?.board_performance_summary || overview.board_stats || {},
          pins: ledger?.all_ranked_pins || [],
        });
      }
    } catch {
      // Fallback to local files
    }

    // 2. Fallback to persisted files in python_engine/data/
    if (fs.existsSync(OVERVIEW_FILE) && fs.existsSync(LEDGER_FILE)) {
      const overviewRaw = fs.readFileSync(OVERVIEW_FILE, "utf-8");
      const ledgerRaw = fs.readFileSync(LEDGER_FILE, "utf-8");
      const overview = JSON.parse(overviewRaw);
      const ledger = JSON.parse(ledgerRaw);

      return NextResponse.json({
        source: "persisted_ledger",
        overview,
        boards: ledger.board_performance_summary || {},
        pins: ledger.all_ranked_pins || [],
      });
    }

    return NextResponse.json(
      { error: "Analytics data not found. Run sync to generate initial ledger." },
      { status: 404 }
    );
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Internal Error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    // 1. Try triggering via Python FastAPI engine
    try {
      const res = await fetch(`${PYTHON_URL}/api/analytics/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json({ success: true, ...data });
      }
    } catch {
      // Fall through to CLI execution
    }

    // 2. Direct CLI fallback via venv python
    const venvPython = path.join(process.cwd(), ".venv", "bin", "python");
    const scriptPath = path.join(process.cwd(), "python_engine", "production_analytics.py");

    const cmd = `${fs.existsSync(venvPython) ? venvPython : "python3"} ${scriptPath} sync`;
    const { stdout, stderr } = await execPromise(cmd, { cwd: process.cwd() });

    // Read back fresh ledger
    if (fs.existsSync(OVERVIEW_FILE) && fs.existsSync(LEDGER_FILE)) {
      const overview = JSON.parse(fs.readFileSync(OVERVIEW_FILE, "utf-8"));
      const ledger = JSON.parse(fs.readFileSync(LEDGER_FILE, "utf-8"));

      return NextResponse.json({
        success: true,
        source: "cli_sync",
        overview,
        boards: ledger.board_performance_summary || {},
        pins: ledger.all_ranked_pins || [],
        logs: stdout,
      });
    }

    return NextResponse.json({ success: true, logs: stdout, warnings: stderr });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Sync execution failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
