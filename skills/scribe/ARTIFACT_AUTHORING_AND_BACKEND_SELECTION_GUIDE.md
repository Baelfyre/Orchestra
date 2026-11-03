# Artifact Authoring and Backend Selection Guide

Use this guide when specifying or creating a Word document, spreadsheet, or presentation. It provides a working checklist, not a runtime schema or an application support registry.

Scribe owns the documented request, source and citation traceability, and capability-evidence record. Cloak owns visual hierarchy, brand presentation, and accessibility guidance. Conductor routes material cross-specialist work. Do not use this guide to grant implementation, cloud, provider, publication, or release authority.

## 1. Record the artifact request

Capture these fields in the task or an existing project document. Keep the spec proportionate to the artifact; do not create a machine contract just to fill out this list.

| Field | Record |
|---|---|
| Goal and audience | What the artifact should help the audience understand or do, who will use it, intended presentation duration or page/slide/word budget, and any institution, course, or rubric requirements. |
| Source and output format | Source content/file format, required deliverable format, filename, location, and whether an editable source is required in addition to a fixed rendering. |
| Target application and availability | Exact product/version, desktop or web surface, platform, local tool availability, account/tenant availability when relevant, and every second application that must open the result. |
| Required features | Separate mandatory from optional features, including formulas, charts, notes, citations, comments, animations, and editability. |
| Content and sources | Supplied text/data, source identities and revisions, citation style, and the required location of references. |
| Narrative and structure | The outline or story arc, artifact-family structure, sequence, and the content/evidence expected in each section, sheet, or slide. |
| Template and visual requirements | Template identity and revision (or `NONE`), page/sheet/slide organization, approved logo, theme, colors, fonts, and any supplied usage rules. |
| Accessibility requirements | Reading order, headings, table structure, text alternatives, contrast, keyboard or assistive-technology checks, as applicable. |
| Conversion risks | Expected changes to editability, layout, formulas, charts, notes, citations, accessibility structure, fonts, animation, or metadata on import/export/round-trip. |
| Execution boundary | Local or cloud authoring, permitted tools, observed Google account/OAuth or tenant authorization when relevant, and whether upload, conversion, sharing, or other provider action is separately authorized. |
| Validation and confirmation | Required checks and validation status for this output; exact target-app evidence; and any user confirmation needed for a format substitution, known gap, conversion, or cloud operation. |

### Document-family structure

- **Documents:** Provide a document outline with section and subsection purpose. For a narrative or argument, state the story arc from the problem or question through evidence and reasoning to the conclusion. Place claims and citations in the relevant sections.
- **Spreadsheets:** Provide a workbook and sheet map. For each sheet, identify its purpose and distinguish source/input data, formulas or transformations, outputs/summaries, checks/reconciliation, units, and required notes or charts. Keep calculation requirements explicit.
- **Presentations:** Provide the narrative/story arc and slide sequence. For every slide, state its purpose, key message, supporting evidence/data, and intended visual. Supply substantive speaker notes that explain context, reasoning, transitions, caveats, or source detail; notes must add useful information and must not merely repeat the slide text.

Name note types instead of saying only “include notes”: Word footnotes or endnotes, spreadsheet cell notes or comments, and slide speaker notes are different features. State whether citations belong inline, in footnotes, in a bibliography, in cell notes, or in speaker notes. Keep essential facts and citations available in the artifact's normal reading flow; speaker notes alone do not make slide content accessible to the audience.

## 2. Match a deliverable profile

These profiles make the target explicit. They are request categories, not claims that a local backend, cloud account, or exporter is available.

| Profile | Required target details |
|---|---|
| PowerPoint desktop presentation | `.pptx`, PowerPoint desktop version/platform, slide size, template/theme identity, and whether presenter notes, animations, and editable objects are mandatory. |
| PowerPoint for the web presentation | `.pptx`, browser and Microsoft 365 surface/version where known, tenant/tool availability, and the required web editing/rendering features. Verify this profile in the web app separately from desktop PowerPoint. |
| PDF presentation | `.pdf`, page size/orientation, fixed-layout expectations, whether notes/comments are included, and whether a separate editable source is required. |
| Markdown presentation | `.md`, slide-separator convention, exact renderer/theme/version, asset paths, and whether rendered HTML/PDF is also required. The Markdown source and its rendered deck are separate deliverables. |
| PDF document | `.pdf`, page size, selectable/searchable text expectation, links, reading structure/tags, and whether an editable source is also required. |
| Markdown document | `.md`, CommonMark/GFM or other named dialect, renderer/version when rendering matters, and any required image, table, citation, or bibliography behavior. |
| LaTeX document | `.tex`, document class/revision, compiler/engine, required packages, bibliography tool, fonts, and expected compiled output. Validate the source and compiled result in the specified toolchain. |
| OpenDocument text document | `.odt`, exact Writer/OpenOffice/LibreOffice product and version, and required structure, notes, and editing features. |
| OpenDocument spreadsheet | `.ods`, exact Calc/OpenOffice/LibreOffice product and version, required formulas, charts, notes, and editing features. |
| OpenDocument presentation | `.odp`, exact Impress/OpenOffice/LibreOffice product and version, slide sequence, speaker notes, and required editing features. |

For every profile, record the source format, output format, template identity, conversion risks, local tool availability, and current validation status before selecting a backend. If a required environment is absent or unknown, record `UNVERIFIED`; do not select it by assumption.

## 3. Select a backend by required features

Check local tool availability before comparing backend features. Record the exact application/backend and version that can actually be used; an installed application, web surface, account, or authorization that has not been observed is not an available candidate. For Google cloud work, an appropriate account/tenant and explicit authorization for the requested operation are separate prerequisites. Do not connect or mutate cloud resources to discover capability.

Compare each available candidate against each required feature. Record product/backend identity and version, output format, feature status, validation status for the current artifact, and evidence in separate columns. This lightweight table is documentation only; it does not introduce a machine schema.

| Status | Meaning | Selection rule |
|---|---|---|
| `SUPPORTED` | Current, backend-specific evidence shows the required feature is available in the named version and configuration. | Eligible for a mandatory feature, subject to output validation. |
| `PARTIAL` | Evidence shows only part of the requirement works, or states a concrete limitation. | Accept only when the gap affects optional scope and the user accepts it; otherwise select another backend or stop. |
| `UNSUPPORTED` | Reliable evidence shows the backend cannot provide or preserve the required feature. | Do not select it for that mandatory feature. Do not silently drop, flatten, or approximate the requirement. |
| `UNVERIFIED` | Product/version/configuration is unknown, or evidence is absent, stale, indirect, or does not cover the exact feature. | Treat as unknown, not supported. Obtain current evidence or choose a candidate with verified coverage. |

**Feature support, evidence, and output validation are separate.** For each support status, record the evidence source, revision or product version, date checked, exact feature examined, environment, and result. Evidence can be current product documentation, a representative local artifact opened in the target app, or both. Separately state which checks passed, failed, were not run, or remain unverified for this output. A backend capability statement does not prove that a particular output is correct; a successful check of one output does not prove general product compatibility.

Choose a backend only when every mandatory feature is `SUPPORTED` by evidence suitable for the claim. A `PARTIAL` mandatory feature blocks selection unless the requirement itself is revised and the user accepts that change. An `UNSUPPORTED` or `UNVERIFIED` feature never becomes supported by choosing a different filename extension. Do not invent a broad compatibility matrix when versions and formats change.

Use this fallback order and keep each change explicit:

1. **Native target format** for the application the user will edit in.
2. **Qualified interchange format** only when the exact import/export path has `SUPPORTED` evidence for all mandatory features in the target application.
3. **User-approved fixed format** such as PDF only when fixed layout meets the task and the user explicitly accepts reduced editing or interaction.
4. **Return to the specification** with the unsupported or unverified requirement if none of the above meets it. Do not silently choose an easier format.

Before using an interchange or fixed format that changes editability, layout, structure, notes, or calculations, show the specific conversion risk and get the user's confirmation of the exact output and accepted limitation. Record that confirmation. Without it, pause before generating the substituted output.

## 4. Preserve editable content and source evidence

- Preserve text, tables, formulas, charts, diagrams, labels, notes, citations, and accessible structure as editable/native elements where the requested format supports them.
- Do not rasterize text, tables, charts, diagrams, or other editable content to work around a backend limitation. That is a lossy substitution, not feature support. If no backend can meet a mandatory editable feature, report the gap and stop for a decision.
- Use an image as an image when the supplied source is raster or the request explicitly accepts decorative raster content. Do not use a rendered image in place of required editable content.
- Keep citations tied to the claim or data they support, preserve source URLs and revision/date information when available, and distinguish factual source evidence from a design reference.
- Use only supplied or explicitly approved brand assets and instructions. Do not fabricate a logo, claim brand approval, or decide reuse rights from a citation; route legal or rights questions through Conductor to The Governor.
- Record missing sources and unresolved requirements rather than filling them with plausible substitutes.

## 5. Apply target-application constraints

File extensions identify formats; they do not establish feature parity. Re-check the current documentation for the exact application and version before making a support claim.

### Microsoft Word and Excel

When Word or Excel is the target, specify the actual deliverable format (`.docx`, `.xlsx`, or another required format) and validate it in the target application. Microsoft documents that converting between formats may not transfer all formatting, data, or features. `.xlsx` cannot store VBA macro code; macro-enabled workbooks use `.xlsm`. Do not silently substitute an image, PDF, or different workbook format for an editable deliverable. See [Microsoft file formats](https://support.microsoft.com/en-us/office/collab-files/learn-about-file-formats) and [Excel supported formats](https://support.microsoft.com/en-us/excel/file-formats-that-are-supported-in-excel).

### Apache OpenOffice and LibreOffice

Treat Apache OpenOffice and LibreOffice as separate target products and record which one and which version is required. Do not infer identical behavior because both use OpenDocument formats or can open some Microsoft Office files. Prefer the requested native format when the target is fixed; if an OOXML file must cross applications, verify the required formatting, data, formulas, charts, notes, and editability in the exact target. See the [Apache OpenOffice compatibility FAQ](https://wiki.openoffice.org/wiki/Documentation/FAQ/General/Is_OpenOffice.org_compatible_with_MS_Office_and_StarOffice_file_formats%3F) and [LibreOffice's Office-format guidance](https://help.libreoffice.org/latest/en-US/text/shared/guide/ms_user.html?DbPAR=BASE&System=WIN).

The Apache OpenOffice FAQ is a legacy compatibility reference, not a current feature-coverage table. Treat current support as `UNVERIFIED` until evidence for the exact target version is available.

### Apple Keynote

Keynote can open and edit PowerPoint `.pptx` presentations and export PowerPoint copies, but a `.pptx` is not a native `.key` file. If the requested deliverable is `.key`, verify it in Keynote itself. If `.pptx` must be exchanged with Keynote, open and inspect that exchanged file in the exact Keynote version and check required layout, fonts, builds, notes, and accessibility features. See [Apple's Keynote file compatibility guidance](https://support.apple.com/en-sg/guide/keynote/tan72232b56/mac) and [conversion formats](https://support.apple.com/en-gb/105050).

### Google Docs, Sheets, Slides, and Drive

Separate local artifact authoring from editing or storing a file in Google's cloud. Google editors can work with Office files in their original formats; converting creates a copy and is needed for some Google-specific features. Do not infer that a feature survives import, conversion, or round-trip save. Uploading, creating, converting, sharing, changing permissions, or deleting a Drive file is a provider operation; it requires its own explicit authorization and must not be triggered solely because Google is named as a target. See [Google's Office-file guidance](https://support.google.com/drive/answer/9406611?hl=en) and [Excel-to-Sheets feature differences](https://support.google.com/docs/answer/9331278?hl=en).

If Google is a target, compare native Docs/Sheets/Slides output separately from importing or editing an Office file. Confirm that the required Google account/tenant, authentication or OAuth authorization, and tool surface are actually available before considering a cloud backend. Validate a native Google artifact in its named editor; validate Office import and round-trip behavior as a separate path. If account or authorization state is unknown, classify that candidate `UNVERIFIED`. Do not create, upload, convert, or change a cloud file as a capability probe.

### Excel and Calc calculations and charts

For an Excel or Calc workbook, enumerate required formulas/functions, calculation settings, dates/locales, external links, macro requirements, charts, and chart data ranges. Check formulas and charts in the exact target engine after opening and recalculation; file-package structure, cached values, and a screenshot do not prove calculation correctness. Compare import and round-trip results in each requested engine. If any required formula or chart behavior is missing or uncertain, record it as `PARTIAL`, `UNSUPPORTED`, or `UNVERIFIED`; do not flatten a chart or replace a formula with a fixed value without explicit user acceptance.

These vendor links are starting points for current evidence, not permanent compatibility guarantees. Confirm current application, account/admin, version, and format details before applying them. This guide was checked against the linked primary product documentation on 2026-11-04.

## 6. Handoff and report

Give implementation and review specialists the accepted request, required feature list, candidate/backend table, evidence references, approved brand/source assets, and unresolved items. For page, sheet, or slide visual structure and accessibility, route the presentation handoff to Cloak and use [Cloak's artifact visual/accessibility guide](https://github.com/Baelfyre/Orchestra/blob/main/skills/cloak/ARTIFACT_VISUAL_ACCESSIBILITY_GUIDE.md). Do not ask Cloak to infer backend capability from appearance.

When reporting, state the selected product/backend and format, each unresolved or partial mandatory feature, evidence used, output checks run, target application/version actually opened, and checks not run. Keep generated artifact correctness, backend support, visual review, accessibility evidence, and cloud-operation authorization as separate claims.
