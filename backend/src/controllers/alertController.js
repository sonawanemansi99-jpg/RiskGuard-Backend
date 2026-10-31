
const alertService = require("../services/alertService");

const handleError = (res, error) => {
  console.error("Alert API Error:", error);

  return res.status(error.statusCode || 500).json({
    success: false,
    message: error.statusCode
      ? error.message
      : "Internal server error"
  });
};

// GET ALL
const getAllAlerts = async (req, res) => {
  try {
    const alerts = await alertService.getAllAlerts();

    return res.status(200).json({
      success: true,
      message: "Alerts fetched successfully",
      data: alerts
    });
  } catch (error) {
    return handleError(res, error);
  }
};

// GET BY ID
const getAlertById = async (req, res) => {
  try {
    const alert = await alertService.getAlertById(
      req.params.id
    );

    if (!alert) {
      return res.status(404).json({
        success: false,
        message: "Alert not found"
      });
    }

    return res.status(200).json({
      success: true,
      data: alert
    });
  } catch (error) {
    return handleError(res, error);
  }
};

// CREATE ALERT
const createAlert = async (req, res) => {
  try {
    const {
      risk_assessment_id,
      assigned_to,
      analyst_notes
    } = req.body;

    const assessmentId = Number(risk_assessment_id);

    if (
      !Number.isSafeInteger(assessmentId) ||
      assessmentId <= 0
    ) {
      return res.status(400).json({
        success: false,
        message: "Valid risk_assessment_id is required"
      });
    }

    const alert = await alertService.createAlert({
      risk_assessment_id: assessmentId,
      assigned_to,
      analyst_notes
    });

    return res.status(201).json({
      success: true,
      message: "HIGH-risk alert created successfully",
      data: alert
    });
  } catch (error) {
    return handleError(res, error);
  }
};

// UPDATE STATUS
const updateAlertStatus = async (req, res) => {
  try {
    const { status, analyst_notes } = req.body;

    const allowedStatuses = [
      "OPEN",
      "IN_PROGRESS",
      "RESOLVED",
      "CLOSED"
    ];

    if (!allowedStatuses.includes(status)) {
      return res.status(400).json({
        success: false,
        message: "Invalid alert status"
      });
    }

    const alert = await alertService.updateAlertStatus(
      req.params.id,
      { status, analyst_notes }
    );

    if (!alert) {
      return res.status(404).json({
        success: false,
        message: "Alert not found"
      });
    }

    return res.status(200).json({
      success: true,
      message: "Alert updated successfully",
      data: alert
    });
  } catch (error) {
    return handleError(res, error);
  }
};

// DELETE
const deleteAlert = async (req, res) => {
  try {
    const deleted = await alertService.deleteAlert(
      req.params.id
    );

    if (!deleted) {
      return res.status(404).json({
        success: false,
        message: "Alert not found"
      });
    }

    return res.status(200).json({
      success: true,
      message: "Alert deleted successfully"
    });
  } catch (error) {
    return handleError(res, error);
  }
};

module.exports = {
  getAllAlerts,
  getAlertById,
  createAlert,
  updateAlertStatus,
  deleteAlert
};
