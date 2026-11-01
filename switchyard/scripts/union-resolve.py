"""Resolve append-only merge conflicts by keeping both sides, upstream first.

Use on append-only files. Consolidate Unreleased CHANGELOG subsections.
Usage: python3 union-resolve.py <file>...
"""

import re
import sys


def union(text):
    output, upstream, incoming = [], [], []
    state = "outside"
    for line in text.splitlines(keepends=True):
        if line.startswith("<<<<<<< ") and state == "outside":
            state = "upstream"
        elif line == "=======\n" and state == "upstream":
            state = "incoming"
        elif line.startswith(">>>>>>> ") and state == "incoming":
            output.append("".join(upstream).rstrip("\n") + "\n\n" + "".join(incoming))
            upstream, incoming = [], []
            state = "outside"
        elif re.match(r"^(?:<{7}|={7}|>{7}|\|{7})(?:\s|$)", line):
            raise ValueError("a conflict is not a plain two-sided append")
        else:
            {"outside": output, "upstream": upstream, "incoming": incoming}[state].append(line)
    if state != "outside":
        raise ValueError("a conflict is not a plain two-sided append")
    return "".join(output)


def changelog(text):
    heading = re.search(r"^## \[Unreleased\][^\n]*\n", text, re.M)
    if not heading:
        return text
    next_section = re.search(r"^## ", text[heading.end():], re.M)
    end = heading.end() + next_section.start() if next_section else len(text)
    section = text[heading.end():end]
    headings = list(re.finditer(r"^### ([^\n]+)\n", section, re.M))
    if not headings:
        return text
    groups = {}
    for index, match in enumerate(headings):
        stop = headings[index + 1].start() if index + 1 < len(headings) else len(section)
        groups.setdefault(match.group(1), []).append(section[match.end():stop].strip("\n"))
    known = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")
    order = [name for name in known if name in groups]
    order.extend(name for name in groups if name not in known)
    merged = section[:headings[0].start()]
    for name in order:
        body = "\n\n".join(part for part in groups[name] if part)
        merged += f"### {name}\n\n" + (body + "\n\n" if body else "")
    return text[:heading.end()] + merged + text[end:]


if __name__ == "__main__":
    for path in sys.argv[1:]:
        with open(path) as handle:
            text = handle.read()
        try:
            text = changelog(union(text))
        except ValueError as exc:
            sys.exit(f"{path}: {exc}")
        with open(path, "w") as handle:
            handle.write(text)
