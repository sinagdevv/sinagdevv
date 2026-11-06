# Interactive site deployment

The portfolio lives in `site/` and is configured as a standalone Next.js app.

## Vercel

1. Import `sinagdevv/sinagdevv` into Vercel.
2. Set **Root Directory** to `site`.
3. Keep the framework preset as **Next.js**.
4. No environment variables are required for the first deployment.
5. Add the resulting deployment URL to the README CTA after deployment; this repository intentionally does not invent one.

The site has no server-side secrets and does not require a database. GitHub telemetry remains a generated static asset, so the site can be deployed independently of GitHub Actions.
