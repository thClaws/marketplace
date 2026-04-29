# thClaws Marketplace

Official registry of skills (and later: plugins, MCP servers) for [thClaws](https://github.com/thClaws/thClaws).

This repo is the source of truth that backs `https://thclaws.ai/api/marketplace.json` — the catalog the thClaws CLI/GUI fetches when you run `/skill marketplace`. Each entry below is curated, license-vetted, and customized where needed for thClaws's `.thclaws/skills/` install convention.

## Layout

```
marketplace/
├── skills/              # one subdir per skill, each with SKILL.md + LICENSE + NOTICE
│   └── skill-creator/
│       ├── SKILL.md
│       ├── LICENSE.txt   (preserved from upstream)
│       ├── NOTICE.md     (our modifications, per Apache 2.0)
│       ├── scripts/
│       └── ...
├── plugins/             # (planned)
└── mcp/                 # (planned)
```

## Install a skill

In a thClaws session:

```
/skill marketplace             # browse the catalog
/skill info skill-creator      # see detail
/skill install skill-creator   # project-scope install (lands in .thclaws/skills/)
/skill install --user skill-creator   # user-scope install (~/.config/thclaws/skills/)
```

You can also install directly without going through the catalog:

```
/skill install https://github.com/thClaws/marketplace.git#main:skills/skill-creator
```

## Contributing a skill

We accept skill submissions via PR. Requirements:

| Requirement | Why |
|---|---|
| Apache-2.0 or MIT license, in a `LICENSE` file inside the skill dir | thClaws redistributes — needs a permissive license |
| Original work, OR a clearly-attributed derivative (with `NOTICE.md` listing modifications) | Apache-2.0 §4(b) compliance |
| `SKILL.md` with valid YAML frontmatter (`name`, `description`, optional `short_description`) | Required for `/skill marketplace` listing |
| The skill directory name matches the `name` field | thClaws install convention; the directory must contain `SKILL.md` directly |
| No proprietary/source-available content | We only ship redistributable skills; if upstream restricts use, link don't mirror |

PRs are reviewed by [@mozeal](https://github.com/mozeal) (per `CODEOWNERS`). Aim for one skill per PR so changes are easy to review.

## License

The scaffolding files in this repo (this `README.md`, `LICENSE`, `CODEOWNERS`) are licensed under Apache-2.0. Each individual skill carries its own `LICENSE` file inside its directory — that's the license that governs that skill's contents.

## Trust model

This repo is the *content* layer; the *trust* layer is the JSON catalog at `thclaws.ai/api/marketplace.json` (published from the operator's workstation, not from CI on this repo). When the thClaws client fetches the catalog, it gets URLs that point back here for the actual skill source — but the entry's existence in the catalog is gated by the operator, not by anyone with merge rights to this registry.

Practically: a malicious skill PR that slipped past review here would still need to be added to the official catalog by the operator before any thClaws user could `/skill install <name>` it by name. The bar is doubled.
