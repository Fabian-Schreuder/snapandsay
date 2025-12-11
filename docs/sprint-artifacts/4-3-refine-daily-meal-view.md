# Story 4.3: Refine Daily Meal View (Meal Slots)

Status: backlog

## Story

As **Martha** (a casual senior user),
I want to see my daily logs organized by **Meals (Breakfast, Lunch, Dinner)** rather than a simple list,
So that I can easily see if I've missed a meal and add it directly.

## Acceptance Criteria

1.  **Given** I am on the Dashboard
    **When** I view the daily list
    **Then** I see three distinct sections/slots: **Breakfast**, **Lunch**, **Dinner** (and optional "Snacks")
    **And** My existing logs are sorted into these slots based on their `meal_type`

2.  **Given** A meal slot is empty (e.g., I haven't had Lunch)
    **When** I view the Lunch slot
    **Then** I see a clear, large "Log Lunch" button (Ghost Card style)
    **And** It is visually distinct from filled cards

3.  **Given** I tap the "Log Lunch" button
    **When** I am taken to the Snap page
    **Then** The app remembers I am logging "Lunch"
    **And** The eventual log is properly categorized as "Lunch" (bypassing time-based inference if needed)

4.  **Given** I logged a meal but it's in the wrong slot (e.g., Breakfast shows up in Lunch)
    **When** I edit the log
    **Then** I can change the `meal_type` to the correct meal
    **And** The card moves to the correct slot immediately

5.  **Given** I have multiple items for one meal
    **When** I view the slot
    **Then** Both items appear in that slot (e.g., "Coffee" and "Toast" both under Breakfast)

## Tasks / Subtasks

- [ ] **Task 1: Update API & Schema for Meal Type Context**
    - [ ] Update `backend/app/schemas/analysis.py`:
        - Add `meal_type: Optional[str] = None` to `AnalysisUploadRequest`.
    - [ ] Update `backend/app/api/v1/endpoints/analysis.py`:
        - In `upload_analysis_data`, accept `meal_type` from request.
        - Persist it to `DietaryLog.meal_type` immediately upon creation.

- [ ] **Task 2: Refactor Dashboard UI to Slot Layout**
    - [ ] Create `frontend/components/features/logs/MealSlot.tsx`:
        - Props: `title` (e.g., "Breakfast"), `logs: DietaryLog[]`, `onAdd: () => void`.
        - Renders list of `FoodEntryCard` or `EmptySlotPlaceholder`.
    - [ ] Create `frontend/components/features/logs/EmptySlotPlaceholder.tsx`:
        - Large dashed border, "Plus" icon, "Log [Meal]" text.
        - High contrast, accessible touch target.
    - [ ] Update `frontend/app/(dashboard)/page.tsx`:
        - Group `data.data` by `meal_type` (Breakfast, Lunch, Dinner, Snack).
        - Render 4 `MealSlot` sections.

- [ ] **Task 3: Implement "Context-Aware" Snap**
    - [ ] Update `frontend/components/features/logs/EmptySlotPlaceholder`:
        - `onAdd` should navigate to `/snap?type=[meal_type]`.
    - [ ] Update `frontend/app/(dashboard)/snap/page.tsx`:
        - Read `type` from searchParams.
        - Pass `mealType` to `useAgent` hook or directly to upload API.
    - [ ] Update `frontend/lib/api.ts` `uploadAnalysisData`:
        - Accept `mealType` and include in JSON body.

- [ ] **Task 4: "Rectify" (Edit Meal Type)**
    - [ ] Update `backend/app/schemas/log.py`:
        - Ensure `DietaryLogUpdate` allows `meal_type`.
    - [ ] Update `frontend/components/features/logs/LogEditDialog.tsx` (or equivalent):
        - Add `Select` or `RadioGroup` for Meal Type.
        - Update mutation to send `meal_type` change.

- [ ] **Task 5: CSS/Styling Refinement (Martha Persona)**
    - [ ] Ensure "Slots" look like a daily schedule/routine.
    - [ ] Use `daily-summary` component from Story 4.1 but perhaps integrated better.

## Technical Notes

- **Sorting Logic**:
    - Backend returns list. Frontend does the grouping (simplest for MVP).
    - `const meals = { breakfast: [], lunch: [], dinner: [], snack: [] }`.
    - Iterate logs and push to arrays.
    - Time fallback: If `meal_type` is null, infer from `created_at` (e.g., < 11am = Breakfast) OR just put in "Uncategorized/Snacks".
- **Context Passing**:
    - Simplest way to pass context to agent: Append to the "User Note" implicitly?
    - Or better: Add `meal_type` to the metadata sent to `analyze_input`.
- **Icons**: Use Lucide icons for each meal (Sunrise, Sun, Moon/Sunset).

## Verification

- [ ] **Manual**:
    - Click "Log Breakfast" -> Snap -> Verify it appears in Breakfast slot.
    - Log a generic item -> Edit -> Move to Dinner -> Verify it jumps slots.
- [ ] **Automated**:
    - `test_dashboard_grouping`: Mock logs with different types, assert they appear in correct sections.
