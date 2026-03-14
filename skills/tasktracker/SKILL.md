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
  Preferred high-level tool for creating new TaskTracker test cases. You provide
  a base JSON payload (summary, attributes, etc.) without `attributes.test_step`
  and an ordered list of step triples
  `[(step_description_1, step_data_1, step_result_1), ...]`. The tool builds the
  correct `attributes.test_step` structure for you and calls the API.

- `create_test_case(suit, test_case_json)`  
  Low-level test creation tool. The `test_case_json` body must already follow the
  TaskTracker schema. You can use `src/tasktracker/test_case_json_example.json` as
  a canonical example of the expected create body (including `attributes.test_step`).

- `update_test_case(code, patch_json)`  
  Update an existing test case by code using a minimal JSON patch. You can use
  `src/tasktracker/patch_json_example.json` as a canonical example of how to
  structure patches for `attributes.test_step.testStepList` and related fields.

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

