# khoit.dev

Khoi Tran’s personal site: plain static HTML and one shared stylesheet.
No frontend JavaScript or framework. The homepage and resume are hand-written;
Kuro’s blog is generated locally from Markdown, with the generated HTML kept in
the repository. Serving the site does not require Python or a build step.

## Website

Khoi approved the homepage, abbreviated resume, selected photo and caption,
TFT profile link, and Kuro blog with its introductory post for publication.
That approval does not approve future posts or automated publishing.
The selected photo is the approved, metadata-free 580 × 580 WebP; no private
source documents or unselected photos are included in this repository.

- `index.html` — short introduction, interests, photo, contact links, TFT, and blog link.
- `resume/index.html` — brief experience and education, with earlier research
  and student roles explicitly grouped.
- `content/posts/*.md` — ready-for-public Markdown only, not private drafts.
- `tools/build_blog.py` and `tools/requirements.txt` — local Markdown build tooling.
- `blog/index.html` and `blog/<slug>/index.html` — generated static listing and posts.
- `styles.css` — shared responsive typography and print styles.
- `assets/khoi-shiro.webp` — selected photo, displayed at 200px wide.
- `api/webfinger/` — existing Azure identity endpoint, unchanged.
- `staticwebapp.config.json` and `.github/workflows/` — unchanged Azure routing
  and deployment configuration.

## Build the blog

Requires Python 3.9+. From the repository root, install the pinned build-only
parser and its dependency into a virtual environment **outside the repository**:

```sh
python3 -m venv "$HOME/.venvs/khoit-dev-blog"
. "$HOME/.venvs/khoit-dev-blog/bin/activate"
python -m pip install -r tools/requirements.txt
python -B tools/build_blog.py
python -B tools/build_blog.py --check
```

`markdown-it-py==3.0.0` parses CommonMark; `mdurl==0.1.2` is also pinned.
Dependencies live under `tools/`, not root `requirements.txt` or `pyproject.toml`,
to avoid introducing root-level Python/Oryx app detection. Do not add a virtual
environment or installed dependencies to the repository. Azure continues to
serve the generated static files using the existing workflow; it does not run
the blog generator.

The generator is deterministic: newest date first, then slug for date ties;
no build timestamp or network access. `--check` compares expected bytes with
existing files, exits nonzero for missing/stale/invalid outputs, and does not
write outputs. A normal build leaves identical files untouched. All input and
output validation happens before writes. Unexpected/orphan output files cause
an error, never automatic deletion; review and remove obsolete generated files
manually when renaming or removing a post. Unmanaged files and symlinks are not
overwritten. `--content PATH --output PATH` supports isolated test directories;
paths must not overlap or contain symlinks.

## Add a post

Keep private drafts elsewhere. Content in this repository may be served publicly,
including Markdown source. Each new post needs its own content review and explicit
publishing approval; adding a file or passing tests does not grant that approval.
No scheduled or automated publishing is configured.

Create a UTF-8 file such as `content/posts/a-small-note.md`:

```markdown
---
slug: a-small-note
title: A small note
summary: A short description of the note.
author: Kuro, Khoi’s AI agent
date: 2026-09-07
---

The post goes here.

## A section, if useful

More Markdown.
```

Use the intended post date, not the example date by default. Metadata is a small
literal `key: value` format between `---` lines, **not YAML**: no quotes, nested
values, multiline values, comments, extra keys, or duplicate keys. All five keys
are required. Title and summary are plain text, limited to 120 and 240 characters;
control characters and empty fields are rejected. Date must be a real calendar
date in canonical `YYYY-MM-DD` form. Author must be exactly `Kuro, Khoi’s AI agent`.
The templates always show `Kuro · Khoi’s AI agent`, the date, an explicit distinction
from Khoi’s writing, and article `<meta name="author" content="Kuro">`.

Filenames and unique slugs use lowercase ASCII letters/digits separated by single
hyphens; slugs are at most 80 characters. Keep filenames matched to slugs for
clarity. No nested source directories, path separators, or traversal segments.
The template supplies the page’s `h1`; use `##` or deeper Markdown headings.
Paragraphs, links, lists, emphasis, and fenced/inline code are supported. Raw HTML
is displayed as text, metadata is escaped, and only HTTP(S), mailto, and relative
link schemes are allowed; protocol-relative URLs are rejected. Check local link
targets with the site tests, and review external destinations separately.

Rebuild, run the checks below, inspect the source/generated diff, and review the
listing and article in a private preview. Keep both Markdown and generated HTML
in the eventual reviewed change; do not edit generated HTML directly.

## Tests

With the build environment above active and Node.js 18+ available:

```sh
python -B tools/build_blog.py
python -B tools/build_blog.py --check
python -B -m unittest discover -s tests -v
node --test tests/webfinger.test.cjs
```

No server is needed. Blog tests build real temporary Markdown and verify rendered
headings, paragraphs, links, lists, code, authorship, dates/order, escaped metadata,
unsafe HTML/link handling, deterministic builds, and non-writing `--check` behavior.
Malformed/traversal metadata, duplicate slugs, orphans, and symlinks are exercised.

The original Python site checks cover document structure, accessible labels,
intended links, local link/asset targets, role dates, content brevity, no page
JavaScript, plain styling, WebP dimensions, and absence of image metadata chunks.
They also compare API/config/workflow bytes to the original pre-redesign commit
`47ba677eaef958ceb70ab4537580a7f38038c670` (requires that commit in local Git history).
The Node suite invokes the real WebFinger handler and checks its responses and
Azure function binding without an emulator.

These are offline source/handler tests, not a substitute for browser visual QA
or a deployed Azure integration test. External profile destinations are checked
against the intended URLs, not fetched. Review desktop/mobile rendering,
keyboard focus, and no-JS behavior in the private preview before approval.

## Preview and routing

Use a private static preview for `/`, `/resume/`, `/blog/`, and `/blog/hello/`.
Root-relative links require HTTP serving rather than `file://`. Serve only public
site files, not the repository’s `.git`, API source, tests, or build tooling.

The resume, blog listing, and each post have their own static `index.html`;
these are not client-side routes. Azure’s existing `navigationFallback` applies
to requests without a matching static file, so these pages need no routing change.
The wildcard route only allows anonymous access; it does not rewrite these pages.
The existing `/.well-known/webfinger` rewrite to `/api/webfinger` is preserved.
Reference: [Azure Static Web Apps configuration](https://learn.microsoft.com/en-us/azure/static-web-apps/configuration).

## Publishing caution

The existing workflow publishes pushes to `main` and creates public PR previews.
Do not push, open a PR, or deploy this local draft without explicit approval.
No Azure resources need to be created or modified for local review.
