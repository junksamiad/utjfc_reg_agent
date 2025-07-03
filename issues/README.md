# Development Issues Tracker

This folder contains detailed technical issues and improvements for the UTJFC Registration System. Each issue is documented comprehensively to allow any developer to understand and implement the solution.

## Issue Format

Each issue follows the naming convention: `ISSUE-XXX-[STATUS]-component-brief-description.md`

- `XXX` - Sequential issue number (001, 002, etc.)
- `[STATUS]` - Either `[OPEN]` or `[CLOSED]`
- `component` - The system component (frontend, backend, registration, etc.)
- `brief-description` - Short kebab-case description

### Examples:
- `ISSUE-001-[OPEN]-frontend-environment-config.md`
- `ISSUE-002-[CLOSED]-photo-upload-413-error.md`

## Issue Document Structure

Each issue document contains:

1. **Header Information**
   - Issue number and title
   - Priority (Critical/High/Medium/Low)
   - Type (Bug/Feature/Configuration/Security/Performance)
   - Component affected
   - Creation date
   - Status (Open/In Progress/Resolved/Closed)

2. **Executive Summary**
   - Brief overview of the issue

3. **Current Implementation**
   - Code snippets showing current state
   - File locations

4. **Problems Identified**
   - Detailed explanation of issues
   - Impact on system

5. **Proposed Solution**
   - Step-by-step implementation guide
   - Code examples
   - Configuration changes

6. **Implementation Checklist**
   - Actionable items with checkboxes

7. **Testing Instructions**
   - How to verify the fix

8. **Additional Context**
   - Related documentation
   - Infrastructure details
   - References

## Current Issues

| Issue | Title | Priority | Status |
|-------|-------|----------|---------|
| [ISSUE-001](./ISSUE-001-[OPEN]-frontend-environment-config.md) | Frontend Environment Configuration - Hardcoded API URLs | Medium | Open |
| [ISSUE-002](./ISSUE-002-[CLOSED]-photo-upload-413-error.md) | Photo Upload 413 Request Entity Too Large Error | Critical | Closed |
| [ISSUE-003](./ISSUE-003-[OPEN]-frontend-ios-mobile-rendering.md) | iOS Mobile Chat UI Rendering Problems | Critical | Open |

## Creating New Issues

When creating a new issue:

1. Use the next sequential number
2. Follow the naming convention
3. Include all sections from the template
4. Be as detailed as possible
5. Include code examples
6. Add to the table above

## Issue Priority Guide

- **Critical**: System breaking, security vulnerabilities, data loss risk
- **High**: Major functionality impaired, poor user experience
- **Medium**: Minor functionality issues, improvements needed
- **Low**: Nice-to-have features, minor optimizations

## Status Definitions

- **Open**: Issue identified, not yet started
- **In Progress**: Currently being worked on
- **Resolved**: Solution implemented, awaiting verification
- **Closed**: Verified and deployed to production 