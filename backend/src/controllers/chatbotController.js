
const { askGemini } = require("../services/chatbotService");

const askChatbot = async (req, res) => {
  try {
    const { message, transactionRef } = req.body || {};

    if (
      typeof message !== "string" ||
      !message.trim() ||
      message.length > 1000
    ) {
      return res.status(400).json({
        success: false,
        message: "Please provide a valid message (max 1000 characters)."
      });
    }

    if (
      transactionRef !== undefined &&
      (
        typeof transactionRef !== "string" ||
        !/^[a-zA-Z0-9_-]{1,100}$/.test(transactionRef)
      )
    ) {
      return res.status(400).json({
        success: false,
        message: "Invalid transaction reference."
      });
    }

    // The route is protected by JWT middleware.
    // Only active ADMIN accounts may reach this controller.
    if (!req.admin || req.admin.role !== "ADMIN") {
      return res.status(403).json({
        success: false,
        message: "Admin access required."
      });
    }

    const reply = await askGemini(
      message.trim(),
      transactionRef || null
    );

    return res.status(200).json({
      success: true,
      message: "Chatbot response generated successfully.",
      data: {
        reply
      }
    });

  } catch (error) {
    console.error("Chatbot error:", error.message);

    return res.status(500).json({
      success: false,
      message: "Unable to process chatbot request."
    });
  }
};

module.exports = { askChatbot };
git branch