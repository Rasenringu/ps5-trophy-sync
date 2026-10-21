import {test,expect,chromium} from '@playwright/test';
import {mkdtemp,cp,readFile,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

test('real MV3 runtime uses provider-tab cookies and sends only scoped identity and verified receipts',async()=>{
 const temp=await mkdtemp(join(tmpdir(),'synthetic-hltb-'));
 const extension=join(temp,'extension');await cp(join(process.cwd(),'connector/hltb-browser'),extension,{recursive:true});
 const manifest=JSON.parse(await readFile(join(extension,'manifest.json'),'utf8'));
 // Pregrant access to this intercepted synthetic host; no user permission UI.
 // Runtime JS is the exact shipped code; never use a real provider account.
 manifest.host_permissions.push('https://synthetic.trophysync.test/*');
 await writeFile(join(extension,'manifest.json'),JSON.stringify(manifest));
 const context=await chromium.launchPersistentContext(join(temp,'profile'),{channel:'chromium',headless:true,
  args:['--no-sandbox','--disable-extensions-except='+extension,'--load-extension='+extension]});
 try{
  let providerEntry:any=null;let writes=0;let claimed:any,received:any;let issued=false;
  const job={id:'a'.repeat(64),hltb_id:123,title:'SYNTHETIC Game',platform:'PlayStation 5',seconds:3500};
  await context.addCookies([{name:'synthetic_session',value:'SYNTHETIC_HTTPONLY_COOKIE',domain:'howlongtobeat.com',path:'/',secure:true,httpOnly:true,sameSite:'Lax'}]);
  await context.route('https://howlongtobeat.com/**',async route=>{
   const path=new URL(route.request().url()).pathname;
   expect(route.request().headers().cookie).toContain('SYNTHETIC_HTTPONLY_COOKIE');
   if(path==='/api/user')return route.fulfill({json:{data:[{user_id:1234,user_name:'SYNTHETIC'}]}});
   if(path==='/api/user/1234/games/list')return route.fulfill({json:{data:{gamesList:providerEntry?[{id:77,game_id:123,platform:'PlayStation 5'}]:[],total:providerEntry?1:0}}});
   if(path==='/api/submit'){writes++;providerEntry={...route.request().postDataJSON(),submissionId:77};return route.fulfill({json:{status:'success'}});}
   if(path==='/submit/edit/77')return route.fulfill({contentType:'text/html',body:'<script id="__NEXT_DATA__" type="application/json">'+JSON.stringify({props:{pageProps:{editData:providerEntry}}})+'</script>'});
   return route.fulfill({contentType:'text/html',body:'<h1>SYNTHETIC provider page</h1>'});
  });
  await context.route('https://synthetic.trophysync.test/**',async route=>{
   const request=route.request();const path=new URL(request.url()).pathname;
   expect(request.headers().cookie||'').not.toContain('SYNTHETIC_HTTPONLY_COOKIE');
   if(path.endsWith('/claim')){claimed=request.postDataJSON();return route.fulfill({json:{token:'SYNTHETIC_SCOPED_TOKEN',expires:Math.floor(Date.now()/1000)+3600,username:'SYNTHETIC'}});}
   expect(request.headers().authorization).toBe('Bearer SYNTHETIC_SCOPED_TOKEN');
   if(path.endsWith('/next')){const next=issued?null:job;issued=true;return route.fulfill({json:{job:next,user_id:1234,reconcile_only:false}});}
   if(path.endsWith('/receipt')){received=request.postDataJSON();return route.fulfill({json:received});}
   throw new Error('Unexpected synthetic server path '+path);
  });
  const provider=await context.newPage();await provider.goto('https://howlongtobeat.com/');
  const worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker');
  const extensionId=new URL(worker.url()).host;
  const popup=await context.newPage();await popup.goto('chrome-extension://'+extensionId+'/popup.html');
  await popup.locator('#origin').fill('https://synthetic.trophysync.test');
  await popup.locator('#code').fill('SYNTHETIC_SINGLE_USE_CODE_1234567890');
  await popup.getByRole('button',{name:'Connect',exact:true}).click();
  await expect(popup.locator('#result')).toHaveText('Connected as SYNTHETIC.');
  expect(claimed).toEqual({code:'SYNTHETIC_SINGLE_USE_CODE_1234567890',user_id:1234,username:'SYNTHETIC'});
  await popup.getByRole('button',{name:'Sync queued updates',exact:true}).click();
  await expect(popup.locator('#result')).toHaveText('1 update(s) verified. Refresh TrophySync Integrations.');
  expect(writes).toBe(1);expect(received).toEqual({job_id:job.id,state:'synced',submission_id:77,seconds:3500,error:null});
  expect(providerEntry.general.progress).toEqual({hours:0,minutes:58,seconds:20});
  expect(providerEntry.lists.completed).toBe(false);
 }finally{await context.close();await rm(temp,{recursive:true,force:true});}
});
