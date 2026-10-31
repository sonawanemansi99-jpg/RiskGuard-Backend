const express = require("express");

const router = express.Router();

const {
    createRiskAssessment,
    getRiskAssessments,
    getRiskAssessmentById
} = require("../controllers/riskAssessmentController");

router.post("/", createRiskAssessment);
router.get("/", getRiskAssessments);
router.get("/:id", getRiskAssessmentById);

module.exports = router;