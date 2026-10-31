
const pool = require("./database");

async function testConnection() {
    try {
        const [rows] = await pool.query("SELECT 1 AS connected");
        console.log("MySQL connected successfully:", rows);
    } catch (error) {
        console.error("MySQL connection failed:", error.message);
        process.exitCode = 1;
    } finally {
        await pool.end();
    }
}

testConnection();
