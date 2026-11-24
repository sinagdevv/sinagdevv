import test from 'node:test';
import assert from 'node:assert/strict';
import { publicRepository, summarizeLanguages, renderActivity, parseContributions, contributionStats, renderFootprints } from './sync-profile.mjs';

test('filters to public repositories owned by sinagdevv', () => {
  assert.equal(publicRepository({ owner: { login: 'sinagdevv' }, private: false }), true);
  assert.equal(publicRepository({ owner: { login: 'sinagdevv' }, private: true }), false);
  assert.equal(publicRepository({ owner: { login: 'someone-else' }, private: false }), false);
});

test('summarizes languages as repository composition', () => {
  const result = summarizeLanguages([{ language: 'TypeScript' }, { language: 'TypeScript' }, { language: 'Python' }, { language: null }]);
  assert.deepEqual(result, [{ name: 'TypeScript', repositories: 2, percent: 67 }, { name: 'Python', repositories: 1, percent: 33 }]);
});

test('renders a self-contained accessible activity asset', () => {
  const svg = renderActivity({ syncedAt: '2026-11-06T00:00:00.000Z', publicRepositoryCount: 1, repositories: [{ name: 'demo', stars: 2, forks: 1, updatedAt: '2026-11-01T00:00:00Z' }], languages: [{ name: 'TypeScript', percent: 100 }] });
  assert.match(svg, /role="img"/);
  assert.match(svg, /demo/);
  assert.match(svg, /source: GitHub REST API/);
});

test('parses a contribution calendar and derives streaks', () => {
  const day = (i, date, level, text) => `<td data-date="${date}" id="contribution-day-component-${i % 7}-${Math.floor(i / 7)}" data-level="${level}"></td><tool-tip for="contribution-day-component-${i % 7}-${Math.floor(i / 7)}">${text} on x</tool-tip>`;
  const html = day(0, '2026-01-01', 0, 'No contributions') + day(1, '2026-01-02', 2, '3 contributions') + day(2, '2026-01-03', 1, '1 contribution');
  const cells = parseContributions(html);
  assert.equal(cells.length, 3);
  assert.deepEqual(contributionStats(cells), { total: 4, longest: 2, current: 2, busiest: cells[1] });
  assert.match(renderFootprints(cells), /role="img"/);
});
