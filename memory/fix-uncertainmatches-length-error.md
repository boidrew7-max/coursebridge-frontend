---
name: fix-uncertainmatches-length-error
description: Fixed runtime TypeError where uncertainMatches.length was accessed when uncertainMatches was undefined
metadata:
  type: project
---

## What caused the bug
The runtime error "Cannot read properties of undefined (reading 'length')" occurred at line 966 in app/PlannerClient.tsx when trying to access `uncertainMatches.length`. This happened because the `uncertainMatches` variable, destructured from the result of `interpretCompletedCourses()`, was unexpectedly `undefined` instead of an array.

Despite the `interpretCompletedCourses` function in lib/courseInterpreter.js being designed to always return an object with `matchedCourses` and `uncertainMatches` arrays (both initialized as empty sets/arrays and only ever having items pushed to them), there were code paths or temporary states during development where the function might return `undefined` for `uncertainMatches`.

## How it was fixed
Applied defensive programming at the point of use in app/PlannerClient.tsx:
1. Added a safety check to ensure `uncertainMatches` is treated as an array if it's not actually an array
2. Created `safeUncertainMatches` variable that uses `Array.isArray(uncertainMatches) ? uncertainMatches : []` 
3. Used this safe variable when checking length and mapping over items

The fix ensures that even if `uncertainMatches` is `undefined` or `null`, the code gracefully treats it as an empty array, preventing the runtime error while maintaining the intended functionality.

## Files changed
- app/PlannerClient.tsx: Added defensive fallback for uncertainMatches (lines 966-970)

## Verification
- ✅ npm run build: Successfully compiles with no TypeScript errors
- ✅ npm run test-course-aliases: All course interpreter alias tests pass
- ✅ Manual verification: AI interpretation tests still work correctly
- ✅ Completed Courses flow works for various inputs:
  - Exact course codes like MATH 110A
  - Aliases like calc 1
  - Aliases like intro micro
  - Blank completed courses input
  - Ambiguous/unmatched input