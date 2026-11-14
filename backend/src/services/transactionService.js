const pool = require("../config/database");

// Get transactions with pagination, search, filters, and sorting
async function getAllTransactions(options = {}) {
    const {
        page = 1,
        limit = 10,
        search = "",
        location = "",
        minAmount,
        maxAmount,
        deviceId = "",
        paymentMethod = "",
        riskLevel = "",
        startDate = "",
        endDate = "",
        sortBy = "transaction_time",
        order = "DESC"
    } = options;

    // Validate pagination
    const currentPage = Math.max(1, parseInt(page, 10) || 1);
    const pageSize = Math.min(
        100,
        Math.max(1, parseInt(limit, 10) || 10)
    );
    const offset = (currentPage - 1) * pageSize;

    // Allowed sort columns
    const allowedSortColumns = {
        id: "t.id",
        transaction_time: "t.transaction_time",
        amount: "t.amount",
        transaction_ref: "t.transaction_ref",
        customer_ref: "t.customer_ref",
        location: "t.location",
        risk_score: "r.risk_score",
        risk_level: "r.risk_level"
    };

    const safeSortBy = allowedSortColumns[sortBy] || "t.transaction_time";
    const safeOrder = String(order).toUpperCase() === "ASC" ? "ASC" : "DESC";

    const conditions = [];
    const values = [];

    // Search transaction and customer references
    if (search && search.trim()) {
        conditions.push("(t.transaction_ref LIKE ? OR t.customer_ref LIKE ?)");
        const searchValue = `%${search.trim()}%`;
        values.push(searchValue, searchValue);
    }

    // Filter by location
    if (location && location.trim()) {
        conditions.push("t.location LIKE ?");
        values.push(`%${location.trim()}%`);
    }

    // Filter by minimum amount
    if (minAmount !== undefined && minAmount !== "") {
        const min = Number(minAmount);
        if (!Number.isFinite(min) || min < 0) {
            throw new Error("minAmount must be a valid non-negative number");
        }
        conditions.push("t.amount >= ?");
        values.push(min);
    }

    // Filter by maximum amount
    if (maxAmount !== undefined && maxAmount !== "") {
        const max = Number(maxAmount);
        if (!Number.isFinite(max) || max < 0) {
            throw new Error("maxAmount must be a valid non-negative number");
        }
        conditions.push("t.amount <= ?");
        values.push(max);
    }

    if (
        minAmount !== undefined &&
        minAmount !== "" &&
        maxAmount !== undefined &&
        maxAmount !== "" &&
        Number(minAmount) > Number(maxAmount)
    ) {
        throw new Error("minAmount cannot be greater than maxAmount");
    }

    // Filter by device_id
    if (deviceId && deviceId.trim()) {
        conditions.push("t.device_id LIKE ?");
        values.push(`%${deviceId.trim()}%`);
    }

    // Filter by payment_method
    if (paymentMethod && paymentMethod.trim()) {
        conditions.push("t.payment_method = ?");
        values.push(paymentMethod.trim().toUpperCase());
    }

    // Filter by risk_level
    if (riskLevel && riskLevel.trim()) {
        conditions.push("UPPER(r.risk_level) = ?");
        values.push(riskLevel.trim().toUpperCase());
    }

    // Date range filters
    if (startDate && startDate.trim()) {
        conditions.push("t.transaction_time >= ?");
        values.push(startDate.trim());
    }
    if (endDate && endDate.trim()) {
        conditions.push("t.transaction_time <= ?");
        values.push(endDate.trim());
    }

    const whereClause = conditions.length
        ? `WHERE ${conditions.join(" AND ")}`
        : "";

    // Count query
    const [countRows] = await pool.execute(
        `SELECT COUNT(*) AS total
         FROM transactions t
         LEFT JOIN risk_assessments r ON r.transaction_id = t.id
         ${whereClause}`,
        values
    );

    const total = Number(countRows[0].total);

    // Data query with joined risk assessments
    const [rows] = await pool.execute(
        `SELECT
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
            t.created_at,
            r.risk_score,
            r.risk_level,
            r.fraud_probability,
            r.model_version,
            r.reasons
         FROM transactions t
         LEFT JOIN risk_assessments r ON r.transaction_id = t.id
         ${whereClause}
         ORDER BY ${safeSortBy} ${safeOrder}
         LIMIT ? OFFSET ?`,
        [...values, pageSize, offset]
    );

    return {
        data: rows,
        pagination: {
            page: currentPage,
            limit: pageSize,
            total,
            totalPages: Math.ceil(total / pageSize)
        }
    };
}

// Convert timestamp to MySQL DATETIME format
function formatMySQLDateTime(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        throw new Error("Invalid transaction_time");
    }

    return date.toISOString().slice(0, 19).replace("T", " ");
}

// Create a new transaction
async function createTransaction(data) {
    const {
        transaction_ref,
        customer_ref,
        amount,
        currency = "INR",
        location,
        device_id,
        payment_method,
        merchant_category,
        transaction_time
    } = data;

    const formattedTransactionTime =
        formatMySQLDateTime(transaction_time);

    const [result] = await pool.execute(
        `INSERT INTO transactions (
            transaction_ref,
            customer_ref,
            amount,
            currency,
            location,
            device_id,
            payment_method,
            merchant_category,
            transaction_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [
            transaction_ref,
            customer_ref,
            amount,
            currency,
            location ?? null,
            device_id ?? null,
            payment_method ?? null,
            merchant_category ?? null,
            formattedTransactionTime
        ]
    );

    return {
        id: result.insertId,
        ...data,
        currency,
        transaction_time: formattedTransactionTime
    };
}

module.exports = {
    getAllTransactions,
    createTransaction
};
