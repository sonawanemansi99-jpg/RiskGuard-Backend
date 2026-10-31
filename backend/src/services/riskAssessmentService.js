
const pool = require("../config/database");

// Calculate a transparent, rule-based risk score.
// This is a baseline, not a trained ML model.
function calculateRisk(transaction) {
    let riskScore = 0;
    const reasons = [];

    const amount = Number(transaction.amount);
    const transactionDate = new Date(
        `${transaction.transaction_time.toISOString
            ? transaction.transaction_time.toISOString().replace("T", " ").slice(0, 23)
            : transaction.transaction_time}`
    );

    // Rule 1: Transaction amount
    if (amount >= 100000) {
        riskScore += 45;
        reasons.push("Very high transaction amount");
    } else if (amount >= 50000) {
        riskScore += 30;
        reasons.push("High transaction amount");
    } else if (amount >= 20000) {
        riskScore += 15;
        reasons.push("Elevated transaction amount");
    }

    // Rule 2: Transaction time
    // Interpret MySQL DATETIME as a local clock value for this baseline.
    const timeText = String(transaction.transaction_time);
    const match = timeText.match(/(?:T|\s)(\d{2}):(\d{2})/);

    if (match) {
        const hour = Number(match[1]);

        if (hour >= 0 && hour < 5) {
            riskScore += 20;
            reasons.push("Transaction occurred during late-night hours");
        }
    } else if (
        !Number.isNaN(transactionDate.getTime()) &&
        transactionDate.getUTCHours() < 5
    ) {
        riskScore += 20;
        reasons.push("Transaction occurred during late-night hours");
    }

    // Rule 3: Device information
    if (!transaction.device_id) {
        riskScore += 10;
        reasons.push("Device information is missing");
    }

    // Rule 4: Location information
    if (!transaction.location) {
        riskScore += 10;
        reasons.push("Transaction location is missing");
    }

    // Keep score within the valid range.
    riskScore = Math.min(riskScore, 100);

    let riskLevel = "LOW";

    if (riskScore >= 60) {
        riskLevel = "HIGH";
    } else if (riskScore >= 30) {
        riskLevel = "MEDIUM";
    }

    if (reasons.length === 0) {
        reasons.push("No risk indicators detected by the current rules");
    }

    return {
        risk_score: riskScore,
        risk_level: riskLevel,
        // Heuristic score-derived indicator, NOT calibrated fraud probability.
        fraud_probability: Number((riskScore / 100).toFixed(5)),
        reasons
    };
}

// Create an assessment for an existing transaction.
async function createRiskAssessment(transactionRef) {
    const [transactions] = await pool.execute(
        `SELECT
            id,
            transaction_ref,
            customer_ref,
            amount,
            currency,
            location,
            device_id,
            merchant_category,
            transaction_time
         FROM transactions
         WHERE transaction_ref = ?
         LIMIT 1`,
        [transactionRef]
    );

    if (transactions.length === 0) {
        const error = new Error("Transaction not found");
        error.statusCode = 404;
        throw error;
    }

    const transaction = transactions[0];

    const [existing] = await pool.execute(
        `SELECT id
         FROM risk_assessments
         WHERE transaction_id = ?
         LIMIT 1`,
        [transaction.id]
    );

    if (existing.length > 0) {
        const error = new Error(
            "A risk assessment already exists for this transaction"
        );
        error.statusCode = 409;
        throw error;
    }

    const assessment = calculateRisk(transaction);

    const [result] = await pool.execute(
        `INSERT INTO risk_assessments
        (
            transaction_id,
            risk_score,
            risk_level,
            fraud_probability,
            reasons,
            model_version
        )
        VALUES (?, ?, ?, ?, ?, ?)`,
        [
            transaction.id,
            assessment.risk_score,
            assessment.risk_level,
            assessment.fraud_probability,
            JSON.stringify(assessment.reasons),
            "rules-v1.0"
        ]
    );

    return {
        id: result.insertId,
        transaction_id: transaction.id,
        transaction_ref: transaction.transaction_ref,
        ...assessment,
        model_version: "rules-v1.0"
    };
}

// Retrieve all assessments.
async function getAllRiskAssessments() {
    const [rows] = await pool.query(
        `SELECT
            ra.id,
            ra.transaction_id,
            t.transaction_ref,
            t.customer_ref,
            t.amount,
            t.currency,
            ra.risk_score,
            ra.risk_level,
            ra.fraud_probability,
            ra.reasons,
            ra.model_version,
            ra.assessed_at
         FROM risk_assessments ra
         INNER JOIN transactions t
            ON t.id = ra.transaction_id
         ORDER BY ra.assessed_at DESC`
    );

    return rows;
}

// Retrieve one assessment by its ID.
async function getRiskAssessmentById(id) {
    const [rows] = await pool.execute(
        `SELECT
            ra.id,
            ra.transaction_id,
            t.transaction_ref,
            t.customer_ref,
            t.amount,
            t.currency,
            ra.risk_score,
            ra.risk_level,
            ra.fraud_probability,
            ra.reasons,
            ra.model_version,
            ra.assessed_at
         FROM risk_assessments ra
         INNER JOIN transactions t
            ON t.id = ra.transaction_id
         WHERE ra.id = ?
         LIMIT 1`,
        [id]
    );

    return rows[0] || null;
}

module.exports = {
    createRiskAssessment,
    getAllRiskAssessments,
    getRiskAssessmentById
};