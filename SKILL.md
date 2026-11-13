---
name: llm-wiki
description: "Builds and maintains a sourced markdown wiki: saves sources unchanged in raw/, compiles cited articles into wiki/, answers questions from it, and lints it for source fidelity. Use only for an explicit request about an LLM wiki: ingesting or adding a source, researching a topic into it, querying it, linting it, or creating one. Acts only on a wiki the project names or that already has a SCHEMA.md; never for general questions."
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check_evidence.py *)
---

# LLM Wiki

Build and maintain a knowledge base of sourced markdown pages. You manage two directories under the wiki root: `raw/` (immutable source material) and `wiki/` (compiled knowledge articles). Sources go into raw/, you compile them into wiki articles, and the wiki compounds over time. The human chooses sources, discusses what they mean, and asks questions; you fetch, summarize, cross-reference and file.

## Rules that always hold

- Act only on an existing wiki, or create one only when the human asks (see Wiki root).
- Never modify a file in raw/.
- Locate every number, date and quote in a linked raw file before writing it; drop a claim you cannot support.
- During an ingest, edit nothing in wiki/ before the Discuss step, unless running unattended.
- Mark interpretations `unreviewed` until the human has discussed them.
- Lint reports factual problems; it never fixes facts.

## Architecture

**Wiki root.** The directory that holds `SCHEMA.md`, `raw/` and `wiki/`. Use the wiki root the project's CLAUDE.md names. If it names none, use a directory in the project that already holds a `SCHEMA.md` beside `raw/` and `wiki/`; if there are several, ask which. If neither exists, this project has no wiki: do nothing beyond saying so and asking whether to create one (see Initialization). Never create one unasked. All paths below are relative to the wiki root.

This skill may be installed for every project, so it is the general workflow only. Everything particular to one wiki lives in that wiki's `SCHEMA.md`.

Three layers:

**raw/** — Immutable source material. You read, never modify. Organized by topic subdirectories (e.g., `raw/models/`).

**wiki/** — Compiled knowledge articles. You have full ownership, within the review rules below. Organized by topic subdirectories, one level only: `wiki/<topic>/<article>.md`. Contains two special files:
- `wiki/index.md` — Global index. One row per article, grouped by topic, with link + summary + Updated date.
- `wiki/log.md` — Append-only operation log.

**Schema** — This file sets the workflow rules. `SCHEMA.md` at the wiki root sets what is particular to this wiki: its domain, its topic directories, and the sections whose interpretations count as settled only after discussion with the human. Where the two conflict, `SCHEMA.md` wins.

Templates live in `references/` beside this file. Read the one you need for the exact format:

- [schema-template.md](references/schema-template.md): when creating a wiki.
- [raw-template.md](references/raw-template.md): when saving a source to raw/.
- [article-template.md](references/article-template.md): when writing an article or a Status block.
- [archive-template.md](references/archive-template.md): when archiving a query's answer.
- [index-template.md](references/index-template.md): when updating `wiki/index.md`.

### Orientation

Before any ingest, query, or lint in a session, read `SCHEMA.md`, `wiki/index.md`, and the last 30 lines of `wiki/log.md`. This prevents duplicate articles, missed cross-references, and repeated work.

### Initialization

Only when the human explicitly asks to create a wiki. Confirm the wiki root's location with them first, and suggest naming it in the project's CLAUDE.md. Create only what is missing; never overwrite existing files:

- `SCHEMA.md` — from `references/schema-template.md`. Ask the human what the wiki covers and which topics it starts with.
- `raw/` directory (with `.gitkeep`)
- `wiki/` directory (with `.gitkeep`)
- `wiki/index.md` — heading `# Knowledge Base Index`, empty body
- `wiki/log.md` — heading `# Wiki Log`, empty body

## The Grounding Invariant

Every load-bearing fact in wiki/ — numbers, dates, direct quotes — exists verbatim in the raw/ files linked by that article's Raw field. Compile *establishes* this invariant (locate before you write). Lint *checks* it: `scripts/check_evidence.py` greps the linked raws for the article's high-signal literals (suffixed or large numbers, decimals, ISO dates, longer quotes), including those in Status block explanations, and the locate-before-write rule covers the rest. Articles change, so every lint re-checks the whole wiki; it takes seconds.

The script is a backstop, not proof. It shows that a literal appears somewhere in an article's sources, not that the source says what the article claims about it. Support for each claim rests on the Source fidelity rule below, the paragraph source links, and the human's review.

## Confidence and Review

Every article, archive pages included, carries two metadata lines (see `references/article-template.md` and `references/archive-template.md`):

- **Confidence** — `high`, `medium` or `low`: how well the article's claims are supported. Use `high` only when the main claims are corroborated by more than one independent source. Single-source, fast-moving, or vendor-reported claims are `medium` at most. Claims resting on inference or on one weak source are `low`.
- **Review** — `unreviewed` or `discussed YYYY-MM-DD`. An article is `unreviewed` from the moment you write or materially change its interpretation (what it concludes, why it matters, what it suggests) until the human has discussed that interpretation with you. Facts copied faithfully from raw/ do not need review; judgments do.

Sections that `SCHEMA.md` names as discussion-only (for example, an article's relevance to the human's own work, or a synthesis page) may be created and revised as drafts at any time, provided the article is marked `unreviewed`. Their interpretations count as settled only after discussion, and are never presented as settled before it. Materially changing a discussed interpretation returns the article to `unreviewed`.

### Synthesis page

The wiki keeps one living synthesis page, `wiki/synthesis/current-understanding.md` unless `SCHEMA.md` names another: what the wiki currently understands across articles, what is disputed, and what is unanswered. Create it once the wiki holds articles on more than one subject, drawn from two or more different sources; one article citing two sources is not enough. It is an ordinary article in a `synthesis` topic directory, so the script checks it like any other. That directory exists only under wiki/, never under raw/, since the page has no sources of its own. Its Raw field lists the raw files behind the articles it draws on, its paragraphs carry source links, and it cross-references those articles. It is discussion-only: revise it as a draft whenever an ingest changes the picture, mark it `unreviewed`, and settle it only by discussion. Unlike an archive page, it is cascade-updated.

---

## Ingest

Fetch a source into raw/, then compile it into wiki/ — unless the source adds nothing new. Always fetch; whether to compile depends on the triage below.

### Fetch (raw/)

1. Get the source's original text. The grounding invariant is only as good as raw/: if raw/ holds a model's summary, lint compares your writing against a paraphrase and a wrong figure can pass. Prefer a direct download (`curl`, a site's raw or API endpoint, `gh` for GitHub), a tool that returns the page text unchanged, or text the human pastes. Web-reading tools that answer through a model return summaries, not originals. If one is all that reaches the source, you may save its output as `Capture: summary` with the tool's name, but only as a research lead: never compile factual claims from it. Get the original text (or ask the human to paste it) and save that as a separate, verbatim raw file before compiling. If nothing can reach the source, ask the human to paste it directly.

2. Pick a topic directory. Check existing `raw/` subdirectories and the topics in `SCHEMA.md` first; reuse one if the topic is close enough. Create a new subdirectory only for genuinely distinct topics, and add it to `SCHEMA.md`.

3. Save as `raw/<topic>/YYYY-MM-DD-descriptive-slug.md`.
   - Slug from source title, kebab-case, max 60 characters.
   - Published date unknown → omit the date prefix from the file name (e.g., `descriptive-slug.md`). The metadata Published field still appears; set it to `Unknown`.
   - If a file with the same name already exists, append a numeric suffix (e.g., `descriptive-slug-2.md`).
   - Include metadata header: source URL, collected date, published date, and capture (verbatim or summary).
   - Preserve original text. Clean formatting noise. Do not rewrite opinions.

   See `references/raw-template.md` for the exact format.

### Triage

After saving the raw file and before editing wiki/, search the full wiki with the source's key entities, aliases, synonyms and the claims it touches, then state the disposition:

- **New** — creates one or more new articles.
- **Update** — merges into existing article(s).
- **Disputed** — contradicts existing content; may combine with New or Update (see Compile for conflict annotation).
- **No material** — adds no knowledge beyond what the wiki already holds. Keep the raw file, log it (see Post-Ingest), and stop. Do not force an article out of a thin source.

New, Update, and Disputed may be combined. No material is exclusive.

Page thresholds:
- Create an article when an entity or concept is central to the source, or appears in two or more sources.
- Do not create an article for a passing mention; add it to an existing article or leave it in raw/.
- Split an article only when it covers distinct subjects that deserve their own articles; length alone is a lint report, not a reason.

### Discuss

Before editing wiki/, use the Triage search to list every article you will change, including those Cascade Updates below would touch, so the human approves the full scope. Then tell the human:
- the disposition and 3–5 key takeaways,
- which articles you will create or update, including cascade updates,
- anything the source contradicts or supersedes,
- what you take it to mean for the domain, marked as your interpretation,
- whether it changes the synthesis page, and how.

Wait for their response. They may redirect emphasis, correct your reading, or say the source is not worth compiling. If the planned change would touch 10 or more existing articles, confirm the scope explicitly.

Skip this step only when running unattended (a scheduled or batch job the human started). In that case, compile facts only, mark every touched article `Review: unreviewed`, and list the interpretations awaiting discussion in the log entry.

### Compile (wiki/)

Determine where the new content belongs:

- **Same core thesis as existing article** → Merge into that article. Add the new source to Sources/Raw. Update affected sections.
- **New concept** → Create a new article in the most relevant topic directory. Name the file after the concept, not the raw file.
- **Spans multiple topics** → Place in the most relevant directory. Add See Also cross-references to related articles elsewhere.

These are not mutually exclusive. A single source may warrant merging into one article while also creating a separate article for a distinct concept it introduces. In all cases, check for factual conflicts: if the new source contradicts existing content, mark the contested claims with a **Status: Disputed** block (see `references/article-template.md`). When the conflicting content lives in separate articles, mark both and cross-link them.

**Source fidelity.** Every factual claim — not only its numbers — must be supported by a linked raw file, with the same subject and the same context: a figure about one company, product, or user group never supports a claim about another. Every number, date, and direct quote must be located in the raw file (grep or read) *before* it is written; write the value exactly as found — if the source says 42K, write 42K, not 42,000. Derived values (sums, deltas, counts you computed) must show their components so each component is findable in raw. Do not put a prose claim's figures, dates or quotes in code formatting: the script skips code, so they would go unchecked. Real code examples may contain any values; review them separately against their source. If you cannot locate support for a claim, drop it. Do not restate it vaguely ("rapid growth" for an unfound "42%"): a vague claim without a source is still unsourced. Your own inferences belong only in sections marked as interpretation, never presented as fact.

**Paragraph sources.** In an article with more than one Raw file, end each paragraph of facts with links to the raw file or files supporting its claims, e.g. `([source](../../raw/topic/file.md); [source](../../raw/topic/other.md))`, so a reader can check any claim without searching every source. The script cannot match claims to sentences; these links let the human and lint do it.

Set Confidence for every touched article, and set Review to `unreviewed` wherever you wrote or changed an interpretation that the human has not discussed. When the Discuss step covered it, set `discussed` with today's date.

See `references/article-template.md` for article format. Key points:
- Sources field: author, organization, or publication name + date, semicolon-separated.
- Raw field: markdown links to raw/ files, semicolon-separated.
- Relative paths from `wiki/<topic>/` use `../../raw/<topic>/<file>.md` (two levels up to the wiki root).

### Cascade Updates

After the primary article, update the other articles approved in the Discuss step. Do not rely on the index alone: search the full wiki again for the source's key entities, aliases, and the claims it touches. If you find a materially affected non-archive article that was not approved, pause and confirm the added scope with the human before editing it; the 10-article confirmation applies to the total. When running unattended, list it in the log under `- Awaiting discussion:` instead of editing it. Each updated file gets its Updated date refreshed.

When the new source supersedes or contradicts an existing claim, keep the old claim for the record but mark it with a Status block (see `references/article-template.md`): **Outdated** when something newer replaces it, **Disputed** when sources disagree. Never silently rewrite history.

Archive pages are never cascade-updated (they are point-in-time snapshots).

### Post-Ingest

Update `wiki/index.md`: add or update entries for every touched article. When adding a new topic section, include a one-line description. The Updated date reflects when the article's knowledge content last changed, not the file system timestamp. See `references/index-template.md` for format.

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] ingest | <primary article title>
- Disposition: <New; Update; Disputed>
- Raw: <raw file path>
- Updated: <cascade-updated article title>
- Awaiting discussion: <interpretation not yet discussed>
```

Omit `- Updated:` lines when no cascade updates occur, and `- Awaiting discussion:` lines when nothing awaits. For No material, log and stop. Use a wiki-root-relative raw path (for example, `raw/topic/file.md`):

```
## [YYYY-MM-DD] ingest | no material: <wiki-root-relative raw file path>
- Disposition: No material
```

The exact no-material heading is the machine-readable inventory key; the Disposition line remains required for a complete human-readable log entry.

Finally, list for the human every file created or updated.

### Research (multi-source ingest)

Use only when the human explicitly asks to research a topic or gather sources into the wiki. Ordinary knowledge questions go to Query, which never writes files.

1. Split the topic into a few angles. For each, search with a wide net — official names, abbreviations, and synonyms, not just the literal keywords.
2. For any core claim you expect to conclude, deliberately search the opposing side: failures, criticism, failed replications.
3. Save selected sources to raw/ as usual. Searching may run in parallel; compilation must not — compile one source at a time, because index.md, log.md, and cascade updates are shared state.
4. Hold one Discuss step for the whole batch before compiling, rather than one per source.

---

## Query

Search the wiki and answer questions. Examples of triggers:
- "What do we know about X?"
- "Summarize everything related to Y"
- "Compare A and B based on the wiki"

### Steps

1. Read `wiki/index.md` to locate candidate articles, then full-text search wiki/ with the topic's key terms *and their synonyms*. Never claim the wiki has no relevant content until both the index and the full-text search come back empty — and say that you searched.
2. Read the articles you found and synthesize an answer. Archive pages are snapshots that cascade updates never touch: answer from current articles, and cite an archive page only as what was concluded on its Archived date.
3. Prefer wiki content over your own training knowledge. Cite sources with markdown links: `[Article Title](wiki/topic/article.md)` (wiki-root-relative paths for in-conversation citations; within wiki/ files, use paths relative to the current file).
4. Say when an answer rests on `low` confidence or `unreviewed` articles.
5. Output the answer in the conversation. Do not write files unless asked.

### Archiving

When the human explicitly asks to archive or save the answer to the wiki:

1. Write the answer as a new wiki page. See `references/archive-template.md`. When converting conversation citations to the archive page, rewrite wiki-root-relative paths (e.g., `wiki/topic/article.md`) to file-relative paths (e.g., `../topic/article.md` or `article.md` for same-directory).
   - Cites: markdown links to the wiki articles cited in the answer.
   - No Raw field (content does not come from raw/). The script does not check archive pages, so check the answer yourself before saving: every factual claim must be supported by an article it cites, with the same subject and context. Drop facts you added from outside the wiki, or ingest their source first. Conclusions that go beyond the cited articles go under a heading that marks them as interpretation.
   - Confidence: judged on the answer's central claims, no higher than the lowest Confidence among the articles those claims rest on. A peripheral claim resting on a weaker article does not lower the page; mark it in place instead, e.g. "(low confidence)".
   - Review: `unreviewed`, unless the human discussed the answer's conclusions in this conversation; then `discussed` with today's date. An answer that draws conclusions across articles is discussion-only, like the synthesis page, and the rules in `SCHEMA.md` for such pages apply to it.
   - File name reflects the query topic, e.g., `transformer-architectures-overview.md`.
   - Place in the most relevant topic directory.
2. Always create a new page. Never merge into existing articles (archive content is a synthesized answer, not raw material).
3. Update `wiki/index.md`. Prefix the Summary with `[Archived]`.
4. Append to `wiki/log.md`:
   ```
   ## [YYYY-MM-DD] query | Archived: <page title>
   ```

---

## Lint

Quality checks on the wiki. Three categories with different authority levels.

### Safe Fixes (auto-fix)

Fix these automatically:

**Index consistency** — compare `wiki/index.md` against actual wiki/ files (excluding index.md and log.md):
- File exists but missing from index → add entry with `(no summary)` placeholder. For Updated, use the article's metadata Updated date if present (for archive pages, the Archived date); otherwise fall back to file's last modified date.
- Index entry points to nonexistent file → mark as `[MISSING]` in the index. Do not delete the entry; let the human decide.
- Index entry's Updated differs from the article's metadata Updated (or Archived, for archive pages) → update the index entry to match the article.

**Internal links** — for every markdown link in wiki/ article files (body text, and the Sources or Cites field), excluding Raw field links and paragraph source links, and any other link into raw/ (all validated by Raw references below), excluding See Also section links (handled by the See Also rule below), and excluding index.md/log.md (handled above):
- Target does not exist → search wiki/ for a file with the same name elsewhere.
  - Exactly one match → fix the path.
  - Zero or multiple matches → report to the human.

**Raw references** — every link in a Raw field or a paragraph source link must point to an existing raw/ file:
- Target does not exist → search raw/ for a file with the same name elsewhere.
  - Exactly one match whose `Source:` line matches the source the article cites (by URL, or by author and date in its Sources field) → fix the path.
  - Otherwise → report to the human. A file with the same name is not necessarily the same evidence.

**See Also** — within each topic directory:
- Target of a See Also link does not exist → search wiki/ for a file with the same name elsewhere.
  - Exactly one match → fix the path.
  - Zero matches → remove the link (a dead cross-reference is not load-bearing).
  - Multiple matches → report to the human.

### Mechanical Reports (no fixes)

Run `python3 ${CLAUDE_SKILL_DIR}/scripts/check_evidence.py <wiki-root>` (`${CLAUDE_SKILL_DIR}` is the directory holding this file), optionally followed by wiki-root-relative article paths to limit scope. It needs Python 3.9 or later and only the standard library; if `python3` is older, use `uv run --no-project python` or any newer interpreter. Default scope is the whole wiki; the script is fast. Report findings; never auto-fix facts.

**Source fidelity** — reported suspects are candidates, not verdicts: derived values and product names may appear. Judge each against the raw context and report only real mismatches.

**Evidence errors** — articles the script cannot verify (missing Raw field, unresolvable Raw links, or Raw links escaping `raw/`). These always need a decision, not a fix from the script.

**Unreferenced raw files** — files logged with a No material disposition are excluded; everything else is a genuine backlog reminder.

### Judgment Reports (no fixes)

These rely on your judgment. Report findings without auto-fixing:

- Factual contradictions across articles
- Outdated claims superseded by newer sources but still presented without a Status block
- Missing conflict annotations where sources disagree
- Obviously missing cross-references between related articles (suggest them; do not add silently)
- Malformed Status blocks (Outdated missing its date, or either block missing its explanation; format reference: `references/article-template.md`)
- Orphan pages with no inbound links from other wiki articles
- Missing cross-topic references
- Concepts frequently mentioned but lacking a dedicated page
- Data gaps a web search could fill, and new questions to investigate or sources to look for
- A synthesis page that no longer reflects the articles it draws on
- Archive pages whose cited articles have been substantially updated since archival
- Archive pages stating facts their cited articles do not support, or conclusions not marked as interpretation
- Articles missing Confidence or Review, articles marked `high` that cite a single source, and any article whose Raw field or paragraph source links point to a raw file with `Capture: summary`
- Articles with more than one Raw file whose paragraphs of facts lack source links
- Claims whose linked source is about a different subject or context than the claim
- Articles marked `unreviewed`, oldest first: the human's discussion backlog
- Articles longer than about 200 lines: candidates for splitting, if they cover distinct subjects
- Fast-moving articles (as `SCHEMA.md` defines them) not updated in 90 days

### Post-Lint

Append to `wiki/log.md`:

```
## [YYYY-MM-DD] lint | <N> issues found, <M> auto-fixed
```

---

## Conventions

- Standard markdown with relative links throughout.
- wiki/ supports one level of topic subdirectories only. No deeper nesting.
- Today's date for log entries, Collected dates, and Archived dates. Updated dates reflect when the article's knowledge content last changed. Published dates come from the source (use `Unknown` when unavailable).
- Inside wiki/ files, all markdown links use paths relative to the current file. In conversation output, use wiki-root-relative paths (e.g., `wiki/topic/article.md`).
- Ingest updates both `wiki/index.md` and `wiki/log.md` (a No material ingest updates only the log). Archive (from Query) updates both. Lint updates `wiki/log.md` (and `wiki/index.md` only when auto-fixing index entries). Plain queries do not write any files.
