
const pool = require("../config/database");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

async function loginAdmin(email, password) {
  const [rows] = await pool.execute(
    `SELECT id, full_name, email, password, role, is_active
     FROM admins
     WHERE email = ?`,
    [email]
  );

  const admin = rows[0];

  if (!admin || !admin.is_active) {
    throw new Error("Invalid email or password");
  }

  const isPasswordValid = await bcrypt.compare(
    password,
    admin.password
  );

  if (!isPasswordValid) {
    throw new Error("Invalid email or password");
  }

  if (!process.env.JWT_SECRET) {
    throw new Error("JWT_SECRET is not configured");
  }

  const token = jwt.sign(
    {
      id: admin.id,
      role: admin.role
    },
    process.env.JWT_SECRET,
    {
      expiresIn: "8h",
      algorithm: "HS256"
    }
  );

  return {
    token,
    admin: {
      id: admin.id,
      fullName: admin.full_name,
      email: admin.email,
      role: admin.role
    }
  };
}

module.exports = { loginAdmin };
