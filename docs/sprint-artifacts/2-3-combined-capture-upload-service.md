# Story 2.3: Combined Capture & Upload Service

Status: done

## Story

As a user,
I want my photo and voice note to be uploaded securely,
So that the AI can analyze them.

## Acceptance Criteria

1.  **Given** I have completed the capture flow (Photo taken + Voice recorded + "Done" triggered)
    **When** The upload process begins
    **Then** The photo is uploaded to Supabase Storage bucket `raw_uploads` path `{user_id}/{timestamp}_image.jpg`
    **And** The audio is uploaded to Supabase Storage bucket `raw_uploads` path `{user_id}/{timestamp}_audio.webm`

2.  **Given** Files are successfully uploaded to Storage
    **When** The frontend notifies the backend
    **Then** The frontend sends a `POST` request to `/api/v1/analysis/upload` with the storage paths and metadata
    **And** A new record is created in the `dietary_logs` database table with status `processing`

3.  **Given** The upload sequence is initiated
    **When** The network is slow or processing
    **Then** The UI displays a "Thinking" state (e.g., pulsing animation or "Analyzing..." text)
    **And** The UI does NOT allow re-submitting until complete or failed

4.  **Given** An upload failure occurs (Storage or API)
    **When** The error is caught
    **Then** The user is notified with a senior-friendly error message ("We couldn't save that. Please try again.")
    **And** The "Retry" option is available

5.  **Given** The backend receives the upload request
    **When** The `dietary_logs` entry is created
    **Then** The endpoint returns a success response containing the new `log_id`

## Tasks / Subtasks

- [x] Database: Schema & Migrations
    - [x] Create `backend/app/models/log.py` defining the `DietaryLog` model (SQLAlchemy).
        - Fields: `id` (UUID), `user_id` (FK), `image_path` (str), `audio_path` (str, nullable), `transcript` (str, nullable), `description` (str, nullable), `calories` (int, nullable), `protein`/`carbs`/`fats` (int, nullable), `status` (enum: processing, clarification, logged), `client_timestamp` (datetime), `created_at` (with `server_default=func.now()`).
    - [x] Create `supabase/migrations/YYYYMMDDHHMMSS_create_dietary_logs.sql`.
        - Define table `dietary_logs`.
        - Enable RLS (Users can select/insert/update/delete their own rows).
        - **CRITICAL**: Create RLS policies for `storage.objects` to allow authenticated users to INSERT into `raw_uploads/{user_id}/*` and SELECT their own files.
        - Create index on `user_id` and `created_at`.
    - [x] Run migration to apply changes.

- [x] Backend: API & Service
    - [x] Create `backend/app/schemas/analysis.py` (Pydantic).
        - `AnalysisUploadRequest`: `image_path`, `audio_path` (optional), `client_timestamp`.
        - `AnalysisUploadResponse`: `log_id`, `status`.
    - [x] Create `backend/app/api/v1/endpoints/analysis.py`.
        - Implement `POST /upload` endpoint.
        - Validate file paths exist (optional, or trust client for MVP).
        - Create DB entry with `status="processing"`.
        - Return `AnalysisUploadResponse`.
    - [x] Register router in `backend/app/api/v1/api.py`.

- [x] Frontend: Service Layer
    - [x] Update `frontend/lib/supabase.ts` (verify storage client access).
        - Ensure `raw_uploads` bucket exists in Supabase (or create via migration/dashboard script if possible, primarily manual or via seed). **Action**: Check if bucket creation via SQL matches Supabase pattern, usually requires storage extension. *Dev note: Assume bucket needs to be created or use SQL to insert into `storage.buckets`.*
    - [x] Create `frontend/services/upload-service.ts`.
        - `uploadFile(bucket, path, file)`: Wrapper for Supabase storage upload.
        - Handle unique filename generation.

- [x] Frontend: Integration & UI
    - [x] Update `frontend/lib/api.ts` to include `analysis.upload(...)` method (fetch wrapper).
    - [x] Modify `frontend/app/(dashboard)/snap/page.tsx`.
        - Implement `handleUpload` function triggered after Voice capture (or "Done" button).
        - Execute `upload-service` calls in parallel for Image + Audio.
        - **Robustness**: Implement cleanup logic if one upload fails (attempt to delete the successful one to avoid orphans) or ensure atomic handling.
        - On success of BOTH, call Backend API.
        - Manage `isUploading` state to show "Thinking" UI (overlay or button state).
        - Handle errors with Toast/Alert.

## Dev Notes

- **Supabase Storage**: If the `raw_uploads` bucket doesn't exist, you might need to create it manually in the dashboard or via an SQL migration inserting into `storage.buckets` and `storage.objects` policies. For this story, providing the SQL to create the bucket and policies is best practice.
- **RLS Policies**: Crucial for `dietary_logs`. Ensure `auth.uid() = user_id`.
- **UX**: The "Thinking" state here is the bridge to the next story (Agentic Analysis). For now, just show the state; the actual streaming updates will come in Story 3.3.
- **Error Handling**: Network flakiness is common on mobile. Ensure uploads are robust (maybe retry logic in service).

### Project Structure Notes

- **Model Location**: `backend/app/models/` for SQL tables.
- **Schema Location**: `backend/app/schemas/` for Pydantic API constraints.
- **Frontend Service**: Keep upload logic out of the UI component; use a dedicated service function in `frontend/services/`.

### References

- [Epics: Story 2.3](docs/epics.md#story-23-combined-capture-upload-service)
- [Architecture: Data Boundaries](docs/architecture.md#data-boundaries)
- [Architecture: Naming Patterns](docs/architecture.md#naming-patterns) ("dietary_logs", snake_case)

## Dev Agent Record

### Context Reference

- `docs/epics.md`
- `docs/architecture.md`
- `docs/sprint-artifacts/2-2-voice-recorder-component.md`

### Agent Model Used

- **Model**: Gemini 2.0 Flash (Antigravity)
- **Role**: Technical Scrum Master (Bob)

### Completion Notes List

- Database migration created for `dietary_logs` and `storage.buckets`.
- `DietaryLog` model implemented. `models.py` refactored to package.
- `AnalysisUploadRequest` schema implemented. `schemas.py` refactored to package.
- `POST /api/v1/analysis/upload` endpoint implemented.
- `upload-service` created in frontend for storage uploads.
- `SnapPage` updated to handle upload flow (Image + Audio -> Storage -> API) with loading and error states.
- Unit tests created for API endpoint (`backend/tests/api/v1/test_analysis.py`).
- Integration tests created for frontend flow (`frontend/__tests__/SnapPageUpload.test.tsx`).

### File List

- backend/app/models/log.py
- backend/app/models/__init__.py
- backend/app/schemas/analysis.py
- backend/app/schemas/__init__.py
- backend/app/api/v1/endpoints/analysis.py
- backend/app/api/v1/api.py
- supabase/migrations/20251206000000_create_dietary_logs.sql
- frontend/services/upload-service.ts
- frontend/lib/api.ts
- frontend/app/(dashboard)/snap/page.tsx
- frontend/__tests__/SnapPageUpload.test.tsx

