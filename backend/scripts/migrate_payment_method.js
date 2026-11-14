require("dotenv").config();
const mysql = require("mysql2/promise");

async function migrate() {
  const conn = await mysql.createConnection({
    host: process.env.DB_HOST,
    port: process.env.DB_PORT,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
  });

  // Align alerts status ENUM
  console.log("Aligning alerts status ENUM...");
  await conn.execute(`
    ALTER TABLE alerts MODIFY COLUMN status ENUM('OPEN','IN_PROGRESS','REVIEWING','RESOLVED','CLOSED','FALSE_POSITIVE') NOT NULL DEFAULT 'OPEN'
  `);

  // Seed alerts if empty
  const [alertsCount] = await conn.execute("SELECT COUNT(*) as count FROM alerts");
  console.log("Current alerts count:", alertsCount[0].count);

  if (alertsCount[0].count === 0) {
    console.log("Seeding alerts table from existing HIGH risk assessments...");
    const [highRa] = await conn.execute(`
      SELECT ra.id, ra.transaction_id, t.amount, t.location, t.transaction_ref
      FROM risk_assessments ra
      JOIN transactions t ON t.id = ra.transaction_id
      WHERE ra.risk_level = 'HIGH'
      ORDER BY ra.id DESC
      LIMIT 12
    `);

    const investigators = ["Emily Wang", "John Lee", "Amina Hassan", "Sara Lee", "Mike Chen"];
    const statuses = ["OPEN", "IN_PROGRESS", "OPEN", "RESOLVED", "OPEN"];

    for (let i = 0; i < highRa.length; i++) {
      const ra = highRa[i];
      const assigned = investigators[i % investigators.length];
      const status = statuses[i % statuses.length];
      const notes = `High-risk transaction flagged for payment amount INR ${Number(ra.amount).toLocaleString('en-IN')} at ${ra.location || 'Unknown Location'}. Under active review.`;
      await conn.execute(
        "INSERT INTO alerts (risk_assessment_id, status, assigned_to, analyst_notes) VALUES (?, ?, ?, ?)",
        [ra.id, status, assigned, notes]
      );
    }
    console.log(`Seeded ${highRa.length} alerts successfully.`);
  }

  const [finalAlerts] = await conn.execute("SELECT COUNT(*) as count FROM alerts");
  console.log("Final alerts count in DB:", finalAlerts[0].count);

  await conn.end();
}

migrate()
  .then(() => console.log("Done."))
  .catch(console.error);
