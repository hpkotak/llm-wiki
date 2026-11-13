# llm-wiki

A Claude Code skill for keeping a knowledge base of sourced markdown pages, maintained by the agent and reviewed by a human. It implements [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), and is a fork of [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki). Compared with upstream, it adds per-claim sourcing rules, a discussion with the human before compiled wiki articles are written, confidence and review markers, a per-wiki `SCHEMA.md`, and it stays inactive in projects that have no wiki.

The agent saves each source unchanged in `raw/`, compiles what it says into articles in `wiki/`, and keeps an index and a log. Every claim in an article must be supported by a linked source. `scripts/check_evidence.py` checks the mechanical part: that the article's suffixed or large numbers, decimals, ISO dates and longer quotes appear word for word in its sources. Small plain integers, other forms and anything written as code are out of its scope, as its docstring lists, and it does not check archived answers. It cannot tell whether a source says what the article claims about it; paragraph source links and the human's review cover that. Interpretations wait for discussion with the human and are marked until they have had it.

Known limitation: the script does not search code blocks inside saved sources, so a genuine figure that appears only there is flagged as a suspect. Upstream [PR #8](https://github.com/Astro-Han/karpathy-llm-wiki/pull/8) proposes a fix.

Maintained for my own use and shared as is. Issues and pull requests may not get a response; fork freely.

## Use

Clone it into Claude Code's skills folder, which makes it available in every project:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/hpkotak/llm-wiki.git ~/.claude/skills/llm-wiki
```

To limit it to one project, clone it into that project's `.claude/skills/` folder instead.

It stays inactive in projects without a wiki. It triggers only on explicit wiki requests, and acts only on a wiki root named in the project's CLAUDE.md or a directory that already holds a `SCHEMA.md`. It creates a wiki only when asked, after confirming where.

To start a wiki in a project, ask for one; then name its root in that project's CLAUDE.md. Afterwards, ask for an ingest, a query or a lint in plain words. Everything particular to one wiki goes in its `SCHEMA.md`, not in the skill.

The check script needs Python 3.9 or later and nothing outside the standard library. Its tests passed on 3.9.6 (macOS's `/usr/bin/python3`), 3.14 and 3.15 in November 2026. Run the tests from the repository root with:

```bash
python3 -m unittest discover -s tests
```

`evals/` holds three tests of the agent's behaviour with the skill: it does nothing in a project without a wiki, stops to discuss before compiling an ingest, and reports rather than fixes a wrong figure at lint. They are in the format `claude plugin eval` reads, and running them makes billed model calls.

## Origin

Forked from [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) at commit `eafcc77` (23 July 2026), MIT. Ideas taken from the [Hermes Agent llm-wiki skill](https://github.com/NousResearch/hermes-agent/tree/main/optional-skills/research/llm-wiki) (version 2.1.0), MIT, without copying its files.

I keep a separate version because, as of November 2026, upstream had merged nothing since that commit, and the Hermes skill is written for a different agent.

### Changes from upstream

From Astro-Han, kept: the raw/ and wiki/ layout, the grounding invariant and its check script, triage, Outdated and Disputed status blocks, cascade updates, lint, and archiving. Not taken: its README, image and `.gitignore`. One of its example pages and its source are kept only as test fixtures, in `tests/fixtures/examples/`.

From Hermes, added: an orientation read at the start of each session, a discussion of takeaways before compiling articles, confirmation before touching 10 or more articles, a confidence field, page thresholds, a per-wiki `SCHEMA.md`, and a report of changed files. Not taken: `[[wikilinks]]`, which render only in Obsidian; tag taxonomy; sha256 drift checks; Obsidian sync.

Original to this fork:
- a living synthesis page of what the wiki understands, disputes and has not answered, from the gist's overview and synthesis, kept as an ordinary checked article and revised by discussion;
- lint suggests data gaps, questions and sources to pursue, as the gist describes;
- safe to install globally: narrow triggers, no default wiki location, and a new wiki only on request; a configurable wiki root;
- a Review field marking interpretations not yet discussed, and discussion-only sections set in `SCHEMA.md`;
- raw files record whether they are verbatim or a model's summary; summaries are research leads only, and facts are compiled only from original text;
- every claim, not only its figures, needs a source with the same subject; unfound claims are dropped rather than restated vaguely; multi-source articles link each paragraph to the sources supporting it;
- archived answers carry Confidence, judged on their central claims, and Review, and list the articles they rest on in a `Cites:` field, upstream's `Sources:`, so that `Sources:` always means outside sources;
- lint repairs a broken source link only when the candidate file records the same source;
- lint reports for missing or overstated confidence, missing paragraph sources, unreviewed articles, long articles and stale fast-moving ones.

`check_evidence.py` changes, each with tests: it skips the Confidence and Review lines; it checks the explanations inside Outdated and Disputed blocks, which upstream skipped, while still skipping the block's own date; it reports a file that is not valid UTF-8 instead of crashing; a bare value no longer matches a source value with a spaced unit (`99.9` against `99.9 %`); Raw links are read whole, so `notes.md.txt` is reported rather than read as `notes.md`; and it runs on Python 3.9.
