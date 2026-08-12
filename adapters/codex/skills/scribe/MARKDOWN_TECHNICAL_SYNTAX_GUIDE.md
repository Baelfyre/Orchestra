# Markdown Technical Syntax Guide

Target the repository's declared renderer. CommonMark and GitHub-Flavored Markdown overlap, but tables, task lists, autolinks, footnotes, callouts, heading IDs, and raw HTML can differ.

## Stable Structure

- Use one H1 title and ordered heading levels. Do not use bold text as a substitute for structure.
- Surround lists, tables, and fenced code blocks with blank lines.
- Add a language identifier to executable or syntax examples. Keep commands and output in separate fences.
- Use inline code for identifiers, paths, flags, and short literals, not for emphasis.
- Use descriptive link text; avoid bare "click here" labels.

## Links and Anchors

Resolve a relative link from the directory of the containing Markdown file. Preserve path case for case-sensitive hosts. Percent-encode spaces only where the renderer requires it.

Heading fragments can change with punctuation, duplicate headings, Unicode, or renderer rules. Validate the generated anchor rather than guessing it. Explicit HTML anchors require portability and accessibility review.

## Tables and Accessibility

Use tables for compact comparisons, not long prose. Escape `|` inside cells, keep headers meaningful, and avoid merged-cell HTML. Provide surrounding explanation for screen-reader and narrow-screen users.

Images require useful alternative text when they convey information. Decorative images use empty alt text where the renderer supports it. Never use an image as the sole source of commands, data, or status.

## Safe Technical Examples

- Label placeholders such as `<host>` and never make them resemble real credentials.
- State working directory, shell/runtime, prerequisites, and expected result when material.
- Verify copy-paste commands against the documented revision.
- Mark pseudocode, abbreviated output, and unexecuted examples explicitly.

Rendering success does not verify the factual claim inside the document. Source-backed validation remains separate.
