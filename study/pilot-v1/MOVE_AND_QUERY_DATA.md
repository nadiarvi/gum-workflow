# Move And Query Participant Data

This guide covers how to move the participant's GUM data from their device to your device after the study and query it later.

## What You Are Collecting

The participant setup stores all study data in `GUM_DATA_DIR`, configured in:

```bash
study/pilot-v1/.env
```

That folder contains the queryable GUM model state. The most important file is:

```bash
gum.db
```

The full folder may also contain screenshots, queued batch files, raw observations, and workflow data. The export script zips the full configured folder so you can probe the user's model after the session.

## On The Participant Device

Stop GUM first:

```bash
Ctrl-C
```

Create the export:

```bash
./study/pilot-v1/export_gum_data.sh
```

The script prints the archive path. It will look like:

```bash
study_exports/gum-pilot-v1-p01-20260522-143000.zip
```

Transfer that zip to your approved research storage or directly to your device. Use the transfer method approved by your protocol, such as encrypted cloud storage, encrypted external drive, or institutional secure transfer.

## On Your Device

Clone or open this branch, install the environment if needed, and activate it:

```bash
git clone --branch pilot-v1 https://github.com/nadiarvi/gum-workflow.git
cd gum-workflow
./study/pilot-v1/install.sh
source .venv/bin/activate
```

Put the participant zip somewhere local, such as `~/Downloads/`.

Import it into a stable participant-specific folder:

```bash
./study/pilot-v1/import_participant_data.sh \
  ~/Downloads/gum-pilot-v1-p01-20260522-143000.zip \
  ~/.cache/gum-pilot-v1-p01
```

The second argument is the destination directory. Use a unique folder per participant.

## Query The Participant Model

Recent propositions:

```bash
gum --data-directory ~/.cache/gum-pilot-v1-p01 --recent -l 20
```

Search propositions:

```bash
gum --data-directory ~/.cache/gum-pilot-v1-p01 -q "email habits" -l 10
```

Search with an empty query, which returns recent query results:

```bash
gum --data-directory ~/.cache/gum-pilot-v1-p01 -q -l 10
```

Recent workflows:

```bash
gum --data-directory ~/.cache/gum-pilot-v1-p01 --workflows -l 20
```

Use the same `--data-directory` value every time you probe that participant. This is what tells GUM which user's study model to inspect.

## Multiple Participants

Keep each participant in a separate folder:

```bash
~/.cache/gum-pilot-v1-p01
~/.cache/gum-pilot-v1-p02
~/.cache/gum-pilot-v1-p03
```

Then query each one by changing `--data-directory`:

```bash
gum --data-directory ~/.cache/gum-pilot-v1-p02 -q "calendar" -l 10
```

## Verify An Import

Check that the database exists:

```bash
ls ~/.cache/gum-pilot-v1-p01/gum.db
```

Check that GUM can read it:

```bash
gum --data-directory ~/.cache/gum-pilot-v1-p01 --recent -l 5
```

If there are no results, confirm that GUM ran long enough during the study and that the archive was created from the correct `GUM_DATA_DIR`.

## Data Handling

Treat the zip and imported folder as sensitive study data. Do not commit them to git. Do not share them outside the approved research workflow.
