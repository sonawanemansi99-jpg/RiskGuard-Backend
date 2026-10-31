
const pool = require("../config/database");

// 1. Dashboard summary
async function getSummary() {
  const [[transactions]] = await pool.query(`
    SELECT COUNT(*) AS total_transactions
    FROM transactions
  `);

  const [[assessments]] = await pool.query(`
    SELECT
      COUNT(*) AS assessed_transactions,
      COALESCE(AVG(risk_score), 0) AS average_risk_score
    FROM risk_assessments
  `);

  const [[alerts]] = await pool.query(`
    SELECT COUNT(*) AS total_alerts
    FROM alerts
  `);

  return {
    totalTransactions: Number(transactions.total_transactions),
    assessedTransactions: Number(assessments.assessed_transactions),
    averageRiskScore: Number(assessments.average_risk_score),
    totalAlerts: Number(alerts.total_alerts)
  };
}

// 2. Risk distribution
async function getRiskDistribution() {
  const [rows] = await pool.query(`
    SELECT
      UPPER(risk_level) AS risk_level,
      COUNT(*) AS count
    FROM risk_assessments
    GROUP BY UPPER(risk_level)
  `);

  const distribution = { LOW: 0, MEDIUM: 0, HIGH: 0 };

  for (const row of rows) {
    if (Object.prototype.hasOwnProperty.call(distribution, row.risk_level)) {
      distribution[row.risk_level] = Number(row.count);
    }
  }

  return distribution;
}

// 3. Recent transactions with their risk assessments
async function getRecentTransactions() {
  const [rows] = await pool.query(`
    SELECT
      t.id,
      t.transaction_ref,
      t.customer_ref,
      t.amount,
      t.currency,
      t.location,
      t.device_id,
      t.merchant_category,
      t.transaction_time,
      r.risk_score,
      r.risk_level,
      r.fraud_probability,
      r.model_version
    FROM transactions t
    LEFT JOIN risk_assessments r
      ON r.transaction_id = t.id
    ORDER BY t.id DESC
    LIMIT 10
  `);

  return rows;
}

// 4. Daily transaction trends (last 7 days)
async function getTransactionTrends() {
  const [rows] = await pool.query(`
    SELECT
      DATE(transaction_time) AS date,
      COUNT(*) AS transaction_count,
      COALESCE(SUM(amount), 0) AS total_amount
    FROM transactions
    WHERE transaction_time >= CURRENT_DATE - INTERVAL 6 DAY
      AND transaction_time < CURRENT_DATE + INTERVAL 1 DAY
    GROUP BY DATE(transaction_time)
    ORDER BY DATE(transaction_time)
  `);

  return rows.map(row => ({
    date: row.date,
    transactionCount: Number(row.transaction_count),
    totalAmount: Number(row.total_amount)
  }));
}

// 5. High-risk transactions
async function getHighRiskTransactions() {
  const [rows] = await pool.query(`
    SELECT
      t.id,
      t.transaction_ref,
      t.customer_ref,
      t.amount,
      t.currency,
      t.location,
      t.device_id,
      t.transaction_time,
      r.risk_score,
      r.risk_level,
      r.reasons,
      r.model_version
    FROM risk_assessments r
    JOIN transactions t ON t.id = r.transaction_id
    WHERE UPPER(r.risk_level) = 'HIGH'
    ORDER BY r.id DESC
    LIMIT 20
  `);

  return rows;
}

// 6. Latest model performance
async function getModelPerformance() {
  const [rows] = await pool.query(`
    SELECT
      version,
      algorithm,
      status,
      precision_score,
      recall_score,
      f1_score,
      training_started_at,
      activated_at
    FROM model_versions
    ORDER BY activated_at DESC
    LIMIT 1
  `);

  return rows[0] || null;
}

// 7. Latest concept drift status
async function getDriftStatus() {
  const [rows] = await pool.query(`
    SELECT
      detector_name,
      drift_detected,
      severity,
      details,
      detected_at
    FROM drift_events
    ORDER BY detected_at DESC
    LIMIT 1
  `);

  return rows[0] || null;
}

module.exports = {
  getSummary,
  getRiskDistribution,
  getRecentTransactions,
  getTransactionTrends,
  getHighRiskTransactions,
  getModelPerformance,
  getDriftStatus
};
