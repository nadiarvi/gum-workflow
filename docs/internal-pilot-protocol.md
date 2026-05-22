# 30-Minute Internal Pilot Protocol

Use this protocol to test whether GUM can infer a reusable workflow pattern from one real computer-use task, whether the extracted workflow is represented at the right depth, and how participants reason about delegating parts of that workflow to an AI agent.

## Pilot Goal

Run one lightweight internal session where a participant performs a real task on their own computer while GUM observes. The session should produce:

- The participant's initial task framing.
- GUM's extracted workflow record or CLI output.
- Moderator notes on task boundaries, tool switches, decisions, revisions, verification, and stopping points.
- Participant corrections to the workflow name, inputs, outputs, and steps.
- Step-level accuracy and usefulness labels.
- Delegation labels for which parts an AI agent could do, draft, or should not automate.
- The participant's rule of thumb for deciding what is delegable.

## Roles

- **Participant:** Performs one real task they already intended to do.
- **Moderator:** Frames the session, starts and stops observation, takes notes, runs workflow extraction, and leads review.
- **GUM:** Observes computer use and extracts workflow candidates from the resulting observations.

## Lightweight Consent And Framing

Before observation starts, say:

> This is an internal pilot to test whether GUM can infer reusable workflow patterns from normal computer use. GUM will observe your screen during the task window and may capture visible application content, websites, filenames, and text on screen. Please avoid opening anything you do not want observed. I will tell you when observation starts and stops. We will review the extracted workflow together and you can mark anything as wrong, too specific, private, or not useful.

Confirm the participant is ready before starting GUM observation.

## Session Timeline

### 0-3 min: Task Framing

Ask the participant to choose one real task they already intended to do. Capture their answers before observation begins:

| Field | Notes |
| --- | --- |
| Task description |  |
| Starting inputs or materials |  |
| Expected output or result |  |
| Done condition |  |
| Routine / occasional / one-off |  |

Suggested prompts:

- "Before you start, what are you trying to accomplish?"
- "What are you starting from?"
- "What would count as being done?"
- "Is this a task you repeat, or is it specific to today?"

### 3-15 min: Observed Task Performance

Start GUM observation and ask the participant to perform the task naturally.

Moderator guidance:

- Avoid interrupting unless the participant gets blocked.
- Note task boundaries and tool switches.
- Mark moments where the participant appears to make a decision, copy or paste, search, revise, verify, or stop.
- Distinguish active work from passive viewing when possible.
- Keep time; if the task expands, ask the participant to finish a natural subtask.

Observation notes:

| Time | App / surface | Observed action | Decision or intent inferred? | Notes / uncertainty |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

### 15-20 min: Workflow Extraction

Stop or pause observation before review. Run the workflow extraction or merge command used by the current build.

Record the command and output:

| Field | Value |
| --- | --- |
| Extraction command |  |
| Workflow ID or source |  |
| Workflow name |  |
| Input |  |
| Output |  |
| Overall confidence |  |
| Reasoning / evidence summary |  |

If multiple workflows appear, review the one closest to the participant's stated task.

Extracted steps:

| Step # | Extracted step | Confidence | Evidence cited |
| --- | --- | --- | --- |
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |

### 20-28 min: Joint Review

Show the participant the extracted workflow name, input, output, steps, confidence, and reasoning or evidence.

Review dimensions:

- **Correctness:** Is this what you were doing?
- **Granularity:** Are the steps too broad, too fine-grained, or about right?
- **Missing context:** What did the system miss that matters?
- **Overreach:** Did it infer anything too specific, too personal, or not justified by observation?

Suggested prompts:

- "Looking at this extracted workflow, what feels right?"
- "What feels too shallow or too detailed?"
- "Are any steps missing because they happened in your head?"
- "Did the system mistake passive viewing for intentional action?"

Step review labels:

- `Accurate`
- `Partially accurate`
- `Wrong`
- `Too detailed`
- `Too vague`
- `Not useful for automation`

Step review table:

| Step # | Participant label | Correction or missing context | Overreach / privacy concern |
| --- | --- | --- | --- |
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |

Workflow-level corrections:

| Field | System extraction | Participant correction |
| --- | --- | --- |
| Name |  |  |
| Input |  |  |
| Output |  |  |
| Boundary / scope |  |  |
| Reasoning / evidence |  |  |

### 28-30 min: Delegation Judgment

Ask:

- "If this workflow were sent to an AI agent, which parts would you want it to do for you?"
- "Which parts would you still want to do yourself?"
- "What rule or heuristic would you use to decide that?"

Delegation labels:

- `Agent can do`
- `Agent can draft but user reviews`
- `User must do`
- `Do not automate`

Delegation table:

| Step # | Delegation label | Why | Required review or guardrail |
| --- | --- | --- | --- |
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |

Heuristic notes:

| Delegability factor | Participant's view |
| --- | --- |
| Low risk |  |
| Boring or repetitive |  |
| Reversible |  |
| Easy to verify |  |
| Requires judgment |  |
| Involves private or sensitive material |  |
| Other rule of thumb |  |

## Analysis Rubric

Evaluate the extracted workflow after the session:

| Dimension | Guiding question | Rating / notes |
| --- | --- | --- |
| Task match | Does the workflow correspond to the participant's stated task? |  |
| Boundary quality | Did it start and end at the right level? |  |
| Step granularity | Are steps actionable without being noisy? |  |
| Evidence grounding | Are steps supported by observations? |  |
| Missing tacit knowledge | What important intent or judgment was invisible from computer use? |  |
| Delegability | Which parts could plausibly become agent actions? |  |
| User control preference | Where does the participant want approval, editing, or manual control? |  |

## Moderator Checklist

Before the session:

- Confirm GUM can observe the participant's screen.
- Confirm the participant understands what is observed.
- Prepare a timer and note-taking document.
- Prepare the workflow extraction or merge command.

During the session:

- Capture initial task framing before observation.
- Start observation only after confirming readiness.
- Avoid coaching the participant through the task.
- Note visible decisions, switches, revisions, verification, and stopping points.
- Keep the review focused on one workflow if multiple are extracted.

After the session:

- Save the raw extracted workflow JSON or CLI output.
- Save participant corrections and step labels.
- Save delegation labels and heuristics.
- Note any prompt, schema, or UX changes suggested by the review.

