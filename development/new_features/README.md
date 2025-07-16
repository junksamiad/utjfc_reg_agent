# New Features Directory

This directory contains feature specification documents for new functionality being developed for the UTJFC Registration Agent system.

## New Organizational Structure

As of July 2025, we've implemented a new organizational structure for better maintainability and scalability:

### Per-Feature Directory Structure
Each feature now has its own dedicated directory containing:

```
feature-name/
├── README.md                    # Feature overview and testing instructions
├── feature_specification.md    # Complete feature documentation
├── implementation_plan.md      # Technical implementation details
└── tests/                      # All test scripts for the feature
    ├── test_comprehensive.py   # Main test suite
    ├── test_database_lookup.py # Database-specific tests
    ├── test_tool_integration.py # Tool registration tests
    └── test_manual.py          # Interactive testing utility
```

### Migration from Old Structure

**OLD (Deprecated)**:
- Individual `.md` files in root `new_features/` directory
- Mixed documentation and implementation files
- No organized testing structure

**NEW (Current)**:
- Per-feature directories with complete documentation
- Dedicated test directories for each feature
- Clear separation of concerns
- Scalable structure for future features

### Benefits of New Structure

#### 🎯 **Organization**
- All feature-related files in one place
- Clear separation between different features
- Easy to find and maintain feature documentation

#### 🧪 **Testing**
- Dedicated test directory for each feature
- Comprehensive test coverage with real data
- Easy to run feature-specific tests

#### 📚 **Documentation**
- Complete feature lifecycle documentation
- Implementation details preserved for future reference
- Clear migration path from old to new structure

#### 🔄 **Scalability**
- Template for future features
- Consistent structure across all features
- Easy to archive or reference completed features

## Document Guidelines

### File Naming Convention

- **In Development**: `feature_name.md`
- **Implemented**: `feature_name_IMPLEMENTED.md`
- **Cancelled/Deprecated**: `feature_name_CANCELLED.md`

### Document Structure

All feature documents should follow this standardized structure:

#### Header Section
```markdown
# Feature Name

**Feature ID**: `kebab-case-feature-id`  
**Status**: [Planning|In Development|Testing|Implemented|Cancelled]  
**Priority**: [Low|Medium|High|Critical]  
**Estimated Effort**: [e.g., "2-3 hours", "1-2 days", "1 week"]  
**Dependencies**: [List any dependencies or "None"]  
**Implementation Date**: [YYYY-MM-DD] (when implemented)  
**Implemented By**: [Developer/AI agent name] (when implemented)  
**Branch**: [feature branch name] (when implemented)  

---
```

#### Core Sections

1. **Overview**
   - Brief description of the feature
   - High-level purpose and goals

2. **Business Requirements**
   - **Problem Statement**: What problem does this solve?
   - **Success Criteria**: How do we measure success?
   - **User Stories**: Who benefits and how?

3. **Technical Changes Required**
   - **Code Locations to Update**: Specific files and components
   - **Database Considerations**: Schema changes, migrations needed
   - **API Changes**: New endpoints, modifications to existing ones
   - **Frontend Changes**: UI/UX modifications needed

4. **Implementation Notes**
   - **Architecture Considerations**: Design patterns, best practices
   - **Security Considerations**: Authentication, authorization, data protection
   - **Performance Considerations**: Scalability, optimization needs
   - **Integration Points**: How it connects with existing systems

5. **Testing Strategy**
   - **Unit Testing**: What needs unit test coverage
   - **Integration Testing**: System interaction testing
   - **Manual Testing**: User acceptance testing scenarios
   - **Edge Cases**: Boundary conditions and error scenarios

6. **Risk Assessment**
   - **Risk Level**: [Very Low|Low|Medium|High|Very High]
   - **Potential Issues**: What could go wrong?
   - **Mitigation**: How to reduce risks
   - **Rollback Plan**: How to undo changes if needed

7. **Deployment**
   - **Changes Required**: Step-by-step deployment instructions
   - **Environment Variables**: New config needed
   - **Migration Steps**: Database or data migration procedures
   - **Verification Steps**: How to confirm successful deployment

8. **Future Considerations**
   - **Extensibility**: How this feature might evolve
   - **Maintenance**: Ongoing support requirements
   - **Related Features**: What other features might build on this

#### Implementation Details Section (for IMPLEMENTED features)

When a feature is implemented, add this section:

9. **Implementation Details**
   - **Implementation Summary**: What was actually built
   - **Files Modified**: List of changed files with descriptions
   - **Testing Recommendations**: How to test the implemented feature
   - **Notes**: Any deviations from the original plan

### Status Definitions

- **Planning**: Feature requirements being defined
- **In Development**: Actively being coded
- **Testing**: Implementation complete, undergoing testing
- **Implemented**: Successfully deployed and working
- **Cancelled**: Feature development discontinued

### Priority Definitions

- **Critical**: System breaking issue, immediate attention required
- **High**: Important feature for business goals, next sprint priority
- **Medium**: Valuable improvement, can be scheduled
- **Low**: Nice to have, lowest scheduling priority

### Best Practices

1. **Be Specific**: Include exact file paths, function names, and technical details
2. **Consider Dependencies**: Think about how changes affect other parts of the system
3. **Plan for Testing**: Define clear testing strategies before implementation
4. **Document Decisions**: Explain why certain approaches were chosen
5. **Keep Updated**: Modify documents as requirements change during development
6. **Version Control**: Commit feature documents alongside code changes

### Templates

For quick feature creation, copy the structure from `extend_kit_number_range_IMPLEMENTED.md` for smaller features or `automated_payment_chasing.md` for larger, complex features.

### Important Implementation Reminder

⚠️ **CRITICAL FINAL STEP**: After any feature is deployed and tested successfully, agents must:

1. **Review System Documentation**: Check `/Users/leehayton/Cursor Projects/utjfc_reg_agent/system_docs/` for any documentation that needs updating
2. **Update Relevant Documents**: Look for files that might need updates based on the new feature:
   - Architecture diagrams
   - API documentation
   - Process flow documents
   - Technical specifications
   - User guides
3. **Update Implementation Plan**: Add a final section documenting what system documentation was updated

This ensures the codebase documentation stays current and accurate for future development.

## Directory Organization

### Feature Structure
Each feature should have its own directory containing:
- `feature_specification.md` - Main feature documentation
- `implementation_plan.md` - Technical implementation details
- `tests/` - All test scripts for the feature
- `README.md` - Feature overview and testing instructions

### Current Features
- `restart_chat_if_disconnected/` - ✅ IMPLEMENTED - Resume registration after disconnection
  - **Status**: Ready for deployment
  - **Branch**: `feature/restart-chat-if-disconnected`
  - **Test Coverage**: Comprehensive test suite created
- `extend_kit_number_range_IMPLEMENTED.md` - ✅ IMPLEMENTED - Extended kit numbers 1-49
  - **Status**: Deployed in production
  - **Legacy Format**: Will be migrated to new structure in future
- `automated_payment_chasing.md` - 📋 PLANNING - Automated payment follow-up system
  - **Status**: Planning phase
  - **Legacy Format**: Will be migrated to new structure when implemented

### Naming Convention
- **Feature Directories**: Use kebab-case (e.g., `restart-chat-if-disconnected/`)
- **Implemented Features**: Keep directory structure, update status in documentation
- **Legacy Features**: Will be migrated to new structure over time
- **Cancelled Features**: Move to `cancelled/` subdirectory if needed

---

*This README should be updated as the feature development process evolves.*