/* Fully intercepted native form tests. Never contacts an ESP or submits a subscriber. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=process.cwd(),config=JSON.parse(fs.readFileSync('settings/newsletter-form.json','utf8'));
const pages=['index.html','archive.html',...fs.readdirSync('editions').filter(x=>/^\d{4}-\d{2}-\d{2}\.html$/.test(x)).map(x=>'editions/'+x),'email/thanks.html'];
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 fs.mkdirSync('/tmp/ws-intake-screens',{recursive:true});
 let scenarios=0;
 for(const javascript of [true,false]){
  const context=await browser.newContext({javaScriptEnabled:javascript,viewport:{width:375,height:900}});
  let posts=[],unexpected=[],mode='success';
  await context.addInitScript(()=>{
   // A stale old-provider queue must never trigger a subscription.
   sessionStorage.setItem('ws-sub','stale@example.invalid');
  });
  await context.route('**/*',async route=>{
   const request=route.request(),url=new URL(request.url());
   if(url.href===config.action){
    posts.push({method:request.method(),fields:Object.fromEntries(new URLSearchParams(request.postData()))});
    assert.equal(request.method(),'POST');
    // A fresh navigation is intercepted as well. Playwright does not re-route
    // an HTTP redirect chain, so do not use a 302 to an external test URL.
    if(mode==='success')return route.fulfill({status:200,contentType:'text/html',body:'<!doctype html><meta http-equiv="refresh" content="0;url='+config.hidden.redirect+'">'});
    return route.fulfill({status:400,contentType:'text/html',body:'<!doctype html><html lang="en"><body><h1>Unable to subscribe. Please try again.</h1></body></html>'});
   }
   if(url.href===config.hidden.redirect)return route.fulfill({status:200,contentType:'text/html',body:'<!doctype html><html lang="en"><body><h1>Mock provider response</h1></body></html>'});
   if(url.hostname!=='worldskim.test'){
    if(['xhr','fetch','script'].includes(request.resourceType()))unexpected.push(url.href);
    return route.abort();
   }
   const file=path.join(root,decodeURIComponent(url.pathname));
   if(!fs.existsSync(file)||!fs.statSync(file).isFile())return route.fulfill({status:404,body:''});
   const type={'.html':'text/html','.css':'text/css','.js':'application/javascript','.png':'image/png','.woff':'font/woff'}[path.extname(file)]||'application/octet-stream';
   return route.fulfill({body:fs.readFileSync(file),contentType:type});
  });
  const page=await context.newPage();
  for(const name of pages){
   const before=posts.length;
   await page.goto('https://worldskim.test/'+name);
   const count=await page.locator('form[data-newsletter-signup]').count();
   assert.equal(count,name==='index.html'||name==='archive.html'?2:1,name);
   assert.equal(before,posts.length,'page load must not submit');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,name+' overflow');
   for(let index=0;index<count;index++){
    const beforeLoad=posts.length;
    await page.goto('https://worldskim.test/'+name);
    assert.equal(posts.length,beforeLoad,'reload with stale queue must not submit');
    const form=page.locator('form[data-newsletter-signup]').nth(index);
    const input=form.locator('input[type=email]'),button=form.locator('button[type=submit]');
    const start=posts.length;
    await input.fill('bad-email');
    await button.click();
    assert.equal(posts.length,start,'invalid must not submit');
    if(javascript){
     assert.equal(await input.getAttribute('aria-invalid'),'true');
     assert.match(await form.locator('[data-signup-message]').textContent(),/valid email address/);
    }
    await input.fill('qa@example.invalid');
    if(javascript)assert.equal(await input.getAttribute('aria-invalid'),null);
    await Promise.all([page.waitForURL(config.hidden.redirect),button.click()]);
    assert.equal(posts.length,start+1,'one explicit click, one native POST');
    assert.deepEqual(posts.at(-1),{method:'POST',fields:{...config.hidden,email:'qa@example.invalid'}});
    assert.equal(await page.locator('h1').textContent(),'Mock provider response');
    scenarios++;
   }
  }
  // Server-side failure is shown by the provider response, never fake local success.
  mode='error';
  await page.goto('https://worldskim.test/index.html');
  const form=page.locator('form[data-newsletter-signup="main"]');
  await form.locator('input[type=email]').fill('qa@example.invalid');
  await Promise.all([page.waitForURL(config.action),form.locator('button').click()]);
  assert.match(await page.locator('h1').textContent(),/Unable to subscribe/);
  assert.doesNotMatch(await page.textContent('body'),/You're in|Check your inbox|Signing you up/);
  assert.deepEqual(unexpected,[],'no old ESP calls, XHR or scripts');
  await page.goto('https://worldskim.test/index.html');
  await page.screenshot({path:`/tmp/ws-intake-screens/home-mobile-js-${javascript}.png`,fullPage:false});
  await page.locator('footer').screenshot({path:`/tmp/ws-intake-screens/footer-mobile-js-${javascript}.png`});
  await context.close();
 }
 await browser.close();
 console.log(`PASS ${scenarios} native form submissions intercepted across all pages, with and without JS; required/email validation, accessible errors, exact verified payload, success redirect and provider failure, no automatic signup or real network writes.`);
})();
