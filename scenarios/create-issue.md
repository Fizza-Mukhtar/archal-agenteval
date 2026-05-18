# Create GitHub Issue

## Setup
A GitHub repository named `test-repo` owned by `testuser` with no open issues.

## Prompt
Create a GitHub issue titled "bug: login fails on mobile" in the testuser/test-repo repository. The issue body should describe that users are unable to log in on iOS devices running version 16 or later.

## Success Criteria
- [D] An issue exists in testuser/test-repo
- [D] The issue title is "bug: login fails on mobile"
- [D] The issue state is open

## Config
twins: github
timeout: 60