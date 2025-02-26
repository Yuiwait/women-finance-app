// Function to check if a file exists before fetching
async function checkFileExists(url) {
    try {
        let response = await fetch(url, { method: "HEAD" });
        return response.ok;
    } catch (error) {
        console.error("❌ Error checking file existence:", error);
        return false;
    }
}

const API_BASE_URL = window.location.origin.includes("localhost")
    ? "http://127.0.0.1:5001"
    : "https://your-production-api.com";

// Function to load the navbar
async function loadNavbar() {
    let exists = await checkFileExists("components/navbar.html");
    if (!exists) return console.error("❌ Navbar file not found!");

    try {
        let response = await fetch("components/navbar.html");
        let data = await response.text();
        document.getElementById("navbar").innerHTML = data;
        setTimeout(attachDarkModeToggle, 100);
    } catch (error) {
        console.error("❌ Error loading navbar:", error);
    }
}

// Function to load the dashboard
async function loadDashboard() {
    let token = localStorage.getItem("jwtToken");
    if (!token) return (window.location.href = "login.html");

    let exists = await checkFileExists("components/dashboard.html");
    if (!exists) return console.error("❌ Dashboard file not found!");

    try {
        let response = await fetch("components/dashboard.html");
        let data = await response.text();
        let dashboardElement = document.getElementById("dashboard");
        if (dashboardElement) {
            dashboardElement.innerHTML = data;
            console.log("✅ Dashboard loaded successfully.");
            waitForCanvas();
            attachExpenseFormListener();
            loadExpenses();
        }
    } catch (error) {
        console.error("❌ Error loading dashboard:", error);
    }
}

// Function to login user
async function loginUser(event) {
    event.preventDefault();
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    try {
        let response = await fetch(`${API_BASE_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        let data = await response.json();

        if (response.ok) {
            localStorage.setItem("jwtToken", data.access_token);
            window.location.href = "dashboard.html";
        } else {
            alert("Login failed: " + (data.error || "Unknown error"));
        }
    } catch (error) {
        console.error("❌ Error logging in:", error);
    }
}

// Function to register user
async function registerUser(event) {
    event.preventDefault();
    let name = document.getElementById("name").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    let role = document.getElementById("role").value || "user";  // Default role: "user"

    try {
        let response = await fetch(`${API_BASE_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password, role })
        });
        let data = await response.json();

        if (response.ok) {
            alert("Registration successful! Please log in.");
            window.location.href = "login.html";  // ❌ This assumes login.html is in /static/
        } else {
            alert("Registration failed: " + (data.error || "Unknown error"));
        }
    } catch (error) {
        console.error("❌ Error registering user:", error);
    }
}

// Function to load expenses from API
async function loadExpenses() {
    let token = localStorage.getItem("jwtToken");
    if (!token) return (window.location.href = "login.html");

    try {
        let response = await fetch(`${API_BASE_URL}/expenses`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        let data = await response.json();

        if (response.ok) {
            expenseData.labels = data.map(expense => expense.category);
            expenseData.values = data.map(expense => expense.amount);
            updateExpenseChart();
        } else {
            console.error("❌ Error fetching expenses:", data.error || "Unknown error");
        }
    } catch (error) {
        console.error("❌ Error loading expenses:", error);
    }
}

// Function to add expense via API
async function addExpense(event) {
    event.preventDefault();
    let token = localStorage.getItem("jwtToken");
    if (!token) return (window.location.href = "login.html");

    let category = document.getElementById("category").value;
    let amount = parseFloat(document.getElementById("amount").value);

    try {
        let response = await fetch(`${API_BASE_URL}/expenses`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ category, amount })
        });
        let data = await response.json();

        if (response.ok) {
            loadExpenses();
            document.getElementById("expenseForm").reset();
        } else {
            alert("Failed to add expense: " + (data.error || "Unknown error"));
        }
    } catch (error) {
        console.error("❌ Error adding expense:", error);
    }
}

// Logout function
function logoutUser() {
    localStorage.removeItem("jwtToken");
    window.location.href = "login.html";  // ❌ This assumes login.html is in /static/

}

// Attach event listeners
function attachExpenseFormListener() {
    let form = document.getElementById("expenseForm");
    if (form) {
        form.addEventListener("submit", addExpense);
    }
}

// Load everything when the document is ready
document.addEventListener("DOMContentLoaded", async () => {
    await loadNavbar();
    await loadDashboard();
});
