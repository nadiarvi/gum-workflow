# Workflow Monitor Feature

## Summary

Create and push a new Git branch named `workflow-monitor` from `main`, then implement workflow-pattern extraction alongside the existing proposition pipeline. Each observation batch will produce both propositions and workflow records. Users will view recent workflow records with `gum -w` / `gum --workflows`.

## Key Changes

- Git workflow:
  - Create branch: `workflow-monitor`
  - Implement all changes there.
  - Push branch to `origin/workflow-monitor`.

- Data model:
  - Add a `Workflow` ORM model with:
    - `name`: activity/workflow name
    - `input`: inferred input or starting material
    - `output`: inferred output/result
    - `steps`: JSON text storing ordered steps
    - `reasoning`: evidence summary
    - `confidence`: overall workflow confidence, 1-10
    - `created_at`, `updated_at`
  - Add `observation_workflow` association table so workflows can be traced back to supporting observations.
  - Let `Base.metadata.create_all` create new tables automatically for local SQLite DBs.

- LLM extraction:
  - Add workflow schemas in `gum/schemas.py`.
  - Add a workflow prompt in `gum/prompts/gum.py`.
  - Add workflow construction and persistence methods in `gum/gum.py`, modeled after proposition extraction.
  - During batch processing, extract workflows from the same combined batch content and attach them to the stored observations.
  - Keep proposition behavior unchanged.

- CLI:
  - Add `--workflows` / `-w` to `gum/cli.py`.
  - `gum -w` lists recent workflows using `--limit/-l`.
  - Output each workflow with name, input, output, steps with confidence, reasoning, overall confidence, and creation time.

- Query helpers:
  - Add `get_recent_workflows(...)` in `gum/db_utils.py`.
  - Add `gum.recent_workflows(...)` as a public method.

## Test Plan

- Run `python -m compileall gum` to catch syntax/import errors.
- Run `.venv/bin/gum --help` and verify `--workflows, -w` appears.
- Run `.venv/bin/gum -w -l 5` against an empty/new DB and confirm it exits cleanly with `Recent 0 workflows`.
- Verify `gum -r` still shows recent propositions and existing query/listening behavior remains unchanged.

## Assumptions

- Workflow extraction is always enabled during normal monitoring.
- Workflows are stored separately from propositions rather than encoded as propositions.
- `steps` are stored as JSON text to avoid adding a separate workflow-step table for this first version.
- The branch is pushed to the existing remote: `origin` at `https://github.com/nadiarvi/gum-workflow.git`.
