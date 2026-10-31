
const pool = require("../config/database");

// GET ALL ALERTS
const getAllAlerts = async () => {
  const [rows] = await pool.query(`
    SELECT
      a.*,
      r.risk_score,
      r.risk_level,
      t.transaction_ref,
      t.customer_ref,
      t.amount
    FROM alerts a
    JOIN risk_assessments r
      ON a.risk_assessment_id = r.id
    JOIN transactions t
      ON r.transaction_id = t.id
    ORDER BY a.id DESC
  `);

  return rows;
};

// GET ALERT BY ID
const getAlertById = async (id) => {
  const [rows] = await pool.query(
    `
    SELECT
      a.*,
      r.risk_score,
      r.risk_level,
      t.transaction_ref,
      t.customer_ref,
      t.amount
    FROM alerts a
    JOIN risk_assessments r
      ON a.risk_assessment_id = r.id
    JOIN transactions t
      ON r.transaction_id = t.id
    WHERE a.id = ?
    `,
    [id]
  );

  return rows[0] || null;
};

// CREATE HIGH-RISK ALERT
const createAlert = async (data) => {
  const {
    risk_assessment_id,
    assigned_to = null,
    analyst_notes = null
  } = data;

  const [assessments] = await pool.query(
    `SELECT id, risk_level
     FROM risk_assessments
     WHERE id = ?`,
    [risk_assessment_id]
  );

  if (assessments.length === 0) {
    const error = new Error("Risk assessment not found");
    error.statusCode = 404;
    throw error;
  }

  if (assessments[0].risk_level !== "HIGH") {
    const error = new Error(
      "Alert can only be created for HIGH-risk assessments"
    );
    error.statusCode = 400;
    throw error;
  }

  const [existing] = await pool.query(
    `SELECT id FROM alerts
     WHERE risk_assessment_id = ?`,
    [risk_assessment_id]
  );

  if (existing.length > 0) {
    const error = new Error(
      "Alert already exists for this risk assessment"
    );
    error.statusCode = 409;
    throw error;
  }

  try {
    const [result] = await pool.query(
      `
      INSERT INTO alerts (
        risk_assessment_id,
        status,
        assigned_to,
        analyst_notes
      )
      VALUES (?, 'OPEN', ?, ?)
      `,
      [
        risk_assessment_id,
        assigned_to,
        analyst_notes
      ]
    );

    return getAlertById(result.insertId);
  } catch (error) {
    if (error.code === "ER_DUP_ENTRY") {
      error.statusCode = 409;
      error.message = "Alert already exists";
    }
    throw error;
  }
};

// UPDATE ALERT STATUS
const updateAlertStatus = async (id, data) => {
  const { status, analyst_notes } = data;

  const [result] = await pool.query(
    `
    UPDATE alerts
    SET
      status = ?,
      analyst_notes = COALESCE(?, analyst_notes)
    WHERE id = ?
    `,
    [status, analyst_notes ?? null, id]
  );

  if (result.affectedRows === 0) {
    return null;
  }

  return getAlertById(id);
};

// DELETE ALERT
const deleteAlert = async (id) => {
  const [result] = await pool.query(
    "DELETE FROM alerts WHERE id = ?",
    [id]
  );

  return result.affectedRows > 0;
};

module.exports = {
  getAllAlerts,
  getAlertById,
  createAlert,
  updateAlertStatus,
  deleteAlert
};
