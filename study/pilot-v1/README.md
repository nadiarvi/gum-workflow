# Pilot v1 Study Setup

This folder contains a participant-ready setup for running GUM in a preliminary user study.

Files:

- `PARTICIPANT_GUIDE.md`: participant setup, run, export, and reset instructions
- `RESEARCHER_CHECKLIST.md`: researcher preparation and data collection checklist
- `MOVE_AND_QUERY_DATA.md`: move exported study data to your machine and query it
- `.env.example`: safe environment template with no real secrets
- `install.sh`: creates `.venv` and installs this repo
- `run_gum.sh`: starts GUM with participant-specific settings
- `query_gum.sh`: probes the participant's local GUM data
- `export_gum_data.sh`: zips the configured GUM data directory
- `import_participant_data.sh`: imports a participant export on the researcher's device
- `reset_gum_data.sh`: deletes the configured GUM data directory

The scripts use `GUM_DATA_DIR` so each participant can have an isolated local data folder.
