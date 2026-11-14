const express = require("express");
const controller = require("../controllers/dashboardController");

const router = express.Router();

router.get("/", controller.getSummary);
router.get("/summary", controller.getSummary);
router.get("/risk-distribution", controller.getRiskDistribution);
router.get("/recent-transactions", controller.getRecentTransactions);
router.get("/transaction-trends", controller.getTransactionTrends);
router.get("/high-risk-transactions", controller.getHighRiskTransactions);
router.get("/location-distribution", controller.getLocationDistribution);
router.get("/payment-method-distribution", controller.getPaymentMethodDistribution);
router.get("/risk-trends", controller.getRiskTrends);
router.get("/alert-trends", controller.getAlertTrends);
router.get("/model-performance", controller.getModelPerformance);
router.get("/drift-status", controller.getDriftStatus);

module.exports = router;
