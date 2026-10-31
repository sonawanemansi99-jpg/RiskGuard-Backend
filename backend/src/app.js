
const express = require("express");
const cors = require("cors");

const transactionRoutes = require("./routes/transactionRoutes");
const riskAssessmentRoutes = require("./routes/riskAssessmentRoutes");
const dashboardRoutes = require("./routes/dashboardRoutes");
const alertRoutes = require("./routes/alertRoutes");


const app = express();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => {
    res.json({
        message: "RiskGuard Banking Risk Monitoring Backend is running"
    });
});

app.use("/api/transactions", transactionRoutes);
app.use("/api/risk-assessments", riskAssessmentRoutes);
app.use("/api/dashboard", dashboardRoutes);
app.use("/api/alerts", alertRoutes);






module.exports = app;
