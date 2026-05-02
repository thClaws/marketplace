# NOTICE

This skill is a derivative work of `skill-creator` from
[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator),
licensed under the Apache License 2.0.

Original copyright © Anthropic, PBC. All rights reserved by the original
authors except where modified below.

## Modifications by ThaiGPT Co., Ltd. (the thClaws project)

The following changes were made when redistributing this skill via the
thClaws marketplace at `github.com/thClaws/marketplace`:

1. **`SKILL.md`** — added a new section "**Where to install the finished
   skill (thClaws)**" between "Test Cases" and "Running and evaluating
   test cases", explaining the `.thclaws/skills/` and
   `~/.config/thclaws/skills/` install locations. Required so the skill
   tells the agent where to land the output when used in a thClaws
   session (the original assumed Claude Code's `.claude/skills/` path
   convention).
2. **`scripts/run_eval.py`** — `find_project_root()` now also recognizes
   `.thclaws/` as a project marker (in addition to `.claude/`), so the
   script works when invoked from a thClaws project directory. The
   `claude -p` subprocess invocation itself is unchanged — description
   evaluation still requires the Claude Code CLI to be installed.
3. **`eval-viewer/viewer.html`** — copy text changed from "your Claude
   Code session" to "your agent session (thClaws or Claude Code)" in
   the review-complete and instructions banners.
4. **`SKILL.md` (Anatomy of a Skill section)** — added documentation
   for thClaws's auto-detection conventions: the `SkillTool` response
   automatically lists `scripts/*.py|.sh|.js|.ts|.rb|...` with the
   conventional interpreter prefix, and surfaces a `requirements.txt`
   sibling as a one-time `pip install -r ...` hint. Skill authors
   following these conventions don't need explicit `Run: ...` lines
   in their SKILL.md for every script. The original SKILL.md only
   showed the directory layout; this revision documents the
   thClaws-side runtime conventions that make zero-config script
   invocation work.
5. **This `NOTICE.md`** — added per Apache 2.0 §4(b) "stating that you
   changed the files".

The original `LICENSE.txt` (Apache License, Version 2.0) is preserved
unchanged. All Anthropic copyright notices in the source files are
preserved.

The eval (`run_eval.py`, `improve_description.py`) and packaging
(`package_skill.py`) scripts retain their original Claude-CLI
dependency. A future revision may add a thClaws-CLI alternative; until
then, treat those scripts as Claude-Code-only.
