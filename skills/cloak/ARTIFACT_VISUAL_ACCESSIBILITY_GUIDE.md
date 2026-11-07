<!-- @codebase_provenance_JEO -->
<!-- @codebase_rights_JEO -->

# Artifact Visual and Accessibility Guide

Use this guide when designing or reviewing the visible structure of a generated document, spreadsheet, or presentation. It extends Cloak's existing accessibility and evidence practices to content artifacts; it does not change the UIEF-4 `UIFidelityHandoff` contract for interactive software interfaces.

Consume the accepted artifact request and backend evidence from Scribe. Cloak owns visible hierarchy, layout, approved visual language, and accessibility requirements. It does not determine whether an exporter supports a format, select a provider, implement an exporter, or authorize cloud operations. Route backend support gaps back through Conductor to the owning specialist or source.

## Visual handoff

Record the target application and format, intended audience, required structure, approved brand references, visible content hierarchy, note and citation placement, accessibility needs, and unresolved items. State what must be preserved, what may adapt, and what must not change.

Capture physical layout requirements before arranging content: page or slide dimensions, orientation, margins, print area, slide size, sheet scaling, and any required headers or footers. Record template identity, theme, fonts, fallback fonts, and renderer/application versions. Specify whether wrapping, page breaks, row/column sizing, and slide composition may adapt or must remain fixed.

- Use only supplied or approved logos, colors, fonts, templates, and brand wording. Mark missing brand inputs instead of inventing them.
- Keep headings, page hierarchy, sheet organization, slide titles, tables, charts, labels, citations, and notes readable and consistent with the requested use.
- Use the specified theme and fonts where available; document substitutions. Check predictable wrapping, clipping, page/slide breaks, print areas, sheet scaling, and chart layout in the target application's actual rendering.
- Preserve data meaning, chart values, units, scales, and legends. A visual treatment must not imply unsupported conclusions or obscure the underlying values.
- Identify where each note type belongs: footnote/endnote, cell note/comment, visible citation, bibliography, or speaker note. Do not move required material into a location that the requested audience cannot access.
- Name assets and source material actually reviewed. Keep confirmed design evidence, missing inputs, and assumptions distinct.

## Editability and fidelity

Keep text, tables, charts, diagrams, labels, and citations as editable/native content when the request requires an editable artifact. Do not rasterize or flatten editable content as a workaround for an unsupported feature. A PDF or image can be a review copy when requested; it does not replace an editable source deliverable unless the user accepts that format.

Raster imagery is appropriate for supplied raster photographs or explicitly accepted decorative artwork. It is not appropriate as a substitute for text, charts, tables, diagrams, or accessibility structure. When the selected backend cannot preserve a required object, mark that gap and return it to Scribe for a `PARTIAL`, `UNSUPPORTED`, or `UNVERIFIED` disposition.

Do not promise that an Office-format file will look or behave identically in Word, Excel, OpenOffice, LibreOffice, Keynote, or Google editors. Use the target-application evidence in the accepted backend record; an extension or package inspection alone does not establish visual fidelity.

## Accessibility review

Review the artifact in the context of its target application and intended use:

- Keep heading levels, reading order, table headers, worksheet names, chart titles, and slide order meaningful.
- Provide useful text alternatives for informative images, charts, and icons; preserve data labels or a text/table alternative when a chart carries important information.
- Do not use color as the only way to distinguish categories, status, or meaning. Check contrast, text scaling, and legibility at the normal viewing size.
- Keep instructions, citations, labels, units, footnotes, and speaker notes associated with the right content and in a logical reading order.
- Check keyboard access and assistive-technology behavior in the target application when those checks are in scope. State when they were not run.
- Treat an automated checker, file-package inspection, or static source review as supporting evidence only. Do not claim accessibility conformance or a rendered pass without the relevant evidence.

## Review and handoff

Open the final artifact in the named target application and inspect the actual content when that application is available. Check page or slide dimensions and setup, line wrapping, font substitution, clipped content, table/chart layout, formulas or visible values, note placement, citation links, brand assets, and editability. Reopen a saved copy when round-trip editing is required. Capture screenshots of the rendered target view with the application/version and artifact identity recorded; include all pages/slides or clearly identify sampled sheets/regions. Treat screenshots as visual evidence only, not as the editable source or proof of calculations/accessibility. If the application, screenshot, or assistive technology is unavailable, report the check as `NOT_RUN` or `UNVERIFIED`; do not replace it with a package-only claim.

For a review handoff, state:

- the request and target application/version;
- the visual hierarchy and structure reviewed;
- brand, source, citation, note, and accessibility requirements;
- the exact artifact or rendered view reviewed;
- confirmed findings, missing evidence, assumptions, and unresolved backend gaps;
- checks run and not run.

The existing [UI Fidelity Handoff Guide](UI_FIDELITY_HANDOFF_GUIDE.md) remains specific to software UI implementation. Do not apply its machine-contract fields to office documents, spreadsheets, or slide decks.

## Primary product references

Use current official product documentation to check changing file-format behavior. These links were reviewed on 2026-11-04:

- [Microsoft Office file-format guidance](https://support.microsoft.com/en-us/office/collab-files/learn-about-file-formats)
- [Apache OpenOffice compatibility FAQ](https://wiki.openoffice.org/wiki/Documentation/FAQ/General/Is_OpenOffice.org_compatible_with_MS_Office_and_StarOffice_file_formats%3F)
- [LibreOffice Office-format guidance](https://help.libreoffice.org/latest/en-US/text/shared/guide/ms_user.html?DbPAR=BASE&System=WIN)
- [Apple Keynote file compatibility](https://support.apple.com/en-sg/guide/keynote/tan72232b56/mac)
- [Google Drive Office-file guidance](https://support.google.com/drive/answer/9406611?hl=en)
