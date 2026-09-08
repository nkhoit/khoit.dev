# khoit.dev

Khoi Tran’s personal site: two static HTML pages and one shared stylesheet.
No frontend JavaScript, framework, dependencies, or build step.

## Local redesign draft

The homepage copy and abbreviated resume are drafts pending Khoi’s approval.
The selected photo is the approved, metadata-free 580 × 580 WebP; no private
source documents or unselected photos are included in this repository.

- `index.html` — short introduction, interests, photo, and contact links.
- `resume/index.html` — brief experience and education, with earlier research
  and student roles explicitly grouped.
- `styles.css` — shared responsive typography and print styles.
- `assets/khoi-shiro.webp` — selected photo, displayed at 200px wide.
- `api/webfinger/` — existing Azure identity endpoint, unchanged.
- `staticwebapp.config.json` and `.github/workflows/` — unchanged Azure routing
  and deployment configuration.

## Tests

Requires Python 3.9+ and Node.js 18+; no packages to install and no server needed.
From the repository root:

```sh
python3 -B -m unittest discover -s tests -v
node --test tests/webfinger.test.cjs
```

The Python suite checks document structure, accessible labels, exact contact
links, local link/asset targets, role dates, content brevity, no page JavaScript,
plain styling, WebP dimensions and absence of metadata chunks. It also compares
API/config/workflow bytes to the pre-redesign commit
`47ba677eaef958ceb70ab4537580a7f38038c670` (requires that commit in local Git history).
The Node suite invokes the real WebFinger handler and checks its responses and
Azure function binding without an emulator.

These are offline source/handler tests, not a substitute for browser visual QA
or a deployed Azure integration test. External profile destinations are checked
against the intended URLs, not fetched. Review desktop/mobile rendering,
keyboard focus, and no-JS behavior in the private preview before approval.

## Preview and routing

Serve the repository root with a static server, bound to loopback, and open `/`
and `/resume/`. Root-relative links require HTTP serving rather than `file://`.
For example: `python3 -m http.server 8000 --bind 127.0.0.1`.

`/resume/` has its own `resume/index.html`; it is not a client-side route.
Azure’s existing `navigationFallback` applies to requests without a matching
static file, so the new page needs no routing change. The wildcard route only
allows anonymous access; it does not rewrite the resume. The existing
`/.well-known/webfinger` rewrite to `/api/webfinger` is preserved.
Reference: [Azure Static Web Apps configuration](https://learn.microsoft.com/en-us/azure/static-web-apps/configuration).

## Publishing caution

The existing workflow publishes pushes to `main` and creates public PR previews.
Do not push, open a PR, or deploy this local draft without explicit approval.
No Azure resources need to be created or modified for local review.
