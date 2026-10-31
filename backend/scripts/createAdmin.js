
require("dotenv").config();

const bcrypt = require("bcryptjs");
const pool = require("../src/config/database");
const readline = require("node:readline/promises");

async function createAdmin() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  try {
    const fullName = (await rl.question("Manager full name: ")).trim();
    const email = (await rl.question("Manager email: ")).trim().toLowerCase();
    const password = await rl.question("Manager password: ");

    if (!fullName || !email || password.length < 12) {
      throw new Error(
        "Name and email are required. Password must be at least 12 characters."
      );
    }

    const [existing] = await pool.execute(
      "SELECT id FROM admins WHERE email = ?",
      [email]
    );

    if (existing.length > 0) {
      throw new Error("An admin with this email already exists.");
    }

    const hashedPassword = await bcrypt.hash(password, 12);

    await pool.execute(
      `INSERT INTO admins
       (full_name, email, password, role, is_active)
       VALUES (?, ?, ?, 'ADMIN', TRUE)`,
      [fullName, email, hashedPassword]
    );

    console.log("Bank Manager account created successfully.");

  } catch (error) {
    console.error("Admin setup error:", error.message);
  } finally {
    rl.close();
    await pool.end();
  }
}

createAdmin();
