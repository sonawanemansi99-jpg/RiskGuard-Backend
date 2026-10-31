
const { loginAdmin } = require("../services/authService");

const login = async (req, res) => {
  try {
    const { email, password } = req.body || {};

    if (
      typeof email !== "string" ||
      !email.trim() ||
      typeof password !== "string" ||
      !password
    ) {
      return res.status(400).json({
        success: false,
        message: "Email and password are required"
      });
    }

    const result = await loginAdmin(
      email.trim().toLowerCase(),
      password
    );

    return res.status(200).json({
      success: true,
      message: "Login successful",
      data: result
    });

  } catch (error) {
    if (error.message === "Invalid email or password") {
      return res.status(401).json({
        success: false,
        message: "Invalid email or password"
      });
    }

    console.error("Login error:", error.message);

    return res.status(500).json({
      success: false,
      message: "Unable to process login"
    });
  }
};

module.exports = { login };
