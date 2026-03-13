import { getDb } from "./server/db.ts";

async function check() {
  console.log("Attempting to connect to database...");
  try {
    const db = await getDb();
    if (db) {
      console.log("SUCCESS: Database connected and Drizzle initialized!");
    } else {
      console.log("FAILURE: Database not initialized.");
    }
  } catch (error) {
    console.error("CRITICAL ERROR during database initialization:", error);
    process.exit(1);
  }
}

check();
