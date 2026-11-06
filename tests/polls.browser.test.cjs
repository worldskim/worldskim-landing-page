// Install Playwright outside the static site, or provide its module location.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = process.cwd();
const site = 'https://worldskim.com';
const endpoint = 'https://energized-kiwi-650.convex.site/v1/votes';
const query = '?poll=kenya-religious-oversight&vote=yes';
const shots = '/tmp/ws-poll-screens';
fs.mkdirSync(shots, {recursive:true});
let browser, passed = 0;
async function setup(options = {}) {
  const context = await browser.newContext({ viewport: options.mobile ? {width:390,height:844} : {width:1200,height:900} });
  if (options.init) await context.addInitScript(options.init);
  const calls = [];
  await context.route('**/*', async route => {
    const req = route.request(), url = new URL(req.url());
    if (url.origin === new URL(endpoint).origin) {
      assert.equal(req.url(), endpoint);
      assert.equal(req.method(), 'POST', 'Never GET votes');
      assert.equal(req.headers()['referer'], undefined);
      const data = req.postDataJSON();
      calls.push(data);
      assert.deepEqual(Object.keys(data).sort(), ['brand','poll','vote','voter']);
      assert.equal(data.brand, 'worldskim');
      assert.equal(data.poll, options.expectedPoll || 'kenya-religious-oversight');
      assert.match(data.voter, /^[0-9a-f]{32}$/);
      if (options.networkError) return route.abort('failed');
      if (options.gate) await options.gate;
      const response = options.response ? options.response(calls.length) : {status:200,body:{ok:true,duplicate:false,vote:'yes'}};
      return route.fulfill({
        status: response.status,
        headers: {'Access-Control-Allow-Origin': site},
        contentType:'application/json',
        body: typeof response.body === 'string' ? response.body : JSON.stringify(response.body),
      });
    }
    // Serve this worktree in-memory at its own HTTPS origin. No public request escapes.
    if (url.origin === site) {
      const file = path.resolve(root, '.' + (url.pathname === '/' ? '/index.html' : url.pathname));
      if (!file.startsWith(root + '/') || !fs.existsSync(file)) return route.fulfill({status:404,body:'Not found'});
      const ext = path.extname(file);
      return route.fulfill({status:200,contentType: ({'.js':'application/javascript','.css':'text/css','.html':'text/html','.woff':'font/woff'})[ext] || 'application/octet-stream',body:fs.readFileSync(file)});
    }
    return route.abort('blockedbyclient');
  });
  const page = await context.newPage();
  await page.goto(site + '/email/thanks.html' + (options.query ?? query));
  return {context,page,calls};
}
async function status(page) { return page.locator('#msg').innerText(); }
async function check(name, fn) { await fn(); console.log('PASS: '+name); passed++; }
(async () => {
  browser = await chromium.launch({headless:true,args:['--no-sandbox']});
  await check('load and programmatic click never submit; explicit trusted confirm submits once', async () => {
    const {context,page,calls} = await setup();
    assert.equal(calls.length,0);
    assert.match(await status(page), /not been recorded/);
    assert.ok((await page.locator('main').innerText()).includes('An anonymous browser token is stored for 30 days to limit repeat votes. No name or email is requested.'));
    assert.equal(await page.evaluate(() => localStorage.getItem('ws-poll-voter')),null);
    await page.screenshot({path: shots+'/confirm-desktop.png',fullPage:true});
    await page.locator('#confirm-vote').evaluate(el => el.click());
    assert.equal(calls.length,0);
    await page.locator('#confirm-vote').click();
    await page.waitForFunction(() => document.getElementById('msg').textContent.includes('vote was recorded'));
    assert.equal(calls.length,1);
    assert.equal(await page.locator('#confirm-vote').isVisible(),false);
    const token = await page.evaluate(() => JSON.parse(localStorage.getItem('ws-poll-voter')));
    assert.match(token.voter,/^[0-9a-f]{32}$/);
    const ttl = token.expires - Date.now();
    assert.ok(ttl > 29.9*86400000 && ttl <= 30*86400000);
    await page.screenshot({path: shots+'/success-desktop.png',fullPage:true});
    await context.close();
  });
  await check('duplicate displays server original No even when selected Yes', async () => {
    const {context,page,calls} = await setup({response:()=>({status:200,body:{ok:true,duplicate:true,vote:'no'}})});
    await page.locator('#confirm-vote').click();
    await page.waitForFunction(() => document.getElementById('msg').textContent.includes('already voted No'));
    assert.match(await status(page),/not counted again/);
    assert.equal(calls.length,1);
    await context.close();
  });
  await check('invalid, missing, duplicate params and unsafe slug stay closed', async () => {
    for (const query of ['', '?vote=yes', '?poll=kenya-religious-oversight&vote=', '?poll=kenya-religious-oversight&vote=YES', '?poll=../unknown&vote=yes', '?poll='+('a'.repeat(101))+'&vote=yes','?poll=kenya-religious-oversight&vote=yes&vote=no','?poll=kenya-religious-oversight&poll=unknown&vote=yes']) {
      const {context,page,calls} = await setup({query});
      assert.match(await status(page),/invalid or unavailable/);
      assert.equal(await page.locator('#confirm-vote').isVisible(),false);
      assert.equal(calls.length,0);
      await context.close();
    }
  });
  await check('original Nov3 supplied email poll confirms No without changing historical website', async () => {
    const {context,page,calls} = await setup({
      query:'?poll=world-elections&vote=no',
      expectedPoll:'world-elections',
      response:()=>({status:200,body:{ok:true,duplicate:false,vote:'no'}}),
    });
    assert.equal(await page.locator('#poll-question').innerText(),'World Skim reader poll');
    assert.equal(calls.length,0);
    await page.locator('#confirm-vote').click();
    await page.waitForFunction(()=>document.getElementById('msg').textContent.includes('Your No vote was recorded'));
    assert.equal(calls[0].vote,'no');
    await context.close();
  });
  await check('dynamic backend registry handles unknown/closed and temporary disabled/capacity', async () => {
    for (const code of ['unknown_poll','poll_closed','voting_disabled','poll_capacity_reached']) {
      const {context,page,calls} = await setup({
        query:'?poll=future-daily-question&vote=yes',expectedPoll:'future-daily-question',
        response:()=>({status:code==='unknown_poll'?404:503,body:{ok:false,error:code}}),
      });
      assert.equal(calls.length,0);
      await page.locator('#confirm-vote').click();
      await page.waitForFunction(()=>document.getElementById('msg').textContent.includes('No vote was confirmed'));
      assert.equal(calls.length,1);
      assert.equal(await page.locator('#confirm-vote').isVisible(),code==='voting_disabled'||code==='poll_capacity_reached');
      assert.doesNotMatch(await status(page),/vote was recorded/);
      await context.close();
    }
  });
  await check('storage read/write blocks and missing crypto fail closed, no retry token churn', async () => {
    for (const init of [
      ()=>{Storage.prototype.getItem=function(){throw new Error('blocked')}},
      ()=>{Storage.prototype.setItem=function(){throw new Error('blocked')}},
      ()=>{window.crypto.getRandomValues=undefined},
      ()=>{localStorage.setItem('ws-poll-voter','invalid json')},
    ]) {
      const {context,page,calls} = await setup({init});
      await page.locator('#confirm-vote').click();
      assert.match(await status(page),/cannot securely save/);
      assert.equal(calls.length,0);
      assert.equal(await page.locator('#confirm-vote').isDisabled(),true);
      await context.close();
    }
  });
  await check('HTTP failures, false ok, malformed responses never claim success; retry preserves nonce', async () => {
    for (const response of [
      {status:400,body:{error:'Invalid poll',code:'INVALID_POLL'}},
      {status:429,body:{error:'Slow down',code:'RATE_LIMITED'}},
      {status:503,body:{ok:true,duplicate:false,vote:'yes'}},
      {status:200,body:{ok:false,duplicate:false,vote:'yes'}},
      {status:200,body:{ok:true,duplicate:false,vote:'no'}},
      {status:200,body:{ok:true,vote:'yes'}},
      {status:200,body:'not JSON'},
    ]) {
      const {context,page,calls} = await setup({response:n=>n===1?response:{status:200,body:{ok:true,duplicate:true,vote:'yes'}}});
      await page.locator('#confirm-vote').click();
      await page.waitForFunction(() => document.getElementById('msg').textContent.includes('could not confirm'));
      assert.equal(await page.locator('#confirm-vote').isDisabled(),false);
      await page.locator('#confirm-vote').click();
      await page.waitForFunction(() => document.getElementById('msg').textContent.includes('already voted'));
      assert.equal(calls[0].voter,calls[1].voter);
      await context.close();
    }
  });
  await check('network failure has honest retry and no count claim', async () => {
    const {context,page,calls} = await setup({networkError:true,mobile:true});
    await page.locator('#confirm-vote').click();
    await page.waitForFunction(() => document.getElementById('msg').textContent.includes('could not confirm'));
    assert.equal(calls.length,1);
    await page.screenshot({path:shots+'/network-error-mobile.png',fullPage:true});
    await context.close();
  });
  await check('pending disables confirmation; concurrent clicks create only one POST', async () => {
    let release;
    const gate = new Promise(resolve=>release=resolve);
    const {context,page,calls} = await setup({gate});
    await page.locator('#confirm-vote').click();
    assert.equal(await page.locator('#confirm-vote').isDisabled(),true);
    await page.locator('#confirm-vote').click({force:true});
    await page.locator('#confirm-vote').evaluate(el => {el.click();el.click();});
    release();
    await page.waitForFunction(() => document.getElementById('msg').textContent.includes('vote was recorded'));
    assert.equal(calls.length,1);
    await context.close();
  });
  await check('nonce reused across reload; expired nonce replaced with 30 day token', async () => {
    const {context,page,calls} = await setup({init:()=>localStorage.setItem('ws-poll-voter',JSON.stringify({voter:'a'.repeat(32),expires:Date.now()+86400000}))});
    await page.locator('#confirm-vote').click();
    await page.waitForFunction(() => document.getElementById('msg').textContent.includes('vote was recorded'));
    assert.equal(calls[0].voter,'a'.repeat(32));
    await page.reload();
    assert.equal(calls.length,1);
    await page.locator('#confirm-vote').click();
    await page.waitForFunction(() => document.getElementById('msg').textContent.includes('vote was recorded'));
    assert.equal(calls[1].voter,calls[0].voter);
    // Init script resets storage on reload, so expire explicitly in this same document.
    await page.evaluate(() => localStorage.setItem('ws-poll-voter',JSON.stringify({voter:'b'.repeat(32),expires:Date.now()-1})));
    await context.close();
    const expired = await setup({init:()=>localStorage.setItem('ws-poll-voter',JSON.stringify({voter:'b'.repeat(32),expires:Date.now()-1}))});
    await expired.page.locator('#confirm-vote').click();
    await expired.page.waitForFunction(() => document.getElementById('msg').textContent.includes('vote was recorded'));
    assert.notEqual(expired.calls[0].voter,'b'.repeat(32));
    await expired.context.close();
  });
  await check('Nov6 native reader poll matches email links and layout on mobile', async () => {
    const {context,page,calls} = await setup({mobile:true});
    await page.goto(site+'/editions/2026-11-06.html');
    const block = page.locator('#reader-poll');
    assert.match(await block.innerText(),/Should governments strengthen oversight of religious organisations following Kenya's Shakahola case\?/);
    assert.equal(await block.locator('a').count(),2);
    assert.equal(await block.locator('a').first().getAttribute('href'), '/email/thanks.html?poll=kenya-religious-oversight&vote=yes');
    await block.screenshot({path:shots+'/reader-poll-mobile.png'});
    assert.equal(calls.length,0);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);
    await context.close();
  });
  console.log(`${passed} browser scenario groups passed; all requests intercepted locally, zero real votes.`);
  await browser.close();
})().catch(async error => {console.error(error);if(browser)await browser.close();process.exit(1)});
