
const jwt = require("jsonwebtoken");
const pool = require("../config/database");

const verifyToken = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res.status(401).json({
        success: false,
        message: "Authentication token is required"
      });
    }

    const token = authHeader.slice(7);

    if (!process.env.JWT_SECRET) {
      throw new Error("JWT_SECRET is not configured");
    }

    const decoded = jwt.verify(
      token,
      process.env.JWT_SECRET,
      { algorithms: ["HS256"] }
    );

    if (
      !decoded ||
      !Number.isSafeInteger(decoded.id) ||
      decoded.role !== "ADMIN"
    ) {
      return res.status(403).json({
        success: false,
        message: "Admin access required"
      });
    }

    const [rows] = await pool.execute(
      `SELECT id, email, role, is_active
       FROM admins
       WHERE id = ?`,
      [decoded.id]
    );

    const admin = rows[0];

    if (!admin || !admin.is_active || admin.role !== "ADMIN") {
      return res.status(403).json({
        success: false,
        message: "Admin access denied"
      });
    }

    req.admin = {
      id: admin.id,
      email: admin.email,
      role: admin.role
    };

    next();

  } catch (error) {
    if (
      error.name === "TokenExpiredError" ||
      error.name === "JsonWebTokenError" ||
      error.name === "NotBeforeError"
    ) {
      return res.status(401).json({
        success: false,
        message: "Invalid or expired token"
      });
    }

    console.error("Authentication error:", error.message);

    return res.status(500).json({
      success: false,
      message: "Authentication failed"
    });
  }
};

module.exports = { verifyToken };
