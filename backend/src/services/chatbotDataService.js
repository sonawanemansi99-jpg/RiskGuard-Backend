
const pool = require("../config/database");

async function getTransactionRisk(transactionRef) {
  const [rows] = await pool.execute(
    `SELECT
       t.transaction_ref,
       t.amount,
       t.currency,
       t.location,
       t.merchant_category,
       r.risk_score,
       r.risk_level,
       r.fraud_probability,
       r.reasons,
       r.model_version
     FROM transactions t
     JOIN risk_assessments r
       ON t.id = r.transaction_id
     WHERE t.transaction_ref = ?
     ORDER BY r.id DESC
     LIMIT 1`,
    [transactionRef]
  );

  return rows[0] || null;
}

module.exports = { getTransactionRisk };
