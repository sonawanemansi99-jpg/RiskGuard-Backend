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

// 3. Recent transactions with their risk assessments & payment method
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
      t.payment_method,
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

// 4. Daily transaction trends (latest 7 recorded days)
async function getTransactionTrends() {
  const [rows] = await pool.query(`
    SELECT
      DATE(transaction_time) AS date,
      COUNT(*) AS transaction_count,
      COALESCE(SUM(amount), 0) AS total_amount
    FROM transactions
    GROUP BY DATE(transaction_time)
    ORDER BY DATE(transaction_time) DESC
    LIMIT 7
  `);

  return rows.reverse().map(row => ({
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
      t.payment_method,
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

// 6. Transactions by Location
async function getLocationDistribution() {
  const [rows] = await pool.query(`
    SELECT
      COALESCE(location, 'Unknown Location') AS location,
      COUNT(*) AS count,
      COALESCE(SUM(amount), 0) AS total_amount
    FROM transactions
    GROUP BY location
    ORDER BY count DESC
    LIMIT 6
  `);

  return rows.map(r => ({
    location: r.location,
    count: Number(r.count),
    totalAmount: Number(r.total_amount)
  }));
}

// 7. Transactions and Risk by Payment Method
async function getPaymentMethodDistribution() {
  const [rows] = await pool.query(`
    SELECT
      COALESCE(t.payment_method, 'OTHER') AS payment_method,
      COUNT(*) AS total_count,
      SUM(CASE WHEN UPPER(r.risk_level) = 'HIGH' THEN 1 ELSE 0 END) AS high_risk_count,
      SUM(CASE WHEN UPPER(r.risk_level) = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk_count,
      SUM(CASE WHEN UPPER(r.risk_level) = 'LOW' THEN 1 ELSE 0 END) AS low_risk_count
    FROM transactions t
    LEFT JOIN risk_assessments r ON r.transaction_id = t.id
    GROUP BY t.payment_method
    ORDER BY total_count DESC
  `);

  return rows.map(r => ({
    paymentMethod: r.payment_method,
    totalCount: Number(r.total_count),
    highRiskCount: Number(r.high_risk_count),
    mediumRiskCount: Number(r.medium_risk_count),
    lowRiskCount: Number(r.low_risk_count)
  }));
}

// 8. Risk Level Trends (Over time)
async function getRiskTrends() {
  const [rows] = await pool.query(`
    SELECT
      DATE(t.transaction_time) AS date,
      SUM(CASE WHEN UPPER(r.risk_level) = 'LOW' THEN 1 ELSE 0 END) AS low_count,
      SUM(CASE WHEN UPPER(r.risk_level) = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_count,
      SUM(CASE WHEN UPPER(r.risk_level) = 'HIGH' THEN 1 ELSE 0 END) AS high_count
    FROM transactions t
    JOIN risk_assessments r ON r.transaction_id = t.id
    GROUP BY DATE(t.transaction_time)
    ORDER BY DATE(t.transaction_time) DESC
    LIMIT 7
  `);

  return rows.reverse().map(r => ({
    date: r.date,
    low: Number(r.low_count),
    medium: Number(r.medium_count),
    high: Number(r.high_count)
  }));
}

// 9. Alert Trends (Over time)
async function getAlertTrends() {
  const [rows] = await pool.query(`
    SELECT
      DATE(created_at) AS date,
      COUNT(*) AS alert_count,
      SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) AS open_count,
      SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) AS in_progress_count,
      SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) AS resolved_count
    FROM alerts
    GROUP BY DATE(created_at)
    ORDER BY DATE(created_at) DESC
    LIMIT 7
  `);

  return rows.reverse().map(r => ({
    date: r.date,
    alertCount: Number(r.alert_count),
    openCount: Number(r.open_count),
    inProgressCount: Number(r.in_progress_count),
    resolvedCount: Number(r.resolved_count)
  }));
}

// 10. Model Performance
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

// 11. Concept Drift Status
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
  getLocationDistribution,
  getPaymentMethodDistribution,
  getRiskTrends,
  getAlertTrends,
  getModelPerformance,
  getDriftStatus
};
