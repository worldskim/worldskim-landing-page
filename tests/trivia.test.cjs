const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('editions/2026-11-06.html', 'utf8');
const scripts = [...source.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map(x => x[1]);
const script = scripts.find(s => s.includes('Interactive trivia'));
assert.ok(script);
function run(search, initial = {}) {
  const state = { ...initial }, classes = new Set();
  const cls = () => ({add() {}});
  const elements = {};
  const card = {
    classList: { contains: x => classes.has(x), add: x => classes.add(x) },
    getAttribute: k => k === 'data-answer' ? '2' : '2026-11-06',
    querySelectorAll: k => k === '.qz-opt' ? rows : [],
    querySelector: k => elements[k] ||= {textContent: '', hidden: true},
    scrollIntoView() {},
  };
  const rows = [0, 1, 2, 3].map(i => ({
    disabled: false, classList: cls(), setAttribute() {},
    getAttribute: () => String(i), closest: () => card,
    addEventListener(k, f) { this[k] = f; },
  }));
  vm.runInNewContext(script, {
    document: {querySelectorAll: () => [card]},
    location: {search}, URLSearchParams, Date, JSON,
    localStorage: {getItem: k => state[k] ?? null, setItem: (k,v) => state[k] = v},
    setTimeout: f => f(),
  });
  return {state, rows, answered: classes.has('is-answered')};
}
for (const query of ['', '?pick=', '?pick=Z', '?pick=AB', '?pick=1', '?pick=%20A', '?other=A']) {
  const r = run(query);
  assert.equal(r.answered, false, query);
  assert.equal(Object.keys(r.state).length, 0, query);
}
for (const [i, letter] of [...'ABCD'].entries()) {
  const r = run('?pick=' + letter);
  assert.equal(r.answered, true);
  assert.equal(JSON.parse(r.state['qz-2026-11-06']), i);
  assert.ok(r.rows.every(x => x.disabled));
  assert.equal(JSON.parse(r.state['qz-record']).answered, 1);
  assert.equal(JSON.parse(r.state['qz-record']).correct, i === 2 ? 1 : 0);
  const again = run('?pick=A', r.state);
  assert.deepEqual(again.state, r.state, 'Revisit must retain first choice and record');
}
assert.equal(JSON.parse(run('?pick=c').state['qz-2026-11-06']), 2);
const manual = run('');
manual.rows[3].click();
assert.equal(JSON.parse(manual.state['qz-2026-11-06']), 3);
console.log('PASS: absent/empty/invalid picks stay unanswered; A–D/lowercase/manual answer, lock, persistence, record, repeat and streak behavior');
