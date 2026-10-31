
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

    // Only allow sorting by known database columns
    const allowedSortColumns = [
        "id",
        "transaction_time",
        "amount",
        "transaction_ref",
        "customer_ref"
    ];

    const safeSortBy = allowedSortColumns.includes(sortBy)
        ? sortBy
        : "transaction_time";

    const safeOrder = String(order).toUpperCase() === "ASC"
        ? "ASC"
        : "DESC";

    const conditions = [];
    const values = [];

    // Search transaction and customer references
    if (search.trim()) {
        conditions.push(
            "(transaction_ref LIKE ? OR customer_ref LIKE ?)"
        );
        const searchValue = `%${search.trim()}%`;
        values.push(searchValue, searchValue);
    }

    // Filter by location
    if (location.trim()) {
        conditions.push("location LIKE ?");
        values.push(`%${location.trim()}%`);
    }

    // Filter by minimum amount
    if (minAmount !== undefined && minAmount !== "") {
        const min = Number(minAmount);
        if (!Number.isFinite(min) || min < 0) {
            throw new Error("minAmount must be a valid non-negative number");
        }
        conditions.push("amount >= ?");
        values.push(min);
    }

    // Filter by maximum amount
    if (maxAmount !== undefined && maxAmount !== "") {
        const max = Number(maxAmount);
        if (!Number.isFinite(max) || max < 0) {
            throw new Error("maxAmount must be a valid non-negative number");
        }
        conditions.push("amount <= ?");
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

    const whereClause = conditions.length
        ? `WHERE ${conditions.join(" AND ")}`
        : "";

    // Get the total number of matching transactions
    const [countRows] = await pool.execute(
        `SELECT COUNT(*) AS total
         FROM transactions
         ${whereClause}`,
        values
    );

    const total = Number(countRows[0].total);

    // Get the requested page
    const [rows] = await pool.execute(
        `SELECT *
         FROM transactions
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
            merchant_category,
            transaction_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [
            transaction_ref,
            customer_ref,
            amount,
            currency,
            location ?? null,
            device_id ?? null,
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
