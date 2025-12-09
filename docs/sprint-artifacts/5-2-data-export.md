# Story 5.2: Data Export

**Epic:** [Epic 5: Admin Oversight & Data Export](../epics.md#epic-5-admin-oversight--data-export)
**Sprint:** 4 (Implementation Phase)
**Status:** Done
**Estimation:** 3 Points

## Goal
As an Admin, I want to export dietary data (logs) in CSV or JSON format, so that I can perform offline analysis or integrate with other tools.

## Context
This story builds upon the [Admin Dashboard (5.1)](./5-1-admin-dashboard-view.md). Now that admins can view logs, they need to extract this data. This feature focuses on a flexible export mechanism that supports filtering (initially by date range and user, inheriting filters from the dashboard if possible) and format selection.

## Acceptance Criteria
- [ ] **Export Button:** A clearly visible "Export Data" button exists on the Admin Dashboard.
- [ ] **Format Selection:** User can choose between "CSV" and "JSON" formats (e.g., via a dropdown or modal).
- [ ] **Filter adherence:** The export respects the currently active filters on the dashboard (e.g., if I filtered by "User A", the export only contains "User A's" logs). *MVP: If passing filters is too complex, export all/by date is acceptable, but passing dashboard state is preferred.*
- [ ] **CSV Structure:** CSV file contains columns: `Log ID`, `Anonymous ID`, `Meal Type`, `Food Items` (joined string), `Calories`, `Created At`, `Transcription`.
- [ ] **JSON Structure:** JSON file contains an array of log objects with full details including `anonymous_id`.
- [ ] **Security:** Only authenticated Admins can trigger the export endpoint.
- [ ] **Performance:** The system handles the export of at least 1000 logs without timing out (consider streaming response if needed).
- [ ] **Data Precision:** Timestamps (e.g., `Created At`) must be in ISO-8601 format (UTC) to avoid ambiguity.

## Tasks

### Backend
1.  **Service Layer (`backend/app/services/export_service.py`):**
    -   Create a service to handle data transformation.
    -   Implement `export_logs_as_csv(logs: List[Log]) -> Request` (or stream).
    -   Implement `export_logs_as_json(logs: List[Log]) -> Request`.
    -   *Note: Reuse `log_service.get_all_logs` for fetching data with filters, but ensure it uses `joinedload(Log.user)` to prevent N+1 queries when accessing user anonymous_id.*
2.  **API Endpoint (`backend/app/api/v1/endpoints/admin.py`):**
    -   `GET /api/v1/admin/export`
    -   Query Params: `format` (csv/json), `start_date`, `end_date`, `user_id`, `min_calories`, `max_calories` (match `get_logs` params).
    -   Dependency: `deps.get_current_admin`.
    -   Return: `StreamingResponse` with appropriate `Content-Disposition` header (attachment; filename=...).
3.  **Tests (`backend/tests/api/test_admin_export.py`):**
    -   Test export as CSV (verify headers and content).
    -   Test export as JSON.
    -   Test export with filters.
    -   Test unauthorized access (403).

### Frontend
1.  **API Client (`frontend/lib/api.ts`):**
    -   Add `adminApi.exportLogs(filters, format)` method. *This might need to handle Blob/download.*
2.  **Export Component (`frontend/components/features/admin/ExportDataButton.tsx`):**
    -   Button with a dropdown menu (using Shadcn UI `DropdownMenu` or `Select`).
    -   Options: "Export as CSV", "Export as JSON".
3.  **Integration (`frontend/app/(dashboard)/admin/page.tsx`):**
    -   Place `ExportDataButton` near the Filters.
    -   Pass current filter state to the export function.
    -   Handle the file download (create object URL from blob and trigger click).
    -   Show `toast` notifications for feedback: "Generating export...", "Export downloaded successfully", "Failed to export data".

## Technical Requirements
-   **Security:** STRICTLY Admin only.
-   **CSV Generation:** Use Python's built-in `csv` module with `utf-8-sig` encoding (for Excel compatibility). Do not introduce `pandas` for this simple task to keep dependencies light unless performance requires it.
-   **Streaming:** Use `fastapi.responses.StreamingResponse` to avoid loading everything into memory if the dataset grows.
-   **File Naming:** `snapandsay_export_{YYYYMMDD}_{HHMM}.{csv|json}`.

## Design References
-   **Button Style:** Secondary or Outline variant to distinguish from primary actions.
-   **Placement:** Top right of the table, or next to "Filter" button.

## Agent Records
-   **Story Created By:** @sm-agent (Fabian)
-   **Date:** 2025-12-09

### One-Shot File List

#### [NEW] [user.py](file:///home/fabian/dev/work/snapandsay/backend/app/models/user.py)
#### [MODIFY] [log.py](file:///home/fabian/dev/work/snapandsay/backend/app/models/log.py)
#### [MODIFY] [log.py](file:///home/fabian/dev/work/snapandsay/backend/app/schemas/log.py)
#### [MODIFY] [export_service.py](file:///home/fabian/dev/work/snapandsay/backend/app/services/export_service.py)
#### [MODIFY] [admin.py](file:///home/fabian/dev/work/snapandsay/backend/app/api/v1/endpoints/admin.py)
#### [NEW] [test_admin_export.py](file:///home/fabian/dev/work/snapandsay/backend/tests/api/test_admin_export.py)
#### [MODIFY] [ExportDataButton.tsx](file:///home/fabian/dev/work/snapandsay/frontend/components/features/admin/ExportDataButton.tsx)
#### [MODIFY] [api.ts](file:///home/fabian/dev/work/snapandsay/frontend/lib/api.ts)

### Completion Notes

- [x] Implemented Backend Export Service with CSV/JSON support.
- [x] Defined User model and relationship for Diet logs to support Anonymous ID.
- [x] Added `meal_type` to schema and export.
- [x] Implemented Frontend Export Button with format selection.
- [x] Verified tests pass for CSV/JSON generation and headers.
- [x] **Code Review Applied (2025-12-09):**
    - Corrected "User Email" requirement to "Anonymous ID" to match database schema.
    - Updated `export_service.py` to use `joinedload` and accessible `anonymous_id`.
    - Added missing `meal_type` to `DietaryLogResponse`.
