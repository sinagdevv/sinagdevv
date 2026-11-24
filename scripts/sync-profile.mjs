import { readFile, writeFile, rename, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const username = 'sinagdevv';
const apiBase = `https://api.github.com/users/${username}`;
const generatedPath = resolve(root, 'data/github-public.json');
const activityPath = resolve(root, 'assets/generated/activity.svg');
const footprintsPath = resolve(root, 'assets/generated/footprints.svg');
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

const FONT = "Cinzel, 'Trajan Pro', 'Palatino Linotype', Georgia, serif";
const PALETTE = { black: '#000000', char: '#141414', ash: '#666666', silver: '#BFBFBF', off: '#E5E5E5' };
const LEVELS = ['#141414', '#3a3a3a', '#666666', '#BFBFBF', '#E5E5E5'];

function frame(width, height, title, desc, body) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-labelledby="t d"><title id="t">${escapeXml(title)}</title><desc id="d">${escapeXml(desc)}</desc><style>text{font-family:${FONT};letter-spacing:.12em}.cap{fill:${PALETTE.off};font-size:13px}.name{fill:${PALETTE.silver};font-size:15px;letter-spacing:.06em}.meta{fill:${PALETTE.ash};font-size:11px}.big{fill:${PALETTE.off};font-size:34px;letter-spacing:.04em}</style><rect width="${width}" height="${height}" fill="#000"/><rect x="6" y="6" width="${width - 12}" height="${height - 12}" fill="none" stroke="${PALETTE.char}"/><path d="M6 6h22M6 6v22M${width - 6} 6h-22M${width - 6} 6v22M6 ${height - 6}h22M6 ${height - 6}v-22M${width - 6} ${height - 6}h-22M${width - 6} ${height - 6}v-22" stroke="${PALETTE.ash}" fill="none"/>${body}</svg>`;
}

export function renderActivity(data) {
  const width = 900;
  const rows = data.repositories.slice(0, 5);
  const langs = data.languages.slice(0, 5);
  const repoLines = rows.length
    ? rows.map((repo, i) => `<text x="40" y="${128 + i * 40}" class="name">${escapeXml(repo.name.length > 30 ? `${repo.name.slice(0, 29)}…` : repo.name)}</text><text x="40" y="${146 + i * 40}" class="meta">${repo.updatedAt ? `pushed ${repo.updatedAt.slice(0, 10)}` : ''}${repo.language ? ` · ${escapeXml(repo.language)}` : ''}${repo.stars ? ` · ${repo.stars} stars` : ''}</text>`).join('')
    : `<text x="40" y="128" class="name">Awaiting first public sync</text>`;
  const bar = 270;
  const langLines = langs.map((language, i) => {
    const w = Math.max(Math.round((language.percent / 100) * bar), language.percent ? 4 : 0);
    return `<text x="500" y="${128 + i * 40}" class="name">${escapeXml(language.name)}</text><text x="860" y="${128 + i * 40}" class="meta" text-anchor="end">${language.percent}%</text><rect x="500" y="${137 + i * 40}" width="360" height="2" fill="${PALETTE.char}"/><rect x="500" y="${136 + i * 40}" width="${w * 360 / bar}" height="4" fill="${PALETTE.silver}"><animate attributeName="width" values="0;${w * 360 / bar}" dur="2.4s" fill="freeze"/></rect>`;
  }).join('');
  const sweep = `<defs><linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#E5E5E5" stop-opacity="0"/><stop offset=".5" stop-color="#E5E5E5" stop-opacity=".05"/><stop offset="1" stop-color="#E5E5E5" stop-opacity="0"/></linearGradient></defs><rect y="6" width="160" height="368" fill="url(#sw)"><animate attributeName="x" values="-160;${width}" dur="12s" repeatCount="indefinite"/></rect>`;
  const body = `<text x="40" y="46" class="cap">PUBLIC CHRONICLE · ${data.syncedAt ? data.syncedAt.slice(0, 10) : 'NOT SYNCED'}</text><text x="860" y="46" class="big" text-anchor="end">${data.publicRepositoryCount ?? '—'}</text><text x="860" y="64" class="meta" text-anchor="end">PUBLIC REPOSITORIES</text><path d="M40 78H860" stroke="${PALETTE.char}"/><text x="40" y="104" class="meta">RECENT RELICS</text><text x="500" y="104" class="meta">LANGUAGE SPECTRUM · BY REPOSITORY</text><path d="M470 96V340" stroke="${PALETTE.char}"/>${repoLines}${langLines}<text x="40" y="364" class="meta">source: GitHub REST API · language shares count repositories, not personal skill</text>${sweep}`;
  return frame(width, 380, 'SINAG public GitHub chronicle', `A monochrome panel of public repository activity and language composition. ${data.publicRepositoryCount ?? 0} public repositories. Repository language percentages describe code composition, not personal skill.`, body);
}

export function parseContributions(html) {
  const tips = new Map();
  for (const m of html.matchAll(/<tool-tip[^>]*\bfor="([^"]+)"[^>]*>\s*(No|\d+) contributions? on/g)) tips.set(m[1], m[2] === 'No' ? 0 : Number(m[2]));
  const cells = [];
  for (const m of html.matchAll(/<td\b[^>]*\bdata-date="([^"]+)"[^>]*\bid="(contribution-day-component-(\d+)-(\d+))"[^>]*\bdata-level="(\d)"/g)) {
    cells.push({ date: m[1], row: Number(m[3]), col: Number(m[4]), level: Number(m[5]), count: tips.get(m[2]) ?? 0 });
  }
  return cells.sort((a, b) => a.date.localeCompare(b.date));
}

export function contributionStats(cells) {
  let longest = 0, run = 0;
  for (const c of cells) { run = c.count > 0 ? run + 1 : 0; longest = Math.max(longest, run); }
  let current = 0;
  for (let i = cells.length - 1; i >= 0; i -= 1) {
    if (cells[i].count > 0) current += 1; else if (i < cells.length - 1) break;
  }
  const busiest = cells.reduce((best, c) => (c.count > (best?.count ?? 0) ? c : best), null);
  return { total: cells.reduce((sum, c) => sum + c.count, 0), longest, current, busiest };
}

export function renderFootprints(cells) {
  const width = 900, size = 12, gap = 4, left = 40, top = 112;
  const stats = contributionStats(cells);
  const weeks = Math.max(...cells.map((c) => c.col)) + 1;
  const step = size + gap;
  const gridW = weeks * step - gap;
  const rects = cells.map((c) => `<rect x="${left + c.col * step}" y="${top + c.row * step}" width="${size}" height="${size}" rx="1" fill="${LEVELS[c.level]}">${c.level >= 3 ? `<animate attributeName="opacity" values="1;.55;1" dur="${4 + (c.col % 5)}s" begin="-${c.col % 7}s" repeatCount="indefinite"/>` : ''}</rect>`).join('');
  const stat = (x, value, label) => `<text x="${x}" y="46" class="big">${value}</text><text x="${x}" y="66" class="meta">${label}</text>`;
  const first = cells[0]?.date ?? '', last = cells.at(-1)?.date ?? '';
  const body = `${stat(40, stats.total, 'CONTRIBUTIONS · LAST YEAR')}${stat(340, stats.longest, 'LONGEST STREAK · DAYS')}${stat(620, stats.current, 'CURRENT STREAK · DAYS')}<path d="M40 82H860" stroke="${PALETTE.char}"/>${rects}<defs><linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#E5E5E5" stop-opacity="0"/><stop offset=".5" stop-color="#E5E5E5" stop-opacity=".16"/><stop offset="1" stop-color="#E5E5E5" stop-opacity="0"/></linearGradient><clipPath id="g"><rect x="${left}" y="${top}" width="${gridW}" height="${7 * step - gap}"/></clipPath></defs><g clip-path="url(#g)"><rect y="${top}" width="120" height="${7 * step}" fill="url(#sw)"><animate attributeName="x" values="${left - 120};${left + gridW}" dur="9s" repeatCount="indefinite"/></rect></g><text x="40" y="${top + 7 * step + 22}" class="meta">${first} → ${last}</text><text x="692" y="${top + 7 * step + 22}" class="meta" text-anchor="end">LESS</text>${LEVELS.map((l, i) => `<rect x="${700 + i * 16}" y="${top + 7 * step + 12}" width="11" height="11" rx="1" fill="${l}"/>`).join('')}<text x="784" y="${top + 7 * step + 22}" class="meta">MORE</text>`;
  return frame(width, top + 7 * step + 40, 'SINAG contribution footprints', `A monochrome contribution calendar for the last year: ${stats.total} contributions, longest streak ${stats.longest} days, current streak ${stats.current} days. Source: GitHub public contribution calendar.`, body);
}

function escapeXml(value) {
  return String(value).replace(/[<>&'\"]/g, (character) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;' })[character]);
}

async function atomicWrite(path, content) {
  await mkdir(dirname(path), { recursive: true });
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
  try {
    const response = await fetch(`https://github.com/users/${username}/contributions`, { headers: { 'User-Agent': 'sinag-profile-sync' } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const cells = parseContributions(await response.text());
    if (cells.length < 300) throw new Error(`unexpected calendar shape (${cells.length} cells)`);
    await atomicWrite(footprintsPath, renderFootprints(cells));
  } catch (error) {
    // Keep the previous footprints.svg rather than failing the whole sync.
    console.warn(`Contribution calendar skipped: ${error.message}`);
  }
  console.log(`Synced ${data.publicRepositoryCount} public repositories for ${username}.`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  sync().catch((error) => {
    console.error(`Profile sync failed: ${error.message}`);
    process.exitCode = 1;
  });
}
