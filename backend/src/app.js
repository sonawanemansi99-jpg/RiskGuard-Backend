
const express = require("express");
const cors = require("cors");

const transactionRoutes = require("./routes/transactionRoutes");
const riskAssessmentRoutes = require("./routes/riskAssessmentRoutes");
const dashboardRoutes = require("./routes/dashboardRoutes");
const alertRoutes = require("./routes/alertRoutes");
const chatbotRoutes = require("./routes/chatbotRoutes");
const authRoutes = require("./routes/authRoutes");

const { verifyToken } = require("./middleware/authMiddleware");

const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
  res.json({
    message: "RiskGuard Banking Risk Monitoring Backend is running"
  });
});

// Public login endpoint
app.use("/api/auth", authRoutes);

// Protected Bank Manager endpoints
app.use("/api/transactions", verifyToken, transactionRoutes);
app.use("/api/risk-assessments", verifyToken, riskAssessmentRoutes);
app.use("/api/dashboard", verifyToken, dashboardRoutes);
app.use("/api/alerts", verifyToken, alertRoutes);
app.use("/api/chatbot", verifyToken, chatbotRoutes);

module.exports = app;
