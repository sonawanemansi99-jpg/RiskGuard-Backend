
const dashboardService = require("../services/dashboardService");

function handleDashboardRequest(serviceMethod, message) {
  return async (req, res) => {
    try {
      const data = await serviceMethod();

      return res.status(200).json({
        success: true,
        message,
        data
      });
    } catch (error) {
      console.error(`${message}:`, error);

      return res.status(500).json({
        success: false,
        message: "Failed to retrieve dashboard data",
        error: error.message,
        code: error.code || null
      });
    }
  };
}

module.exports = {
  getSummary: handleDashboardRequest(
    dashboardService.getSummary,
    "Dashboard summary retrieved successfully"
  ),

  getRiskDistribution: handleDashboardRequest(
    dashboardService.getRiskDistribution,
    "Risk distribution retrieved successfully"
  ),

  getRecentTransactions: handleDashboardRequest(
    dashboardService.getRecentTransactions,
    "Recent transactions retrieved successfully"
  ),

  getTransactionTrends: handleDashboardRequest(
    dashboardService.getTransactionTrends,
    "Transaction trends retrieved successfully"
  ),

  getHighRiskTransactions: handleDashboardRequest(
    dashboardService.getHighRiskTransactions,
    "High-risk transactions retrieved successfully"
  ),

  getModelPerformance: handleDashboardRequest(
    dashboardService.getModelPerformance,
    "Model performance retrieved successfully"
  ),

  getDriftStatus: handleDashboardRequest(
    dashboardService.getDriftStatus,
    "Drift status retrieved successfully"
  )
};
