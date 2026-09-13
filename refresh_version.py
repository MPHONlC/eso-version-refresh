import os
import re
import sys
import time
import argparse
from datetime import date


def parse_format(fmt):
    if not fmt or fmt.upper() == 'NONE':
        return None

    runs = []
    i = 0
    while i < len(fmt):
        ch = fmt[i]
        j = i
        while j < len(fmt) and fmt[j] == ch:
            j += 1
        runs.append((ch, j - i))
        i = j

    date_runs = [(ch, w) for ch, w in runs if ch in 'YMD']
    if not date_runs:
        return None

    seen = [ch for ch, _ in date_runs]
    if len(seen) != len(set(seen)):
        raise ValueError(f"format '{fmt}' repeats a date component in more than one place - Y/M/D must each appear as a single contiguous run")

    return date_runs


def find_date_span(fmt, date_runs):
    idx = 0
    positions = []
    for ch, w in date_runs:
        m = re.compile(re.escape(ch) + '{' + str(w) + '}').search(fmt, idx)
        if not m:
            raise ValueError(f"could not locate '{ch}'*{w} in format '{fmt}' - internal error")
        positions.append((m.start(), m.end()))
        idx = m.end()
    start = positions[0][0]
    end = positions[-1][1]
    if end - start != sum(w for _, w in date_runs):
        raise ValueError(f"format '{fmt}' has its Y/M/D digits scattered non-contiguously - not supported, keep the date block together")
    return start, end


def validate_literals(fmt, value):
    if len(fmt) != len(value):
        raise ValueError(f"manifest value '{value}' is {len(value)} characters, but format '{fmt}' expects {len(fmt)} - format doesn't match the real value")
    for i, ch in enumerate(fmt):
        if ch not in 'YMDV' and value[i] != ch:
            raise ValueError(f"format '{fmt}' expects literal '{ch}' at position {i}, but the manifest value '{value}' has '{value[i]}' there")


def build_new_date_block(date_runs):
    today = date.today()
    parts = []
    for ch, width in date_runs:
        if ch == 'Y':
            y = today.year % (10 ** width)
            parts.append(str(y).zfill(width))
        elif ch == 'M':
            parts.append(str(today.month).zfill(width))
        elif ch == 'D':
            parts.append(str(today.day).zfill(width))
    return ''.join(parts)


def refresh(fmt, current_value):
    if not fmt or fmt.upper() == 'NONE':
        return current_value, False

    if fmt.upper() == 'TIMESTAMP':
        new_value = str(int(time.time()))
        return new_value, new_value != current_value

    date_runs = parse_format(fmt)
    validate_literals(fmt, current_value)
    if date_runs is None:
        return current_value, False

    start, end = find_date_span(fmt, date_runs)
    new_block = build_new_date_block(date_runs)
    new_value = current_value[:start] + new_block + current_value[end:]
    return new_value, new_value != current_value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest-file', required=True)
    parser.add_argument('--field-name', default='AddOnVersion')
    parser.add_argument('--format', dest='fmt', default='YYMMDDVVV')
    args = parser.parse_args()

    try:
        with open(args.manifest_file) as f:
            text = f.read()
    except FileNotFoundError:
        print(f"::error::Could not read {args.manifest_file}")
        sys.exit(1)

    field_re = re.compile(r'^(## ' + re.escape(args.field_name) + r':\s*)(\S+)', re.M)
    m = field_re.search(text)
    if not m:
        print(f"::error::No '## {args.field_name}:' field found in {args.manifest_file}")
        sys.exit(1)
    current_value = m.group(2)

    try:
        new_value, changed = refresh(args.fmt, current_value)
    except ValueError as e:
        print(f"::error::{e}")
        sys.exit(1)

    print(f"Field: {args.field_name}")
    print(f"Format: {args.fmt}")
    print(f"Current value: {current_value}")
    print(f"New value:     {new_value}")

    if changed:
        new_text = text[:m.start(2)] + new_value + text[m.end(2):]
        with open(args.manifest_file, 'w') as f:
            f.write(new_text)

    print(f"changed={'true' if changed else 'false'}")

    output_path = os.environ.get('GITHUB_OUTPUT')
    if output_path:
        with open(output_path, 'a') as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
            f.write(f"old={current_value}\n")
            f.write(f"new={new_value}\n")


if __name__ == '__main__':
    main()
