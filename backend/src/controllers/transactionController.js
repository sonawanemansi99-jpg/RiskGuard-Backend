
const transactionService = require("../services/transactionService");

// GET /api/transactions
// Supports pagination, search, filtering, and sorting
async function getAllTransactions(req, res) {
    try {
        const result = await transactionService.getAllTransactions(
            req.query
        );

        return res.status(200).json({
            success: true,
            message: "Transactions retrieved successfully",
            ...result
        });
    } catch (error) {
        console.error("Get transactions error:", error);

        return res.status(400).json({
            success: false,
            message: "Failed to retrieve transactions",
            error: error.message
        });
    }
}

// POST /api/transactions
// Creates a new transaction
async function createTransaction(req, res) {
    try {
        const {
            transaction_ref,
            customer_ref,
            amount,
            transaction_time
        } = req.body;

        // Validate required fields
        if (
            !transaction_ref ||
            !customer_ref ||
            amount === undefined ||
            amount === null ||
            transaction_time === undefined ||
            transaction_time === null
        ) {
            return res.status(400).json({
                success: false,
                message:
                    "transaction_ref, customer_ref, amount, and transaction_time are required"
            });
        }

        // Validate amount
        if (!Number.isFinite(Number(amount)) || Number(amount) < 0) {
            return res.status(400).json({
                success: false,
                message: "amount must be a valid non-negative number"
            });
        }

        const transaction = await transactionService.createTransaction({
            ...req.body,
            amount: Number(amount)
        });

        return res.status(201).json({
            success: true,
            message: "Transaction created successfully",
            data: transaction
        });
    } catch (error) {
        console.error("Create transaction error:", error);

        // Handle duplicate transaction references
        if (
            error.code === "ER_DUP_ENTRY" ||
            error.code === "23505"
        ) {
            return res.status(409).json({
                success: false,
                message: "Transaction reference already exists"
            });
        }

        return res.status(500).json({
            success: false,
            message: "Failed to create transaction",
            error: error.message,
            code: error.code || null
        });
    }
}

// Keep both controller functions exported
module.exports = {
    getAllTransactions,
    createTransaction
};
