import test from 'node:test';
import assert from 'node:assert/strict';
import { publicRepository, summarizeLanguages, renderActivity } from './sync-profile.mjs';

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
  const svg = renderActivity({ syncedAt: '2026-11-06T00:00:00.000Z', publicRepositoryCount: 1, repositories: [{ name: 'demo', stars: 2, forks: 1 }], languages: [{ name: 'TypeScript', percent: 100 }] });
  assert.match(svg, /role="img"/);
  assert.match(svg, /demo/);
  assert.match(svg, /source: GitHub REST API/);
});
