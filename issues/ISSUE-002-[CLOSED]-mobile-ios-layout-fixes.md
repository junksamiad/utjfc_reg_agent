# ISSUE-002: Mobile iOS Layout and Input Focus Fixes

**Priority**: High
**Type**: Bug
**Component**: Frontend
**Created**: 2024-12-15 (estimated)
**Status**: CLOSED
**Resolution Date**: 2024-12-15

## Executive Summary

Critical mobile experience issue on iOS devices where the chat interface had severe layout problems including unwanted scrollbars, layout thrashing during keyboard appearance, and zoom behavior on input focus. This issue significantly impacted user experience on mobile devices, particularly during registration flows.

## Current Implementation (Before Fix)

### Problematic Viewport Configuration
```html
<!-- frontend/web/src/app/layout.tsx -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
```

### Missing Mobile-Specific CSS
- No font-size controls for iOS zoom prevention
- No hardware acceleration for mobile inputs
- No iOS-specific keyboard handling

## Problems Identified

### 1. Layout Thrashing on iOS
- **Root Cause**: `user-scalable=no` and `maximum-scale=1.0` in viewport meta tag
- **Impact**: Caused layout instability during keyboard appearance/disappearance
- **Symptoms**: Scrollbars appearing, content jumping, poor UX

### 2. Unwanted Zoom on Input Focus
- **Root Cause**: Input elements with font-size < 16px
- **Impact**: iOS Safari/Chrome would zoom in automatically
- **Symptoms**: Disruptive zoom behavior during chat input

### 3. Keyboard Handling Issues
- **Root Cause**: No iOS-specific keyboard event handling
- **Impact**: Document scrolling and layout shifts during input focus
- **Symptoms**: Chat interface becoming unusable during typing

## Implemented Solution

### 1. Viewport Meta Tag Fix
```html
<!-- AFTER: frontend/web/src/app/layout.tsx -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
```
**Change**: Removed `user-scalable=no` and `maximum-scale=1.0`

### 2. iOS Zoom Prevention CSS
```css
/* frontend/web/src/app/globals.css */
/* Prevent iOS zoom on input focus by ensuring font-size >= 16px */
input, textarea {
  font-size: 16px;
}

/* Additional iOS-specific input handling */
@media screen and (-webkit-min-device-pixel-ratio: 0) {
  select, textarea, input[type="text"] {
    font-size: 16px;
  }
}
```

### 3. Enhanced Mobile Performance CSS
```css
/* frontend/web/src/app/globals.css */
@media (max-width: 768px) {
  /* Prevent layout shifts on focus */
  textarea, input {
    transform: translateZ(0);
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
  }
  
  /* Improve touch scrolling performance */
  * {
    -webkit-overflow-scrolling: touch;
  }
}
```

### 4. iOS-Specific Input Focus Management
```typescript
// frontend/web/src/app/chat/_components/chat-input.tsx
const handleInputFocus = useCallback(() => {
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
        document.body.style.position = 'fixed';
        document.body.style.width = '100%';
        document.body.style.top = `-${window.scrollY}px`;
    }
}, []);

const handleInputBlur = useCallback(() => {
    if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
        const scrollY = document.body.style.top;
        document.body.style.position = '';
        document.body.style.width = '';
        document.body.style.top = '';
        if (scrollY) {
            window.scrollTo(0, parseInt(scrollY || '0', 10) * -1);
        }
    }
}, []);
```

### 5. Layout Stability Enhancement
```jsx
// frontend/web/src/app/chat/page.tsx
<div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-850 min-h-0">
```
**Change**: Added `min-h-0` to prevent flex container collapse

### 6. Explicit Font Size Override
```jsx
// frontend/web/src/app/chat/_components/chat-input.tsx
<textarea
  style={{ fontSize: '16px' }}
  // ... other props
/>
```

## Implementation Checklist

- [x] Update viewport meta tag in layout.tsx
- [x] Add iOS zoom prevention CSS rules
- [x] Implement mobile-specific performance CSS
- [x] Add iOS keyboard focus/blur handlers
- [x] Enhance layout stability with min-h-0
- [x] Set explicit 16px font size on textarea
- [x] Add delayed focus for better UX
- [x] Test on actual iOS devices
- [x] Deploy to production via CloudFront
- [x] Verify fixes work across iOS versions

## Testing Instructions

### Device Testing
1. **iPhone Safari**: Test input focus, typing, keyboard appearance
2. **iPhone Chrome**: Verify same behavior as Safari
3. **iPad**: Test in both portrait and landscape orientations
4. **Various iOS versions**: Test on iOS 14+

### Specific Test Scenarios
1. **Initial page load**: Verify no layout issues
2. **Chat input focus**: No unwanted zoom or scrollbars
3. **Typing messages**: Stable layout during keyboard use
4. **File upload**: Test photo upload flow on mobile
5. **Message scrolling**: Smooth scrolling throughout chat
6. **Device rotation**: Layout remains stable during orientation changes

## Results Achieved

- ✅ **No scrollbars** appearing after input interaction
- ✅ **Stable layout** during keyboard appearance/disappearance  
- ✅ **No unwanted zoom** on input focus
- ✅ **Smooth scrolling** throughout the app
- ✅ **Proper viewport handling** during redirects
- ✅ **Improved performance** with hardware acceleration

## Monitoring and Verification

### Production Verification
- **URL**: https://urmstontownjfc.co.uk/chat/
- **Testing Period**: December 2024
- **Results**: All iOS layout issues resolved
- **User Feedback**: Positive mobile experience reports

### Chrome DevTools Testing
- **Layout shifts**: Eliminated during input focus
- **Viewport changes**: Stable during keyboard events
- **Performance**: Improved scroll performance on mobile

## Rollback Plan

If any regressions occur, the primary rollback point is the viewport meta tag:

```html
<!-- Emergency rollback only -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
```

**Note**: The CSS changes (font sizes, hardware acceleration) are safe to keep as they only improve performance.

## Additional Context

### Related Files Modified
- `frontend/web/src/app/layout.tsx` - Viewport meta tag
- `frontend/web/src/app/globals.css` - Mobile CSS enhancements
- `frontend/web/src/app/chat/page.tsx` - Layout stability
- `frontend/web/src/app/chat/_components/chat-input.tsx` - Input handling

### Technical References
- [iOS Safari Web Content Guide](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/UsingtheViewport/UsingtheViewport.html)
- [Preventing iOS Zoom on Input Focus](https://css-tricks.com/16px-or-larger-text-prevents-ios-form-zoom/)
- [Mobile Web Best Practices](https://developers.google.com/web/fundamentals/design-and-ux/responsive)

### Infrastructure Impact
- **Deployment**: Standard CloudFront deployment
- **Performance**: Improved mobile rendering performance
- **Compatibility**: Enhanced iOS compatibility without breaking other platforms

This issue resolution significantly improved the mobile user experience and eliminated a major barrier to successful registrations on iOS devices.