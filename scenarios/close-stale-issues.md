# Close Stale Issues

## Setup
A GitHub repository named `test-repo` owned by `testuser` with 5 open issues.
3 of them have no activity in the last 90 days.

## Prompt
Find all open issues in testuser/test-repo that have had no activity in the last 90 days and close them with a comment explaining they are being closed due to inactivity.

## Success Criteria
- [D] Exactly 3 issues are closed
- [D] Each closed issue has a new comment
- [P] The comment mentions inactivity as the reason

## Config
twins: github
timeout: 90