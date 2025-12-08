# Story 4.2: Edit & Delete Log

Status: ready-for-dev

## Story

As a user,
I want to edit or delete a logged meal entry,
So that I can correct mistakes and maintain accurate dietary records.

## Acceptance Criteria

1.  **Given** A logged meal exists on the dashboard
    **When** I tap on the `FoodEntryCard`
    **Then** I see a detail view with edit and delete options
    **And** The view shows the full meal photo, description, and nutritional breakdown

2.  **Given** I am viewing a meal's detail view
    **When** I tap the "Edit" button
    **Then** I can modify the description text
    **And** I can modify the calorie count, protein, carbs, and fats
    **And** Changes are validated before submission

3.  **Given** I have made changes in edit mode
    **When** I tap "Save"
    **Then** The entry is updated via `PUT /api/v1/logs/{id}`
    **And** The UI shows a success toast: "Meal updated"
    **And** The dashboard list refreshes with the updated data

4.  **Given** I am viewing a meal's detail view
    **When** I tap the "Delete" button
    **Then** I see a confirmation dialog: "Delete this meal?"
    **And** The dialog has "Cancel" and "Delete" buttons
    **And** The delete button is visually distinct (destructive styling)

5.  **Given** The delete confirmation dialog is shown
    **When** I tap "Delete"
    **Then** The entry is removed via `DELETE /api/v1/logs/{id}`
    **And** The UI shows a success toast: "Meal deleted"
    **And** I am navigated back to the dashboard
    **And** The deleted entry is no longer visible

6.  **Given** I am in edit mode or viewing detail view
    **When** I tap "Cancel" or navigate back
    **Then** No changes are saved
    **And** I return to the previous screen

7.  **Given** The backend API returns an error during edit or delete
    **When** The operation fails
    **Then** I see a user-friendly error message
    **And** The original data remains unchanged

## Tasks / Subtasks

- [ ] **Task 0: Install Required Shadcn Components** (AC: #2, #4, #3)
    - [ ] Run: `npx shadcn-ui@latest add sheet alert-dialog sonner`
    - [ ] Verify components added to `frontend/components/ui/`
    - [ ] Update `frontend/app/layout.tsx` to include `<Toaster />` from sonner

- [ ] **Task 1: Create Backend GET Single Log Endpoint** (AC: #1)
    - [ ] Add `get_log_by_id` service in `backend/app/services/log_service.py`:
        ```python
        async def get_log_by_id(db: AsyncSession, user_id: UUID, log_id: UUID) -> Optional[DietaryLog]:
            result = await db.execute(
                select(DietaryLog).where(DietaryLog.id == log_id, DietaryLog.user_id == user_id)
            )
            return result.scalar_one_or_none()
        ```
    - [ ] Add `GET /api/v1/logs/{log_id}` endpoint:
        ```python
        @router.get("/{log_id}", response_model=DietaryLogResponse)
        async def get_log(
            log_id: UUID,
            current_user: UserContext = Depends(get_current_user),
            db: AsyncSession = Depends(get_async_session),
        ) -> DietaryLogResponse:
            log = await log_service.get_log_by_id(db, current_user.id, log_id)
            if not log:
                raise HTTPException(status_code=404, detail="Log not found")
            return DietaryLogResponse.model_validate(log)
        ```
    - [ ] Add test: `test_get_log_by_id_success`, `test_get_log_by_id_not_found`

- [ ] **Task 2: Create Backend Update Endpoint** (AC: #2, #3, #7)
    - [ ] Create `DietaryLogUpdateRequest` schema in `backend/app/schemas/log.py`:
        ```python
        from pydantic import Field
        
        class DietaryLogUpdateRequest(BaseModel):
            description: Optional[str] = Field(None, max_length=500)
            calories: Optional[int] = Field(None, ge=0, le=5000)
            protein: Optional[int] = Field(None, ge=0, le=500)
            carbs: Optional[int] = Field(None, ge=0, le=500)
            fats: Optional[int] = Field(None, ge=0, le=500)
        ```
    - [ ] Create `update_log` service in `backend/app/services/log_service.py`:
        ```python
        async def update_log(db: AsyncSession, user_id: UUID, log_id: UUID, update_data: dict) -> Optional[DietaryLog]:
            result = await db.execute(
                select(DietaryLog).where(DietaryLog.id == log_id, DietaryLog.user_id == user_id)
            )
            log = result.scalar_one_or_none()
            if not log:
                return None
            for key, value in update_data.items():
                setattr(log, key, value)
            await db.commit()
            await db.refresh(log)
            return log
        ```
    - [ ] Add `PUT /api/v1/logs/{log_id}` endpoint:
        ```python
        @router.put("/{log_id}", response_model=DietaryLogResponse)
        async def update_log(
            log_id: UUID,
            update_data: DietaryLogUpdateRequest,
            current_user: UserContext = Depends(get_current_user),
            db: AsyncSession = Depends(get_async_session),
        ) -> DietaryLogResponse:
            updated = await log_service.update_log(db, current_user.id, log_id, update_data.model_dump(exclude_unset=True))
            if not updated:
                raise HTTPException(status_code=404, detail="Log not found")
            return DietaryLogResponse.model_validate(updated)
        ```

- [ ] **Task 3: Create Backend Delete Endpoint** (AC: #4, #5, #7)
    - [ ] Create `delete_log` service in `backend/app/services/log_service.py`:
        ```python
        async def delete_log(db: AsyncSession, user_id: UUID, log_id: UUID) -> bool:
            result = await db.execute(
                select(DietaryLog).where(DietaryLog.id == log_id, DietaryLog.user_id == user_id)
            )
            log = result.scalar_one_or_none()
            if not log:
                return False
            await db.delete(log)
            await db.commit()
            return True
        ```
    - [ ] Add `DELETE /api/v1/logs/{log_id}` endpoint:
        ```python
        @router.delete("/{log_id}", status_code=204)
        async def delete_log(
            log_id: UUID,
            current_user: UserContext = Depends(get_current_user),
            db: AsyncSession = Depends(get_async_session),
        ) -> None:
            deleted = await log_service.delete_log(db, current_user.id, log_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Log not found")
        ```

- [ ] **Task 4: Backend Tests** (AC: #3, #5, #7)
    - [ ] Add tests in `backend/tests/api/v1/test_logs.py`:
        - `test_get_log_by_id_success`
        - `test_get_log_by_id_not_found`
        - `test_update_log_success`
        - `test_update_log_partial_update`
        - `test_update_log_not_found`
        - `test_update_log_wrong_user`
        - `test_update_log_requires_authentication`
        - `test_update_log_validation_error` (calories > 5000)
        - `test_delete_log_success`
        - `test_delete_log_not_found`
        - `test_delete_log_wrong_user`
        - `test_delete_log_requires_authentication`

- [ ] **Task 5: Frontend API Client & Types** (AC: #3, #5)
    - [ ] Add `LogUpdateRequest` type to `frontend/types/log.ts`:
        ```typescript
        export interface LogUpdateRequest {
          description?: string;
          calories?: number;
          protein?: number;
          carbs?: number;
          fats?: number;
        }
        ```
    - [ ] Extend `frontend/lib/api.ts`:
        ```typescript
        export const logsApi = {
          // existing getByDate...
          
          getById: async (logId: string): Promise<DietaryLog> => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) throw new Error('No active session');
            const response = await fetch(`${API_BASE_URL}/api/v1/logs/${logId}`, {
              headers: { 'Authorization': `Bearer ${session.access_token}` },
            });
            if (!response.ok) throw new Error('Failed to fetch log');
            return response.json();
          },
          
          update: async (logId: string, data: LogUpdateRequest): Promise<DietaryLog> => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) throw new Error('No active session');
            const response = await fetch(`${API_BASE_URL}/api/v1/logs/${logId}`, {
              method: 'PUT',
              headers: {
                'Authorization': `Bearer ${session.access_token}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(data),
            });
            if (!response.ok) throw new Error('Failed to update log');
            return response.json();
          },
          
          delete: async (logId: string): Promise<void> => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) throw new Error('No active session');
            const response = await fetch(`${API_BASE_URL}/api/v1/logs/${logId}`, {
              method: 'DELETE',
              headers: { 'Authorization': `Bearer ${session.access_token}` },
            });
            if (!response.ok) throw new Error('Failed to delete log');
          },
        };
        ```

- [ ] **Task 6: Create Mutation Hooks** (AC: #3, #5, #7)
    - [ ] Add to `frontend/hooks/use-logs.ts`:
        ```typescript
        import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
        import { toast } from 'sonner';
        
        export function useLog(logId: string) {
          return useQuery({
            queryKey: ['log', logId],
            queryFn: () => logsApi.getById(logId),
          });
        }
        
        export function useUpdateLog() {
          const queryClient = useQueryClient();
          return useMutation({
            mutationFn: ({ logId, data }: { logId: string; data: LogUpdateRequest }) => 
              logsApi.update(logId, data),
            onMutate: async ({ logId, data }) => {
              await queryClient.cancelQueries({ queryKey: ['log', logId] });
              const previous = queryClient.getQueryData(['log', logId]);
              queryClient.setQueryData(['log', logId], (old: DietaryLog) => ({ ...old, ...data }));
              return { previous };
            },
            onError: (err, variables, context) => {
              queryClient.setQueryData(['log', variables.logId], context?.previous);
              toast.error('Failed to update meal');
            },
            onSuccess: () => {
              toast.success('Meal updated');
            },
            onSettled: (data, error, { logId }) => {
              queryClient.invalidateQueries({ queryKey: ['log', logId] });
              queryClient.invalidateQueries({ queryKey: ['logs'] });
            },
          });
        }
        
        export function useDeleteLog() {
          const queryClient = useQueryClient();
          return useMutation({
            mutationFn: (logId: string) => logsApi.delete(logId),
            onSuccess: () => {
              toast.success('Meal deleted');
              queryClient.invalidateQueries({ queryKey: ['logs'] });
            },
            onError: () => {
              toast.error('Failed to delete meal');
            },
          });
        }
        ```

- [ ] **Task 7: Create Log Detail Page** (AC: #1, #6)
    - [ ] Create `frontend/app/(dashboard)/log/[id]/page.tsx`:
        - Use `useLog(params.id)` to fetch data
        - Display full-size image (aspect-ratio-[4/3])
        - Show description, calories, protein, carbs, fats
        - Back button in header: `<Button variant="ghost" onClick={() => router.back()}>`
        - Fixed bottom bar with Edit and Delete buttons (h-16, gap-4)

- [ ] **Task 8: Create Edit Sheet** (AC: #2, #3, #6)
    - [ ] Create `frontend/components/features/logs/EditLogSheet.tsx`:
        ```typescript
        // Uses Shadcn Sheet (bottom drawer on mobile)
        // Form with validation:
        // - description: Textarea, maxLength=500
        // - calories: Input type="number", min=0, max=5000
        // - protein/carbs/fats: Input type="number", min=0, max=500
        // All inputs: className="h-14 text-lg" (senior-friendly)
        // Save button: disabled={!isDirty || isPending}
        ```
    - [ ] Use `useUpdateLog` mutation hook

- [ ] **Task 9: Create Delete Dialog** (AC: #4, #5)
    - [ ] Create `frontend/components/features/logs/DeleteLogDialog.tsx`:
        ```typescript
        import { AlertDialog, AlertDialogAction, AlertDialogCancel, ... } from '@/components/ui/alert-dialog';
        
        // Title: "Delete this meal?"
        // Description: "This action cannot be undone."
        // Cancel: variant="outline", className="h-14"
        // Delete: variant="destructive", className="h-14"
        // On confirm: call deleteLog mutation, then router.push('/')
        ```

- [ ] **Task 10: Connect FoodEntryCard Navigation** (AC: #1)
    - [ ] Update `FoodEntryCard` to use `useRouter`:
        ```typescript
        const router = useRouter();
        // onClick={() => router.push(`/log/${log.id}`)}
        ```

- [ ] **Task 11: Frontend Component Tests** (AC: All)
    - [ ] `EditLogSheet.test.tsx`: Form rendering, validation errors, submit
    - [ ] `DeleteLogDialog.test.tsx`: Confirm/cancel flow
    - [ ] `LogDetailPage.test.tsx`: Data display, action buttons

## Dev Notes

### Validation Rules

| Field       | Type     | Min | Max  | Required |
|-------------|----------|-----|------|----------|
| description | string   | -   | 500  | No       |
| calories    | integer  | 0   | 5000 | No       |
| protein     | integer  | 0   | 500  | No       |
| carbs       | integer  | 0   | 500  | No       |
| fats        | integer  | 0   | 500  | No       |

### Senior-Friendly UX Requirements

- **Form Inputs**: `h-14` (56px) height, `text-lg` (18px) font
- **Buttons**: `h-14` minimum, full-width on mobile
- **Touch Targets**: 60px+ for all interactive elements
- **Contrast**: AAA (7:1) ratio
- **Labels**: Always visible, never icon-only
- **Toast Duration**: 6 seconds (accessibility)
- **Confirmation**: Required for destructive actions

### Anti-Patterns to Avoid

- **DO NOT** allow editing `image_path`, `audio_path`, or `status`
- **DO NOT** skip ownership verification (security critical)
- **DO NOT** use small text - minimum 18px
- **DO NOT** forget to invalidate React Query cache
- **DO NOT** use generic error messages

### Previous Story Intelligence (Story 4.1)

- `FoodEntryCard` already accepts `onClick` prop
- `useLogs` hook established - extend with mutations
- `DietaryLogResponse` schema exists - add update request
- Backend test patterns in `test_logs.py`
- QueryProvider already in layout

### Security Considerations

- **Ownership Verification**: Always verify `user_id == current_user.id`
- **UUID Validation**: FastAPI auto-validates UUID path params
- **Partial Updates**: Use `model_dump(exclude_unset=True)`

### References

- [Architecture: API Patterns](file:///home/fabian/dev/work/snapandsay/docs/architecture.md#api--communication-patterns)
- [UX Spec: Form Patterns](file:///home/fabian/dev/work/snapandsay/docs/ux-design-specification.md#form-patterns)
- [PRD: FR14, FR15](file:///home/fabian/dev/work/snapandsay/docs/prd.md#4-dietary-log-management)

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/4-1-daily-log-list-ui.md` (previous story patterns)
- `backend/app/api/v1/endpoints/logs.py`, `backend/app/services/log_service.py`
- `backend/app/schemas/log.py`, `backend/app/models/log.py`
- `frontend/lib/api.ts`, `frontend/hooks/use-logs.ts`
- `frontend/components/features/logs/FoodEntryCard.tsx`

### Agent Model Used

{{agent_model_name_version}}

### Completion Notes List

### File List

**Backend (Modified):**
- backend/app/api/v1/endpoints/logs.py
- backend/app/services/log_service.py
- backend/app/schemas/log.py
- backend/tests/api/v1/test_logs.py

**Frontend (New):**
- frontend/components/ui/sheet.tsx (via shadcn)
- frontend/components/ui/alert-dialog.tsx (via shadcn)
- frontend/components/ui/sonner.tsx (via shadcn)
- frontend/app/(dashboard)/log/[id]/page.tsx
- frontend/components/features/logs/EditLogSheet.tsx
- frontend/components/features/logs/DeleteLogDialog.tsx
- frontend/__tests__/components/EditLogSheet.test.tsx
- frontend/__tests__/components/DeleteLogDialog.test.tsx
- frontend/__tests__/app/LogDetailPage.test.tsx

**Frontend (Modified):**
- frontend/lib/api.ts
- frontend/types/log.ts
- frontend/hooks/use-logs.ts
- frontend/components/features/logs/FoodEntryCard.tsx
- frontend/app/layout.tsx (add Toaster)
