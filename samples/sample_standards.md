# Team Standards — TaskFlow

## Sprint Capacity
Default sprint points: 40
Velocity adjustment: apply --velocity flag from last sprint

## Definition of Ready
- Feature must have at least 2 acceptance criteria
- Security features require explicit security review note
- No feature over 8 points without subtask breakdown

## QA Standards
- All API endpoints need happy path + error path test cases
- Auth features require token expiry edge case coverage
- Performance test required for any database query endpoint

## Engineering Standards
- All new endpoints need OpenAPI documentation
- Database migrations must be reversible
- No PR merges without passing CI
