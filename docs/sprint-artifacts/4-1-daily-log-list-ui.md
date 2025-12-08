# Story 4.1: Daily Log List UI

Status: ready-for-dev

## Story

As a user,
I want to see a list of my meals for today,
So that I can keep track of my eating and review what I've logged.

## Acceptance Criteria

1.  **Given** I am logged in and have logged meals today
    **When** I view the dashboard
    **Then** I see a list of `FoodEntryCard` components for today's logs
    **And** Cards are sorted by `created_at` descending (newest first)

2.  **Given** A logged meal exists
    **When** I view the `FoodEntryCard`
    **Then** I see the meal photo thumbnail (from `image_path`)
    **And** I see the meal description (or transcript if no description)
    **And** I see the calorie count as a badge
    **And** I see the timestamp in human-readable format (e.g., "12:30 PM")

3.  **Given** I am on the dashboard
    **When** No meals have been logged today
    **Then** I see an empty state with friendly message: "No meals logged yet today"
    **And** A call-to-action button linking to the capture screen

4.  **Given** The meals are loading
    **When** I view the dashboard
    **Then** I see skeleton loading states for the cards
    **And** The loading state shows 3 placeholder cards

5.  **Given** A meal has `needs_review: true`
    **When** I view the `FoodEntryCard`
    **Then** I see a visual indicator (subtle badge/icon) that the entry needs review

6.  **Given** The backend API returns an error
    **When** I view the dashboard
    **Then** I see a user-friendly error message
    **And** A "Retry" button to refresh the data

7.  **Given** I am on the dashboard
    **When** A new meal is logged (e.g., from snap page)
    **Then** The list updates automatically via React Query invalidation

## Tasks / Subtasks

- [ ] **Task 1: Create Logs Service & API Endpoint** (AC: #1, #2)
    - [ ] Create `backend/app/services/log_service.py`:
        - `get_logs_for_date(db, user_id, date) -> List[DietaryLog]` - Filter by date (UTC), status="logged", order DESC
    - [ ] Create `backend/app/api/v1/endpoints/logs.py`:
        ```python
        @router.get("/logs")
        async def get_logs(
            date: Optional[str] = None,  # ISO format, defaults to today
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db)
        ) -> DietaryLogListResponse:
        ```
    - [ ] Create `backend/app/schemas/log.py`:
        - `DietaryLogResponse`: id, image_path, transcript, description, calories, protein, carbs, fats, needs_review, created_at
        - `DietaryLogListResponse`: data (list), meta (total count)
    - [ ] Register router: `api_router.include_router(logs.router, prefix="/logs", tags=["logs"])`
    - [ ] Tests in `backend/tests/api/test_logs.py`:
        - `test_get_logs_returns_empty_list_when_none_exist`
        - `test_get_logs_filters_by_date_correctly`
        - `test_get_logs_requires_authentication` (401 without token)
        - `test_get_logs_only_returns_logged_status` (excludes processing/clarification)
        - `test_get_logs_handles_timezone_correctly` (UTC boundaries)

- [ ] **Task 2: Create Frontend API Client** (AC: #1, #6)
    - [ ] Extend `frontend/lib/api.ts` matching existing pattern:
        ```typescript
        export const logsApi = {
          getByDate: async (date?: string) => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) throw new Error('No active session');
            const url = date ? `${API_BASE_URL}/api/v1/logs?date=${date}` : `${API_BASE_URL}/api/v1/logs`;
            const response = await fetch(url, { headers: { 'Authorization': `Bearer ${session.access_token}` } });
            if (!response.ok) throw new Error('Failed to fetch logs');
            return response.json();
          }
        };
        ```
    - [ ] Create `frontend/types/log.ts` with `DietaryLog` interface
    - [ ] Create `frontend/hooks/use-logs.ts`:
        ```typescript
        export function useLogs(date?: string) {
          return useQuery({ queryKey: ['logs', date ?? 'today'], queryFn: () => logsApi.getByDate(date), staleTime: 30000 });
        }
        ```

- [ ] **Task 3: Create FoodEntryCard Component** (AC: #2, #5)
    - [ ] Create `frontend/components/features/logs/FoodEntryCard.tsx`:
        - Props: `log: DietaryLog`, `onClick?: () => void`
        - Layout: 80x80 thumbnail | description + time | calories badge
        - Senior-friendly: min-h-[100px], text-lg (18px+), rounded-xl, shadow-sm
        - Needs review: Show subtle AlertTriangle icon if `needs_review=true`
    - [ ] Create `frontend/components/features/logs/FoodEntryCardSkeleton.tsx`:
        - Use existing `frontend/components/ui/skeleton.tsx` (Shadcn Skeleton)
        - Match FoodEntryCard layout

- [ ] **Task 4: Create Dashboard Page** (AC: #1, #3, #4, #6)
    - [ ] Create `frontend/app/(dashboard)/page.tsx`:
        - Uses `useLogs()` hook
        - Loading: Render 3x `FoodEntryCardSkeleton`
        - Empty: Render `EmptyLogState`
        - Error: Render `LogListError` with `refetch` callback
        - Success: Map logs to `FoodEntryCard` list
    - [ ] Create `frontend/components/features/logs/EmptyLogState.tsx`:
        - Friendly message, utensils icon, large "Log a Meal" button → `/snap`
    - [ ] Create `frontend/components/features/logs/LogListError.tsx`:
        - Error message + "Retry" button calling `refetch()`

- [ ] **Task 5: Create Daily Summary Header** (AC: #2)
    - [ ] Create `frontend/components/features/logs/DailySummary.tsx`:
        - Today's date (e.g., "Sunday, December 8")
        - Total calories: `logs.reduce((sum, log) => sum + (log.calories || 0), 0)`
        - Typography: text-2xl heading

- [ ] **Task 6: Integrate with Navigation** (AC: #7)
    - [ ] Bottom navigation "Home" tab → dashboard
    - [ ] Invalidate `['logs']` query key after successful log on snap page

- [ ] **Task 7: Testing**
    - [ ] Backend: 5 test cases specified in Task 1
    - [ ] Frontend: `FoodEntryCard.test.tsx`, `EmptyLogState.test.tsx`

## Dev Notes

### Backend Endpoint Pattern

Use existing authentication pattern from `analysis.py`:

```python
from app.core.security import get_current_user
from app.db.session import get_db

@router.get("/logs")
async def get_logs(
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),  # JWT validation
    db: AsyncSession = Depends(get_db)
):
    # Parse date (default: today in UTC)
    # Call service: log_service.get_logs_for_date(db, current_user.id, parsed_date)
    # Return DietaryLogListResponse
```

### Service Layer Pattern

Create `backend/app/services/log_service.py` for business logic:

```python
async def get_logs_for_date(db: AsyncSession, user_id: UUID, date: datetime.date) -> List[DietaryLog]:
    # All dates stored/queried in UTC
    start = datetime.combine(date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(date, time.max, tzinfo=timezone.utc)
    return await db.execute(
        select(DietaryLog)
        .where(DietaryLog.user_id == user_id, DietaryLog.status == "logged",
               DietaryLog.created_at >= start, DietaryLog.created_at <= end)
        .order_by(DietaryLog.created_at.desc())
    )
```

### Timezone Handling

- **Backend**: All `created_at` timestamps are UTC. Date filter boundaries computed in UTC.
- **Frontend**: Convert `created_at` to local time for display using `toLocaleTimeString()`.

### FoodEntryCard Layout

```
┌─────────────────────────────────────────┐
│ ┌──────┐  Chicken Salad with Ranch    │
│ │ IMG  │  12:30 PM                     │
│ │80x80 │                    [320 cal]  │
│ └──────┘        [⚠️ if needs_review]   │
└─────────────────────────────────────────┘
```

Card: min-h-[100px], p-4, rounded-xl, shadow-sm

### Image URL Generation

```typescript
const getImageUrl = (path: string) => 
  `${process.env.NEXT_PUBLIC_SUPABASE_URL}/storage/v1/object/public/${path}`;
```

### Existing Components to Reuse

- `frontend/components/ui/skeleton.tsx` - Shadcn Skeleton for loading states
- `frontend/components/ui/button.tsx` - Shadcn Button for CTAs
- `frontend/components/ui/card.tsx` - Shadcn Card if available

### Anti-Patterns to Avoid

- **DO NOT** load all historical logs - filter by date
- **DO NOT** use small text - minimum 18px for body text
- **DO NOT** show processing/clarification status logs - only `status="logged"`
- **DO NOT** hardcode Supabase URL - use environment variables
- **DO NOT** put DB queries in endpoint - use service layer

### Previous Story Intelligence (Story 3.4)

- `DietaryLog` model: id, user_id, image_path, transcript, description, calories, protein, carbs, fats, status, needs_review, created_at
- Logs created via `/api/v1/analysis/upload` → status transitions: processing → clarification → logged
- React Query patterns established for server state

### References

- [Architecture: API Patterns](file:///home/fabian/dev/work/snapandsay/docs/architecture.md#api--communication-patterns)
- [UX Spec: FoodEntryCard](file:///home/fabian/dev/work/snapandsay/docs/ux-design-specification.md#2-foodentrycard)
- [PRD: FR13](file:///home/fabian/dev/work/snapandsay/docs/prd.md#4-dietary-log-management)

## Dev Agent Record

### Context Reference

- `docs/epics.md`, `docs/architecture.md`, `docs/prd.md`, `docs/ux-design-specification.md`
- `backend/app/models/log.py`, `backend/app/api/v1/endpoints/analysis.py`
- `frontend/lib/api.ts`, `frontend/components/ui/skeleton.tsx`

### Agent Model Used

{{agent_model_name_version}}

### Completion Notes List

### File List
