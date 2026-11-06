import { readFile, writeFile, rename } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const username = 'sinagdevv';
const apiBase = `https://api.github.com/users/${username}`;
const generatedPath = resolve(root, 'data/github-public.json');
const activityPath = resolve(root, 'assets/generated/activity.svg');
const siteActivityPath = resolve(root, 'site/public/activity.svg');
const token = process.env.GITHUB_TOKEN;

export function publicRepository(repo) {
  return repo.owner?.login?.toLowerCase() === username && repo.private !== true;
}

export function summarizeLanguages(repositories) {
  const totals = new Map();
  for (const repo of repositories) {
    if (!repo.language) continue;
    totals.set(repo.language, (totals.get(repo.language) ?? 0) + 1);
  }
  const total = [...totals.values()].reduce((sum, value) => sum + value, 0);
  return [...totals.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([name, repositoriesCount]) => ({
      name,
      repositories: repositoriesCount,
      percent: total ? Math.round((repositoriesCount / total) * 100) : 0
    }));
}

async function getJson(url, attempts = 3) {
  let lastError;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10_000);
    try {
      const response = await fetch(url, {
        headers: {
          Accept: 'application/vnd.github+json',
          'User-Agent': 'sinag-profile-sync',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        signal: controller.signal
      });
      if (!response.ok) throw new Error(`GitHub API ${response.status} for ${url}`);
      return await response.json();
    } catch (error) {
      lastError = error;
      if (attempt < attempts - 1) await new Promise((resolvePromise) => setTimeout(resolvePromise, 500 * (attempt + 1)));
    } finally {
      clearTimeout(timeout);
    }
  }
  throw lastError;
}

export function renderActivity(data) {
  const width = 920;
  const rows = data.repositories.slice(0, 5);
  const repoLines = rows.length
    ? rows.map((repo, index) => `<text x="42" y="${132 + index * 36}" class="repo">${index + 1}. ${escapeXml(repo.name)}</text><text x="620" y="${132 + index * 36}" class="meta">${repo.stars} ★  ${repo.forks} forks</text>`).join('')
    : '<text x="42" y="132" class="repo">Awaiting first public sync</text>';
  const languageLines = data.languages.slice(0, 4).map((language, index) => `<text x="42" y="${350 + index * 28}" class="repo">${escapeXml(language.name)}</text><rect x="180" y="${336 + index * 28}" width="${Math.max(language.percent * 4, language.percent ? 8 : 0)}" height="10" rx="5" class="bar"/><text x="${205 + Math.max(language.percent * 4, 8)}" y="${350 + index * 28}" class="meta">${language.percent}% of public repos</text>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} 470" role="img" aria-labelledby="title desc"><title id="title">SINAG public GitHub telemetry</title><desc id="desc">A generated panel showing public repository signals and language composition. Repository language percentages describe code composition, not personal skill.</desc><style>.panel{fill:#111216;stroke:#383129}.label{fill:#D6A443;font:600 11px ui-monospace,monospace;letter-spacing:2px}.repo{fill:#F4F0E8;font:15px ui-monospace,monospace}.meta{fill:#96918A;font:12px ui-monospace,monospace}.bar{fill:#D6A443}.hair{stroke:#383129}.pulse{fill:#FFBF47}</style><rect width="${width}" height="470" rx="22" fill="#090A0C"/><rect x="1" y="1" width="${width - 2}" height="468" rx="21" class="panel"/><circle cx="42" cy="44" r="5" class="pulse"/><text x="62" y="48" class="label">PUBLIC TELEMETRY / ${data.syncedAt ? data.syncedAt.slice(0, 10) : 'NOT SYNCED'}</text><line x1="42" x2="878" y1="78" y2="78" class="hair"/><text x="42" y="108" class="label">RECENT SIGNALS</text>${repoLines}<line x1="42" x2="878" y1="294" y2="294" class="hair"/><text x="42" y="324" class="label">LANGUAGE SPECTRUM</text>${languageLines}<text x="42" y="445" class="meta">${data.publicRepositoryCount ?? '—'} public repositories · source: GitHub REST API</text></svg>`;
}

function escapeXml(value) {
  return String(value).replace(/[<>&'\"]/g, (character) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;' })[character]);
}

async function atomicWrite(path, content) {
  const tempPath = `${path}.tmp`;
  await writeFile(tempPath, content, 'utf8');
  await rename(tempPath, path);
}

async function sync() {
  const repositories = [];
  for (let page = 1; page <= 10; page += 1) {
    const batch = await getJson(`${apiBase}/repos?per_page=100&page=${page}&sort=updated`);
    repositories.push(...batch.filter(publicRepository));
    if (batch.length < 100) break;
  }
  const data = {
    status: 'ok',
    username,
    syncedAt: new Date().toISOString(),
    publicRepositoryCount: repositories.length,
    repositories: repositories
      .sort((a, b) => new Date(b.pushed_at) - new Date(a.pushed_at) || a.name.localeCompare(b.name))
      .slice(0, 20)
      .map((repo) => ({ name: repo.name, description: repo.description ?? '', url: repo.html_url, updatedAt: repo.pushed_at, language: repo.language, stars: repo.stargazers_count, forks: repo.forks_count })),
    languages: summarizeLanguages(repositories),
    error: null
  };
  try {
    const current = JSON.parse(await readFile(generatedPath, 'utf8'));
    const comparable = (value) => JSON.stringify({ ...value, syncedAt: null });
    if (comparable(current) === comparable(data)) data.syncedAt = current.syncedAt;
  } catch {
    // First sync or an invalid prior file: write the verified response.
  }
  await atomicWrite(generatedPath, `${JSON.stringify(data, null, 2)}\n`);
  const activity = renderActivity(data);
  await atomicWrite(activityPath, activity);
  await atomicWrite(siteActivityPath, activity);
  console.log(`Synced ${data.publicRepositoryCount} public repositories for ${username}.`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  sync().catch((error) => {
    console.error(`Profile sync failed: ${error.message}`);
    process.exitCode = 1;
  });
}
