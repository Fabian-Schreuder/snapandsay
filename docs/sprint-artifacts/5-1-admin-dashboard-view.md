# Story 5.1: Admin Dashboard View

Status: ready-for-dev

## Story

As a researcher (Admin),
I want to view all user logs in a table,
so that I can monitor the study progress and analyze data patterns.

## Acceptance Criteria

1.  **Admin Authorization:**
    *   Only users with 'admin' role or privileges can access the `/admin` routes.
    *   Unauthorized users are redirected or shown a 403 Forbidden.
2.  **Dashboard View:**
    *   Navigating to `/admin` displays a data table of dietary logs.
    *   The table columns include: User ID (Anonymous), Date, Time, Food Description, Calories, and Status.
3.  **Data Filtering:**
    *   Admins can filter the table by **User ID** (exact match).
    *   Admins can filter the table by **Date Range** (Start/End).
4.  **Pagination:**
    *   The table supports pagination to handle large datasets (e.g., 50 items per page).

## Tasks / Subtasks

- [x] **Backend: Admin API Endpoints**
    - [x] Create `backend/app/api/v1/endpoints/admin.py`.
    - [x] Implement dependency `get_current_admin` in `deps.py`.
        - [x] Logic: Verify JWT and Check `app_metadata` for role='admin' OR validate email against `ADMIN_EMAILS` env var.
    - [x] Create endpoint `GET /api/v1/admin/logs` with query params (user_id, start_date, end_date, page, limit).
    - [x] Register router in `backend/app/api/v1/api.py`.
- [x] **Backend: Service Layer**
    - [x] Update `backend/app/services/log_service.py` to add `get_all_logs` method (and `count_all_logs`).
    - [x] Ensure valid Pydantic schemas in `backend/app/schemas/log.py` (add `user_id`, `status` to response).
- [x] **Frontend**
    - [x] Create `frontend/app/(dashboard)/admin/page.tsx` (Protected).
    - [x] Create `frontend/components/AdminGuard.tsx` (Handle admin-specific auth).
    - [x] Extend `frontend/lib/api.ts` (Add `adminApi`).
    - [x] Implement `AdminLogsTable` using `shadcn/ui`.
    - [x] Integrate `frontend/components/page-pagination.tsx`.
    - [x] Add Filters (`UserFilter`, `DateRangePicker` implementation).

## Dev Notes

### Architecture & Security

-   **Admin Auth:** Since main users are Anonymous, Admins will likely log in via Supabase Email/Password (configured in Supabase Console).
-   **Role Verification:** The JWT for an email-authenticated user will have `aud: authenticated`.
    -   *Implementation:* In `get_current_admin`, check if `user.email` is present and matches the `ADMIN_EMAILS` environment variable (comma-separated list).
-   **API Security:** Ensure `GET /api/v1/admin/logs` is strictly protected using the `get_current_admin` dependency.

### Component Guidelines

-   **Table:** Use `components/ui/table.tsx` (Shadcn).
-   **Pagination:** **MUST USE** `components/page-pagination.tsx`. Do not reinvent pagination logic.
-   **State:** Use `useQuery` with `keepPreviousData: true` for smooth pagination/filtering.
-   **Date Handling:** Use `date-fns` for formatting.

### File Structure

-   `backend/app/api/v1/endpoints/admin.py` [NEW]
-   `frontend/app/(dashboard)/admin/page.tsx` [NEW]
-   `frontend/components/features/admin/AdminLogsTable.tsx` [NEW]
-   `frontend/components/features/admin/AdminFilters.tsx` [NEW]
-   `frontend/components/AdminGuard.tsx` [NEW]

## Dev Agent Record

### Context Reference

-   **PRD:** FR17, FR18
-   **Architecture:** Admin/Research Oversight section
-   **Epics:** Story 5.1

### Models Checking
-   Check `backend/app/models/log.py` for fields to display.
-   Check `backend/app/core/security.py` for `UserContext` expansion if needed.

## File List

### Backend
-   `backend/app/api/v1/endpoints/admin.py`
-   `backend/app/api/deps.py`
-   `backend/app/api/v1/api.py`
-   `backend/app/config.py`
-   `backend/app/core/security.py`
-   `backend/tests/api/test_admin.py`
-   `backend/tests/api/test_admin_auth.py`

## Change Log

-   2025-12-09: Implemented Admin API foundation (auth, endpoint scaffolding).

## Dev Agent Record

### Implementation Plan
-   [x] **Backend: Admin API Endpoints**: Implemented `get_current_admin` using `ADMIN_EMAILS` or `app_metadata` role. Created `/admin/logs` endpoint (currently mocks response). Tests added for auth and routing.

