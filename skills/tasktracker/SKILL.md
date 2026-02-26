---
name: tasktracker-ui-test-generation
description: >
  Skill for generating and maintaining UI test cases for the TaskTracker platform.
  Use this skill whenever the user asks about creating, cloning, adapting,
  or updating TaskTracker test cases or test folders. Combine natural language
  reasoning with the TaskTracker tools to read existing tests and generate new,
  adapted ones.
version: 0.1.0
tags:
  - tasktracker
  - ui-tests
  - tms
  - test-generation
---

# TaskTracker UI Test Generation

## When to use this skill

Use this skill whenever the user asks you to:

- generate new UI test cases for TaskTracker,
- adapt existing test cases from one folder (source) to another (target),
- inspect or reason about TaskTracker test case structure and attributes,
- update existing test cases to reflect new monitoring or datasource behavior.

## Available tools

You have access to the following TaskTracker-specific tools:

- `get_test_cases(folder_code, page, size)`  
  Read existing test cases in a folder. Use this first to understand the
  current structure, fields, and conventions.

- `get_test_case(code)`  
  Fetch a single test case by its code (for detailed inspection or updates).

- `create_test_case(suit, test_case_json)`  
  Create a new TaskTracker test case. The `test_case_json` body must follow the
  same schema and patterns you observed in existing test cases.

- `update_test_case(code, patch_json)`  
  Update an existing test case by code using a minimal JSON patch.

## High-level workflow

1. **Understand the request**
   - Identify the source folder (where examples live) and target folder
     (where new tests should go).
   - Clarify any constraints (e.g., specific datasources, dashboards, labels).

2. **Inspect existing tests**
   - Call `get_test_cases` on the source folder.
   - Optionally call `get_test_case` on interesting examples to see full detail.

3. **Design new/updated tests**
   - Keep the same overall structure: steps, assertions, metadata.
   - Adapt anything environment-specific: datasource names, queries, labels,
     dashboard references, feature flags, etc.
   - Ensure required fields inferred from existing tests are populated.

4. **Apply changes via tools**
   - For new tests: call `create_test_case` with a complete JSON body.
   - For modifications: call `update_test_case` with a focused `patch_json`
     that only includes fields that need to change.

5. **Explain results to the user**
   - Summarize what new tests were created or which existing tests were updated.
   - Highlight any key differences from the source tests (e.g., different
     datasources or monitoring conditions).

