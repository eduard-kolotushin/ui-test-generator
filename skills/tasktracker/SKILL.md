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
  - pvm
  - view
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

These tools are implemented by the **TaskTracker MCP server** (`src.mcp.tasktracker_server`) and are used by the Deep Agent via `src.mcp.tasktracker_client_tools`. They can also be used directly from Cursor when the MCP server is configured.

You have access to the following TaskTracker-specific tools:

**Folders (TMS plugin)**

- `get_root_folder_units(space_id_code, page, size)`  
  Get the root folder hierarchy and paginated units. Use this to discover
  folder structure and root-level test cases (e.g. space_id_code `PVM`).

- `create_folder(name, parent_id_code, space_id_code)`  
  Create a new folder under the given parent. Parent is often `PVM_test_case`
  for the root test-case tree, or a child folder code from the hierarchy.

**Test cases**

- `get_test_cases(folder_code, page, size)`  
  Read existing test cases in a folder. Use this first to understand the
  current structure, fields, and conventions.

- `get_test_case(code)`  
  Fetch a single test case by its code (for detailed inspection or updates).

- `create_test_case_from_steps(suit, test_case_base, steps)`  
  Preferred high-level tool for creating new TaskTracker test cases. The system
  prompt includes the exact `test_case_base` JSON structure to use (copy it and
  set summary, folder, space). Do not add `attributes.test_step` — the tool adds
  it from your ordered list of steps (step_description, step_data, step_result).

- `create_test_case(suit, test_case_json)`  
  Low-level test creation tool. Use only when you have a full API-shaped payload.

- `update_test_case_from_steps(code, steps)`  
  Preferred way to update an existing test case’s steps. Provide the test case code
  and an ordered list of steps (step_description, step_data, step_result). The tool
  builds the correct patch body and calls the API.

- `update_test_case(code, patch_json)`  
  Low-level update tool. Use when you need to patch fields other than steps.

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
   - For new tests: use the `test_case_base` structure from the system prompt and
     call `create_test_case_from_steps(suit, test_case_base, steps)`.
   - For step-only changes: call `update_test_case_from_steps(code, steps)`.
   - For other field changes: call `update_test_case(code, patch_json)`.

5. **Explain results to the user**
   - Summarize what new tests were created or which existing tests were updated.
   - Highlight any key differences from the source tests (e.g., different
     datasources or monitoring conditions).

