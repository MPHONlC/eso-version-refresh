# ESO Addon Version Refresh

Refreshes an Elder Scrolls Online addon manifest's `## AddOnVersion:` date-prefix (the `YYMMDDVVV` convention some addon authors use, where the first 6 digits are a date and the last few digits are a manually-controlled version suffix) to today's date, leaving the suffix untouched, and commits+pushes the change if it actually differs.

This never bumps your real version number - only the date portion. It's meant to run automatically - on every push to `main` (immediate), on a daily schedule (a catch-all in case nothing was pushed that day), and on demand via manual dispatch - so your manifest's declared date always reflects when the addon last actually shipped, without you doing it by hand.

## Usage

Your workflow must check out the repo first, with `permissions: contents: write` on the job (this action commits and pushes).

```yaml
name: Version Refresh

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 12 * * *'   # once a day, 12:00 UTC
  workflow_dispatch:
  workflow_call:

jobs:
  refresh-version:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v7

      - uses: MPHONlC/eso-version-refresh@Version-0.0.1
        with:
          manifest_file: 'MyAddon.addon'
          git_name: 'YourGitName'
          git_email: 'your-email@example.com'
```

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `manifest_file` | Yes | - | Path to your addon's `.addon` manifest file. |
| `git_name` | Yes | - | Git name to attribute the refresh commit to. |
| `git_email` | Yes | - | Git email to attribute the refresh commit to. |
| `skip_ci` | No | `true` | Appends `[skip ci]` to the commit message. Leave `true` if this runs from a push-triggered workflow, to avoid the commit re-triggering itself in a loop. |

## Outputs

| Output | Description |
|---|---|
| `changed` | `'true'` if the manifest was updated, `'false'` if it was already current. |
| `old_version` | The `AddOnVersion` before this run. |
| `new_version` | The `AddOnVersion` after this run. |

## Requirements

- Your manifest's `## AddOnVersion:` value must already follow the `YYMMDDVVV` shape (6-digit date + a fixed-length suffix) - this action only ever rewrites the first 6 digits.
- The calling job needs `permissions: contents: write`, since this action pushes directly.

## License

MIT - see [LICENSE](LICENSE).
