---
title: 'Extend Dutch Support'
slug: 'extend-dutch-support'
created: '2026-01-21'
status: 'in-progress'
stepsCompleted: [1]
tech_stack: ['Next.js', 'Typescript', 'next-intl']
files_to_modify: [
  'frontend/app/(dashboard)/snap/page.tsx',
  'frontend/app/(dashboard)/log/[id]/page.tsx',
  'frontend/components/features/logs/DeleteLogDialog.tsx',
  'frontend/components/features/logs/EditLogSheet.tsx',
  'frontend/app/(dashboard)/admin/page.tsx',
  'frontend/messages/en.json',
  'frontend/messages/nl.json'
]
code_patterns: ['i18n', 'React Components']
test_patterns: ['Visual inspection', 'Parity script']
---

# Extend Dutch Support

## Overview

### Problem Statement
The user wants Dutch support on all pages, not just the dashboard. Currently, `SnapPage`, `LogDetailPage`, and shared components like `DeleteLogDialog` and `EditLogSheet` contain hardcoded English strings.

### Solution
We will systematically refactor these pages and components to use `next-intl` (`useTranslations`, `useLocale`) and move all hardcoded strings into the translation JSON files.

### Scope
**In Scope:**
- **Snap Page**: Localize prompts ("What's in this meal?", "Tap to toggle").
- **Log Detail Page**: Localize headers, nutrient labels, edit/delete buttons, date formatting.
- **Admin Page**: Localize fallback states.
- **Components**: Localize `DeleteLogDialog` and `EditLogSheet` (titles, labels, buttons, errors).
- **Translations**: Add matching keys to `en.json` and `nl.json`.

**Out of Scope:**
- Backend changes (already done).
- New pages/features.

## Context for Development

### Files to Reference

| Component | File | Status | Notes |
|Data| `frontend/messages/*.json` | **Needs Mod** | Add ~30 new keys. |
|UI| `frontend/app/(dashboard)/snap/page.tsx` | **Needs Mod** | 2-3 strings. |
|UI| `frontend/app/(dashboard)/log/[id]/page.tsx` | **Needs Mod** | Heavy refactor (no i18n yet). |
|UI| `frontend/components/features/logs/DeleteLogDialog.tsx` | **Needs Mod** | Hardcoded dialogs. |
|UI| `frontend/components/features/logs/EditLogSheet.tsx` | **Needs Mod** | Hardcoded form labels/placeholders. |
|UI| `frontend/app/(dashboard)/admin/page.tsx` | **Needs Mod** | Minor (fallback text). |

### Technical Decisions
- **Namespace Strategy**:
    - `snap`: Use existing namespace.
    - `logDetail`: Create new namespace for detailed view.
    - `logs.delete`, `logs.edit`: Use `logs` namespace for shared actions.
- **Date Formatting**: Enforce `useLocale` in `LogDetailPage`.

## Implementation Plan

### 1. Update Translations
- [ ] **Task 1: Add Keys to `en.json` and `nl.json`**
    - `snap.whatsInThisMeal`, `snap.tapToToggle`
    - `logDetail.title`, `logDetail.failed`, `logDetail.goBack`
    - `logs.delete.title`, `logs.delete.description`, `logs.delete.confirm`, `logs.delete.deleting`
    - `logs.edit.title`, `logs.edit.description`, `logs.edit.save`, `logs.edit.saving`
    - `logs.edit.labels`: title, description, calories, protein, carbs, fats
    - `logs.edit.placeholders`: title ("e.g. Roasted Cashews"), description ("Describe your meal...")
    - `admin.loadingDashboard`

### 2. Localize Snap Page
- [ ] **Task 2: Refactor `SnapPage.tsx`**
    - Replace hardcoded strings with `t('snap.whatsInThisMeal')` etc.

### 3. Localize Log Detail Page
- [ ] **Task 3: Refactor `LogDetailPage.tsx`**
    - Add `useTranslations('logDetail')`.
    - Add `useLocale` for `formatDateTime`.
    - Replace hardcoded strings.

### 4. Localize Shared Components
- [ ] **Task 4: Refactor `DeleteLogDialog.tsx`**
    - Use `useTranslations('logs.delete')` (or passing props, but hook is easier).
- [ ] **Task 5: Refactor `EditLogSheet.tsx`**
    - Use `useTranslations('logs.edit')`.

### 5. Localize Admin Page
- [ ] **Task 6: Refactor `AdminPage.tsx`**
    - Localize "Loading dashboard...".

### 6. Verification
- [ ] **Task 7: Verify Parity**
    - Run `scripts/verify_i18n.py`.
- [ ] **Task 8: Manual Check**
    - Navigate to Snap, Log Detail (click a log), Admin (if accessible). Toggle language.

## Acceptance Criteria
- [ ] **AC 1**: No English text remains on Snap, Log Detail, Edit/Delete modals when in Dutch.
- [ ] **AC 2**: Translation files remain in sync.
- [ ] **AC 3**: Date formats respect the locale.

## Testing Strategy
1.  **Automated**: `verify_i18n.py` for keys.
2.  **Manual**: Click through the flow.
