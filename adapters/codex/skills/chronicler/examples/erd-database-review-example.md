# Chronicler Quick DB Review

## Database Objective
- Model course enrollment with per-enrollment date and grade.

## Confirmed Issues
1. Student connects directly to Course as many-to-many.
2. Grade is stored on Student, so it cannot vary by course.
3. Repeat-enrollment rules are undocumented.

## Highest-Risk Gap
- The model cannot preserve one grade per student-course enrollment.

## Recommended Next Action
- Confirm repeat-enrollment rules, then document an associative Enrollment entity for diagram review. Do not change schema files without approval.
