# Project: Kariyer Ajanı Revamp & Fixes

## Overview
The user is dissatisfied with the current state of the Kariyer Ajanı project. Specifically, the UI is too simple and lacks the "premium" feel expected of a modern AI tool. Additionally, several core features (CV analysis, Gmail syncing, CV deletion) are either broken or unintuitive.

## Goals
1.  **Premium UI/UX**: Completely revamp the frontend with a "Mission Control / HUD" style design. Use Anime.js for sophisticated animations (parallax, path drawing, staggered reveals).
2.  **Fix CV Analysis**: Ensure uploaded CVs are correctly extracted and analyzed by Gemini.
3.  **Add CV Deletion**: Implement a way to delete CVs from both the database and the filesystem.
4.  **Improve Gmail Syncing**: Fix the "0 items" issue by allowing syncing of already seen emails and relaxing AI filtering criteria.
5.  **Unified Workflow**: Create a cohesive operational center for scanning, analysis, and application approval.

## Technical Requirements
- **Backend**: FastAPI, SQLAlchemy (SQLite), imaplib, pdfplumber, Gemini API.
- **Frontend**: React, Vite, Anime.js, Lucide React, Glassmorphism CSS.
- **AI**: Gemini 2.0 Flash for CV analysis, email categorization, and cover letter generation.

## Specific Fixes
### Backend
- **CV Router**: 
    - Ensure `upload_cv` correctly triggers `analyze_cv_ats`.
    - Verify `delete_cv` is accessible and functional.
- **Inbox Router**: 
    - Debug `run_sync` to ensure it doesn't fail silently.
    - Modify `GmailService.fetch_latest_emails` to search for more than just `UNSEEN` emails (e.g., last 30 days).
- **Email Agent**: 
    - Lower the relevance score threshold or improve the prompt to avoid missing opportunities.

### Frontend
- **Design System**: 
    - Dark mode with deep blues/blacks.
    - Neon Cyan/Green accents.
    - Glassmorphism panels.
    - HUD elements (scanning lines, data grids).
- **Animations**:
    - "System Boot" sequence on load.
    - Smooth parallax transitions between sections.
    - SVG path animations for the "Network" section.
- **Components**:
    - `CyberModal` and `CyberToast` refinements.
    - `CVList` with delete buttons.
    - `Inbox` with better status indicators.
    - `ApplicationWorkflow` tracker.

## Quality Standards
- No broken links or 404s.
- Clear feedback for every user action (Toasts).
- Responsive layout (desktop first, but usable on mobile).
- High-performance animations (no lag).
