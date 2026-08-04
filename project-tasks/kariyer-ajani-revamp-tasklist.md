# Kariyer Ajanı Revamp Task List

## Phase 1: Backend Infrastructure & AI Refinement
### [/] Task 1.1: Fix Gmail Syncing Logic
- **Requirement**: "Modification of GmailService.fetch_latest_emails to search for more than just UNSEEN emails."
- **Status**: Implemented `SINCE` search. Needs validation on duplicate UID handling in DB.

### [ ] Task 1.2: Improve AI Email Filtering
- **Requirement**: "Improve the prompt to avoid missing opportunities."
- **Action**: Relax relevance score thresholds and refine the prompt (Work in progress).

### [x] Task 1.3: Robust CV Deletion
- **Requirement**: "Implement a way to delete CVs from both the database and the filesystem."
- **Status**: COMPLETED. `delete_cv` endpoint handles both DB and file removal.

### [ ] Task 1.4: CV Analysis Validation
- **Requirement**: "Ensure uploaded CVs are correctly extracted and analyzed by Gemini."
- **Action**: Add more detailed logging and fallback mechanisms.

## Phase 2: Technical Architecture & UX Foundation
### [/] Task 2.1: CSS Design System (Premium HUD)
- **Status**: Initial tokens defined. Needs more pulse and path animation classes.

### [ ] Task 2.2: Anime.js Master Timeline
- **Status**: Boot sequence working. Parallax and section transitions need polish.

## Phase 3: Development - Frontend Revamp
### [ ] Task 3.1: Redesign Section 1 (Mission Control)
- **Action**: Add CV delete buttons to the HUD panel.

### [ ] Task 3.2: Redesign Section 2 (Global Network)
- **Requirement**: "SVG path animations for the Network section."
- **Action**: Implement pulsing nodes and moving path data packets during scan.

### [ ] Task 3.3: Redesign Section 3 (Autonomous Protocol)
- **Requirement**: "Unified operational center for scanning, analysis, and application approval."
- **Action**: Implement the `ProtocolTracker` component with live status updates.

### [ ] Task 3.4: Enhanced Feedback Components
- **Action**: CyberModal/Toast entry/exit animations improvement.

## Phase 4: Final Integration & Verification
### [ ] Task 4.1: End-to-End Testing
- **Requirement**: "No broken links or 404s. Clear feedback for every user action."

### [ ] Task 4.2: Reality Check
- **Requirement**: "Default to 'NEEDS WORK' unless overwhelming evidence proves production readiness."

---
*Son Güncelleme: 2026-04-24*
