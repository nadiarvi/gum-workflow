# GUM Pilot v1 Researcher Checklist

Use this checklist to prepare a participant machine and collect the GUM data artifact after the study.

## Before The Session

- Confirm participant consent explicitly covers screen observation, local storage, data export, retention period, and who can access the exported archive.
- Decide whether you need the full GUM folder or only `gum.db`. The full folder may include screenshots and queued raw observations.
- Create one participant ID per participant, for example `p01`, `p02`, `p03`.
- Provide a per-participant API key, short-lived key, or controlled proxy endpoint. Do not distribute your personal API key.
- If using a remote model endpoint, test the `GUM_LM_API_BASE` and `GUM_LM_API_KEY` values before the participant session.

## Recommended Branch Distribution

Ask the participant to clone this branch:

```bash
git clone --branch pilot-v1 https://github.com/nadiarvi/gum-workflow.git
cd gum-workflow
```

Then have them follow:

```bash
study/pilot-v1/PARTICIPANT_GUIDE.md
```

## Participant Env Values

Set `study/pilot-v1/.env` like this:

```bash
USER_NAME="p01"
MODEL_NAME="gpt-4o-mini"
OPENAI_API_KEY="participant-specific-key"
GUM_DATA_DIR="$HOME/.cache/gum-pilot-v1-p01"
MIN_BATCH_SIZE=3
MAX_BATCH_SIZE=8
```

Use a unique `GUM_DATA_DIR` for every participant. This prevents overwriting data and makes exports easy to label.

## During The Session

- Start GUM with `./study/pilot-v1/run_gum.sh`.
- Confirm Terminal has Accessibility and Screen Recording permissions.
- Let GUM run during the assigned task.
- Avoid collecting unrelated private activity beyond the approved study window.

## End Of Session

Stop GUM:

```bash
Ctrl-C
```

Export:

```bash
./study/pilot-v1/export_gum_data.sh
```

Confirm the zip exists in:

```bash
study_exports/
```

Record:

- participant ID
- date and time
- study task condition
- archive filename
- whether screenshots were included
- any setup or permission issues

## Probing A Participant Model Later

Use the move and query guide:

```bash
study/pilot-v1/MOVE_AND_QUERY_DATA.md
```

Short version: import the participant export on your machine:

```bash
./study/pilot-v1/import_participant_data.sh \
  ~/Downloads/gum-pilot-v1-p01-20260522-143000.zip \
  ~/.cache/gum-pilot-v1-p01
```

Then query against that participant's folder:

```bash
source .venv/bin/activate
gum --data-directory "$HOME/.cache/gum-pilot-v1-p01" --recent
gum --data-directory "$HOME/.cache/gum-pilot-v1-p01" -q "your probe query" -l 10
gum --data-directory "$HOME/.cache/gum-pilot-v1-p01" --workflows
```

If you unzip into a different location, pass that path to `--data-directory`.

## Data Handling

Treat exports as sensitive study data. They may contain:

- `gum.db`
- screenshots
- raw observations
- model-generated propositions
- workflow records
- queued batch files

Store exports only in the approved study storage location. Do not commit exports or `.env` files to git.
