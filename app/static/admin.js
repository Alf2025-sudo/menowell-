
// ==========================================
// MENOWELL ADMIN DASHBOARD
// ==========================================

const appointmentTableBody = document.getElementById("appointmentTableBody");
const totalCount = document.getElementById("totalCount");
const pendingCount = document.getElementById("pendingCount");
const reviewedCount = document.getElementById("reviewedCount");
const searchRequests = document.getElementById("searchRequests");
const filterStatus = document.getElementById("filterStatus");
const refreshRequests = document.getElementById("refreshRequests");
const adminMessage = document.getElementById("adminMessage");

let allAppointmentRequests = [];

function adminEscape(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

// Retrieve appointment requests from the backend.
async function loadAppointmentRequests() {
    adminMessage.textContent = "Loading appointment requests...";

    try {
        const response = await fetch("/api/admin/appointment-requests");

        if (!response.ok) {
            throw new Error("Unable to retrieve appointment requests.");
        }

        const data = await response.json();

        allAppointmentRequests = data.requests || [];

        updateDashboardStatistics();
        displayAppointmentRequests();

        adminMessage.textContent =
            `Successfully loaded ${allAppointmentRequests.length} appointment request(s).`;

    } catch (error) {
        appointmentTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="admin-empty">
                    ${adminEscape(error.message)}
                </td>
            </tr>
        `;

        adminMessage.textContent = "Dashboard loading failed.";
        console.error("Admin dashboard error:", error);
    }
}

// Update the dashboard summary figures.
function updateDashboardStatistics() {
    totalCount.textContent = allAppointmentRequests.length;

    pendingCount.textContent = allAppointmentRequests.filter(
        request => request.request_status === "pending"
    ).length;

    reviewedCount.textContent = allAppointmentRequests.filter(
        request => request.request_status === "reviewed"
    ).length;
}

// Display the appointment requests in the table.
function displayAppointmentRequests() {
    const searchTerm = searchRequests.value.toLowerCase().trim();
    const selectedStatus = filterStatus.value;

    const filteredRequests = allAppointmentRequests.filter(request => {
        const searchableText = [
            request.reference_number,
            request.provider_name,
            request.specialty
        ].join(" ").toLowerCase();

        const matchesSearch = searchableText.includes(searchTerm);

        const matchesStatus = !selectedStatus ||
            request.request_status === selectedStatus;

        return matchesSearch && matchesStatus;
    });

    if (filteredRequests.length === 0) {
        appointmentTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="admin-empty">
                    No matching appointment requests found.
                </td>
            </tr>
        `;
        return;
    }

    appointmentTableBody.innerHTML = filteredRequests.map(request => {
        const status = String(request.request_status || "pending").toLowerCase();

        return `
            <tr>
                <td><strong>${adminEscape(request.reference_number)}</strong></td>
                <td>${adminEscape(request.provider_name)}</td>
                <td>${adminEscape(request.specialty)}</td>
                <td>${adminEscape(request.preferred_date)}</td>
                <td>${adminEscape(request.preferred_time)}</td>
                <td>
                    <span class="admin-status status-${adminEscape(status)}">
                        ${adminEscape(status)}
                    </span>
                </td>
                <td>
                    <select
                        class="status-select"
                        data-reference="${adminEscape(request.reference_number)}"
                        aria-label="Update status for ${adminEscape(request.reference_number)}"
                    >
                        <option value="pending" ${status === "pending" ? "selected" : ""}>Pending</option>
                        <option value="reviewed" ${status === "reviewed" ? "selected" : ""}>Reviewed</option>
                        <option value="completed" ${status === "completed" ? "selected" : ""}>Completed</option>
                        <option value="cancelled" ${status === "cancelled" ? "selected" : ""}>Cancelled</option>
                    </select>
                </td>
            </tr>
        `;
    }).join("");
}

// Search and filter events.
searchRequests.addEventListener("input", displayAppointmentRequests);
filterStatus.addEventListener("change", displayAppointmentRequests);

// Refresh the dashboard.
refreshRequests.addEventListener("click", loadAppointmentRequests);

// Update an appointment status.
appointmentTableBody.addEventListener("change", async function(event) {
    if (!event.target.classList.contains("status-select")) {
        return;
    }

    const statusSelect = event.target;
    const referenceNumber = statusSelect.dataset.reference;
    const newStatus = statusSelect.value;

    const originalRequest = allAppointmentRequests.find(
        request => request.reference_number === referenceNumber
    );

    if (!originalRequest) {
        return;
    }

    const previousStatus = originalRequest.request_status;
    statusSelect.disabled = true;

    adminMessage.textContent =
        `Updating request ${referenceNumber}...`;

    try {
        const response = await fetch(
            `/api/admin/appointment-requests/${encodeURIComponent(referenceNumber)}`,
            {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    status: newStatus
                })
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof result.detail === "string"
                    ? result.detail
                    : "Could not update the request status."
            );
        }

        originalRequest.request_status = result.request_status;

        updateDashboardStatistics();
        displayAppointmentRequests();

        adminMessage.textContent =
            `Request ${referenceNumber} successfully updated to ${newStatus}.`;

    } catch (error) {
        statusSelect.value = previousStatus;
        statusSelect.disabled = false;

        adminMessage.textContent = error.message;
    }
});

// Load requests when the dashboard opens.
loadAppointmentRequests();
