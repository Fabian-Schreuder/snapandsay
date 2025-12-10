# Test Design: Epic 5 (Admin Oversight & Data Export)

## 1. Scope
This document outlines the test strategy for Epic 5, which focuses on the Admin Dashboard for researchers. The features include viewing all user logs, filtering them, and exporting data.

### Stories Covered
- **Story 5.1: Admin Dashboard View** (Table view, Filters)
- **Story 5.2: Data Export** (CSV/JSON Export)

## 2. Test Scenarios

### TS-5.1: Admin Access & Dashboard View
- **Objective:** Verify that admins can access the dashboard and view the logs table.
- **Preconditions:** User is authenticated with "admin" role (mocked).
- **Steps:**
    1. Navigate to `/admin`.
    2. Verify the page title "Admin Dashboard".
    3. Verify the logs table is visible.
    4. Assert that log entries are displayed (mocked data).
- **Negative Test:** Verify that a non-admin user is redirected/shown 403.

### TS-5.2: Filtering Logs
- **Objective:** Verify that the admin can filter logs by User ID and Date.
- **Steps:**
    1. Enter a User ID in the filter input.
    2. Select a Date in the date picker.
    3. Verify that the API is called with the correct query parameters (`?user_id=...&date=...`).
    4. Verify the table updates (mocked response).

### TS-5.3: Data Export
- **Objective:** Verify that the export function triggers a download.
- **Steps:**
    1. Click the "Export CSV" button.
    2. Verify that the browser initiates a download/API call to `/api/v1/admin/export`.
    3. Verify the file name/format (if possible via download event).

## 3. Mocking Strategy

### Authentication (Admin)
- Mock `**/auth/v1/user` to return a user with admin metadata/claims if the application uses them, or simply ensure the backend API mocks accept the requests.
- *Note:* The frontend might check a specific user ID or role field. I will assume a role check or specific ID check is needed.

### Admin Logs API
- **Endpoint:** `GET /api/v1/admin/logs`
- **Response:**
```json
{
  "data": [
    { "id": "log-1", "user_id": "user-A", "description": "Admin view test", "calories": 500, "created_at": "..." }
  ],
  "meta": { "total": 1, "page": 1 }
}
```

### Export API
- **Endpoint:** `GET /api/v1/admin/export`
- **Response:** Content-Disposition header with CSV data.

## 4. Risks & Mitigation
- **R-5-1 (Unauthorized Access):** Ensure the negative test for non-admin access is robust.
- **R-5-2 (Large Data Sets):** The logs table might crash with many logs. We will test with a small set but verify pagination controls exist if implemented.

