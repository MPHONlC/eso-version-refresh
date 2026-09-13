# Version Refresh

Refreshes the date portion of a text manifest's version field to today, leaving the rest of the value untouched, and commits+pushes the change if it actually differs. Works with any manifest that declares a field as `## <FieldName>: <value>` on its own line - not tied to a field-naming convention.

This never bumps your real version number - only the date portion. It's meant to run automatically - on every push to `main` (immediate), on a daily schedule (a catch-all in case nothing was pushed that day), and on demand via manual dispatch - so your manifest's declared date always reflects when the addon last actually shipped, without you doing it by hand.

## The `format` template

`Y`/`M`/`D` mark date digits (repeat for width: `YY` = 2-digit year, `YYYY` = 4-digit year, `MM`/`DD` default to width 2 if repeated twice). `V` marks version digits - never touched, any width. Any other character is a literal that must match exactly at that position (e.g. the dots in `V.V.V`). The date run can be a prefix, a suffix, or use a different date order:

| Your scheme | `format` |
|---|---|
| `260913009` (date first, YYMMDD + 3-digit version) | `YYMMDDVVV` |
| `009260913` (version first) | `VVVYYMMDD` |
| `09091326` (2-digit version, then MMDDYY) | `VVMMDDYY` |
| `130926009` (DDMMYY, date first) | `DDMMYYVVV` |
| `20260913` (full 4-digit year, no version segment) | `YYYYMMDD` |
| `1.0.0`, `10000`, or any value with no date at all | `NONE` |
| `1748895315` (Unix timestamp, e.g. an `IntVersion` field) | `TIMESTAMP` |

If your value doesn't match the declared `format` (wrong length, or a literal character doesn't match), the action fails with a clear error naming the mismatch rather than silently doing the wrong thing.

**`format: NONE` means don't refresh anything.** If your field has no date portion at all - it's pure semver (`1.0.0`) or a plain counter (`10000`) - there is nothing in it for this action to legitimately touch: the whole value IS the version, and this action never modifies a version number, only a date stamp. With `NONE`, the action reads the field, writes it back completely unchanged, always reports `changed: false`, and never commits anything. It exists so you can still wire this action into the same workflow shape across every project, even one that doesn't use date-based versioning at all - the step just becomes a permanent no-op for that project instead of you having to leave it out.

`format: TIMESTAMP` is its own mode, not expressible in the Y/M/D/V template - it replaces the whole field with the current Unix timestamp (seconds since epoch), since a timestamp is one continuously-increasing integer, not separate calendar digit groups.

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

      - uses: MPHONlC/version-refresh@Version-0.0.3
        with:
          manifest_file: 'MyAddon.addon'
          field_name: 'AddOnVersion'
          format: 'YYMMDDVVV'
          git_name: 'YourGitName'
          git_email: 'your-email@example.com'
```

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `manifest_file` | Yes | - | Path to your manifest file (`.addon`, `.toc`, or any similar text manifest). |
| `field_name` | No | `AddOnVersion` | The field to refresh, matched as `## <field_name>: <value>`. WoW's `.toc` format, for example, uses `Version` instead. |
| `format` | No | `YYMMDDVVV` | Template describing the field's value shape - see above. `NONE` for a field with no date component, `TIMESTAMP` to refresh to the current Unix timestamp instead. |
| `git_name` | Yes | - | Git name to attribute the refresh commit to. |
| `git_email` | Yes | - | Git email to attribute the refresh commit to. |
| `skip_ci` | No | `true` | Appends `[skip ci]` to the commit message. Leave `true` if this runs from a push-triggered workflow, to avoid the commit re-triggering itself in a loop. |

## Outputs

| Output | Description |
|---|---|
| `changed` | `'true'` if the manifest was updated, `'false'` if it was already current (or `format` is `NONE`). |
| `old_version` | The field's value before this run. |
| `new_version` | The field's value after this run. |

## Requirements

- The calling job needs `permissions: contents: write`, since this action pushes directly.

> [!IMPORTANT]
> Without `permissions: contents: write` on the job, the commit/push step fails - this is the most common setup mistake with this action.

## License

MIT - see [LICENSE](LICENSE).
