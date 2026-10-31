const riskAssessmentService = require("../services/riskAssessmentService");

async function createRiskAssessment(req, res) {
    try {
        const { transaction_ref } = req.body;

        if (
            typeof transaction_ref !== "string" ||
            !transaction_ref.trim()
        ) {
            return res.status(400).json({
                success: false,
                message: "Valid transaction_ref is required"
            });
        }

        const assessment =
            await riskAssessmentService.createRiskAssessment(
                transaction_ref.trim()
            );

        return res.status(201).json({
            success: true,
            message: "Risk assessment completed successfully",
            data: assessment
        });
    } catch (error) {
        console.error("Create risk assessment error:", error);

        if (error.statusCode === 404) {
            return res.status(404).json({
                success: false,
                message: error.message
            });
        }

        if (
            error.statusCode === 409 ||
            error.code === "ER_DUP_ENTRY"
        ) {
            return res.status(409).json({
                success: false,
                message:
                    "A risk assessment already exists for this transaction"
            });
        }

        return res.status(500).json({
            success: false,
            message: "Failed to create risk assessment"
        });
    }
}

async function getRiskAssessments(req, res) {
    try {
        const assessments =
            await riskAssessmentService.getAllRiskAssessments();

        return res.status(200).json({
            success: true,
            count: assessments.length,
            data: assessments
        });
    } catch (error) {
        console.error("Get risk assessments error:", error.message);

        return res.status(500).json({
            success: false,
            message: "Failed to retrieve risk assessments"
        });
    }
}

async function getRiskAssessmentById(req, res) {
    try {
        const id = req.params.id;

        if (!/^[1-9]\d*$/.test(id)) {
            return res.status(400).json({
                success: false,
                message: "Valid risk assessment ID is required"
            });
        }

        const assessment =
            await riskAssessmentService.getRiskAssessmentById(id);

        if (!assessment) {
            return res.status(404).json({
                success: false,
                message: "Risk assessment not found"
            });
        }

        return res.status(200).json({
            success: true,
            data: assessment
        });
    } catch (error) {
        console.error("Get risk assessment error:", error.message);

        return res.status(500).json({
            success: false,
            message: "Failed to retrieve risk assessment"
        });
    }
}

module.exports = {
    createRiskAssessment,
    getRiskAssessments,
    getRiskAssessmentById
};