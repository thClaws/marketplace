# NOTICE

This skill is a derivative work of `frontend-design` from
[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design),
licensed under the Apache License 2.0.

Original copyright © Anthropic, PBC. All rights reserved by the original
authors except where modified below.

## Modifications by ThaiGPT Co., Ltd. (the thClaws project)

The following changes were made when redistributing this skill via the
thClaws marketplace at `github.com/thClaws/marketplace`:

1. **`SKILL.md`** — added a header note flagging this as a thClaws-
   distributed fork of the upstream Anthropic skill, with a pointer to
   this NOTICE file for the modification list.
2. **`SKILL.md`** — added a `short_description` field to the YAML
   frontmatter for the marketplace catalogue list view (~50 chars).
   Required by the thClaws marketplace schema for the one-line
   `/skill marketplace` rendering.
3. **`SKILL.md`** — appended a "## Working with thClaws" section
   documenting tool-call conventions specific to the thClaws agent
   surface: Bash auto-non-interactive env vars (`CI=1`, etc.),
   sandbox-respected Edit/Write, build-not-dev-server verification.
   The original SKILL.md was framework-agnostic and didn't address
   agent-tool conventions; this section helps the model use thClaws's
   specific tool affordances without rediscovering them per session.
4. **`SKILL.md`** — replaced `license: Complete terms in LICENSE.txt`
   with `license: Apache-2.0 — complete terms in LICENSE.txt` so the
   marketplace JSON's SPDX-style identifier matches what the
   frontmatter advertises.
5. **`SKILL.md`** — replaced "Claude is capable of extraordinary
   creative work" in the closing remember-line with "thClaws (and the
   underlying model) is capable of extraordinary creative work." The
   substantive guidance is unchanged; the wording acknowledges that
   thClaws sessions may run on multiple model providers, not only
   Claude.
6. **This `NOTICE.md`** — added per Apache 2.0 §4(b) "stating that you
   changed the files".

The original `LICENSE.txt` (Apache License, Version 2.0) is preserved
unchanged. All Anthropic copyright notices in the source files are
preserved.

The skill body's design guidance (Design Thinking, Frontend Aesthetics
Guidelines) is verbatim from the upstream and continues to reflect the
upstream maintainers' aesthetic point of view.
