# Public profile synchronization

`sync-profile.mjs` uses the public GitHub REST repositories endpoint for `sinagdevv`. It requests at most ten pages of 100 repositories, filters to repositories owned by `sinagdevv` with `private !== true`, and writes only a bounded summary to `data/github-public.json` plus the self-contained `assets/generated/activity.svg` panel.

The workflow runs daily at 04:17 UTC and can also be started with `workflow_dispatch`. Its only required permission is `contents: write`, because the default `GITHUB_TOKEN` commits generated changes back to this repository. The token is never written to output or generated files.

Writes happen only after a complete successful fetch, using temporary files followed by atomic rename. A failed request exits non-zero before replacing the last valid generated files. The workflow commits only when the generated content changed and serializes runs through a concurrency group.

The language spectrum is repository code composition, not a claim about personal proficiency. Private repositories and private activity are never queried or rendered.
