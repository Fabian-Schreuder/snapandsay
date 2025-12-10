# Test Design: Epic 4 (Dietary Log Management)

**Epic**: 4
**Scope**: Epic-Level Mode
**Status**: DRAFT

---

## 1. Risk Assessment

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **R-4-1** | DATA | Accidental deletion of meal logs | 2 (Possible) | 2 (Degraded) | **4** | **UI**: Confirmation dialog required before delete action. |
| **R-4-2** | TECH | Stale data in UI after edit/delete (Cache) | 3 (Likely) | 2 (Degraded) | **6 (High)**| **Code**: Ensure React Query `invalidateQueries` is called on mutation success. **Test**: Verify list updates immediately without reload. |
| **R-4-3** | BUS | Users cannot view history (Network/API fail) | 1 (Unlikely) | 3 (Critical) | **3** | **UI**: Error boundary and retry mechanism. |
| **R-4-4** | TECH | Edit form payload payload validation failure | 2 (Possible) | 1 (Minor) | **2** | **Backend**: Pydantic validation. **Frontend**: Form validation schema. |

**High-Priority Risks (Score ≥ 6):**
- **R-4-2**: Cache invalidation is critical for UX. If this fails, user sees deleted items or old data.

---

## 2. Test Coverage Plan

We will focus on **End-to-End (E2E)** tests to verify the integration of Frontend Components (Cards, Sheets, Dialogs) with the Backend API mocks.

### E2E Scenarios (Playwright)

**File**: `tests/e2e/e4-logs.spec.ts` (To be created)

#### Scenario 4.1: View Daily Log List (P0)
- **Objective**: Verify users can see their logged meals.
- **Pre-conditions**: Mocked API returns list of logs.
- **Actions**: Navigate to Dashboard.
- **Assertions**:
    - `FoodEntryCard` elements appear.
    - Data (Title, Calories) matches mock.
    - Empty state displayed if no logs.

#### Scenario 4.2: Delete Meal Log (P1)
- **Objective**: Verify secure deletion with confirmation.
- **Pre-conditions**: Setup 1 log entry.
- **Actions**:
    - Click "Delete" button.
    - **Verify**: Confirmation dialog appears (Mitigates R-4-1).
    - Click "Confirm".
- **Assertions**:
    - API `DELETE` called.
    - Log disappears from list (Verify R-4-2).
    - Toast success message appears.

#### Scenario 4.3: Edit Meal Log (P1)
- **Objective**: Verify editing details.
- **Pre-conditions**: Setup 1 log entry.
- **Actions**:
    - Click "Edit" item (opens Sheet).
    - Change Food Item name and Calories.
    - Click "Save".
- **Assertions**:
    - API `PUT` called with new data.
    - List update reflects changes (Verify R-4-2).

---

## 3. Execution Strategy

1.  **Mocking Strategy**:
    - Mock `GET /api/v1/logs?date=...` for stable list data.
    - Mock `DELETE` and `PUT` responses to simulate success.
2.  **Helpers**:
    - Reuse `tests/support/auth.ts` for login state.
3.  **Browsers**:
    - Chromium (Primary).
    - Webkit/Firefox (Sanity check for dialogs/sheets).

## 4. Quality Gate Criteria

- All P0/P1 scenarios pass.
- **R-4-2 Verified**: Explicit check for UI update after mutation.
