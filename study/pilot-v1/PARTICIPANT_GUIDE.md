# GUM Pilot v1 Participant Setup

This guide installs and runs GUM for a preliminary user study. GUM observes computer interaction, including screen content, and stores study data locally on your device until you export it for the researcher.

## Before You Start

You need:

- macOS
- Python 3.10 or newer
- Terminal access
- The study API key or model endpoint provided by the researcher
- About 10 minutes for install and permissions

Do not continue until you have reviewed the study consent form. The local GUM data folder can include screenshots, raw observations, inferred propositions, and workflow records.

## 1. Open Terminal

Open the project folder in Terminal. If you downloaded a zip, unzip it first, then run:

```bash
cd path/to/gum-workflow
```

## 2. Install

```bash
./study/pilot-v1/install.sh
```

This creates a local Python environment in `.venv` and installs GUM from this folder.

## 3. Configure

Open `study/pilot-v1/.env` in a text editor and fill in the participant values:

```bash
USER_NAME="Participant 01"
MODEL_NAME="gpt-4o-mini"
OPENAI_API_KEY="paste-study-api-key-here"
GUM_DATA_DIR="$HOME/.cache/gum-pilot-v1-participant-01"
MIN_BATCH_SIZE=3
MAX_BATCH_SIZE=8
```

Use the participant ID assigned by the researcher. Do not put personal names in `USER_NAME` unless the study protocol specifically asks for it.

## 4. Grant macOS Permissions

GUM needs permission to observe screen and interaction events.

Open System Settings:

1. Privacy & Security -> Accessibility -> enable Terminal
2. Privacy & Security -> Screen Recording -> enable Terminal

If macOS prompts for permissions after the first run, grant them, stop GUM with `Ctrl-C`, then start it again.

## 5. Run GUM

```bash
./study/pilot-v1/run_gum.sh
```

Keep this Terminal window open while completing the study task. To stop GUM, press:

```bash
Ctrl-C
```

## 6. Quick Check

After GUM has run for a few minutes, you can check whether it has stored queryable data:

```bash
./study/pilot-v1/query_gum.sh
```

You can also query for a topic:

```bash
./study/pilot-v1/query_gum.sh "email"
```

It is normal to get few or no results at the very beginning.

## 7. Export Study Data

At the end of the study session, stop GUM with `Ctrl-C`, then run:

```bash
./study/pilot-v1/export_gum_data.sh
```

The script creates a zip file in:

```bash
study_exports/
```

Send that zip file to the researcher using the approved study transfer method. The researcher can use this export to query your study GUM after the session ends.

## 8. Reset Local Study Data

Only do this after the researcher confirms the export was received, or if the study protocol asks you to clear local data:

```bash
./study/pilot-v1/reset_gum_data.sh
```

This deletes the configured `GUM_DATA_DIR`.

## Troubleshooting

If `gum` is not found, rerun:

```bash
./study/pilot-v1/install.sh
```

If screen data is not being collected, check Accessibility and Screen Recording permissions, then restart Terminal.

If the API key fails, confirm that `OPENAI_API_KEY` is filled in correctly in `study/pilot-v1/.env`.

If you need to restart the study from scratch, ask the researcher before running the reset script.
