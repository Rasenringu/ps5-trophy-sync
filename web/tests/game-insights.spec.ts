import {test,expect} from '@playwright/test';
import type {Page} from '@playwright/test';

// All routes below are intercepted synthetic fixtures; no provider/console calls.
const completion={hltb_id:123,main_seconds:7200,extra_seconds:null,completionist_seconds:36000,url:'https://howlongtobeat.com/game/123',updated:1792600000};
const listing={id:123,title:'SYNTHETIC Game',platform:'PS5',url:'https://platprices.com/game/123'};
function insights(selected=false){return {howlongtobeat:{...completion},rarity:{status:selected?'ok':'not_selected',listing:selected?listing:null,rates:selected?{'0':0,'1':null}:{},fetched:1792600000,stale:false}};}
async function fixture(page:Page,{many=false,shared=false}:{many?:boolean;shared?:boolean}={}){
 const base={profile_uuid:shared?'shared':'SYNTHETIC_PROFILE',profile_label:'SYNTHETIC profile',source:'ps5_native',kind:'trophy',mock:false,artwork_url:null,icon_url:null};
 const rows=Array.from({length:many?40:1},(_,game)=>Array.from({length:many?30:3},(_,trophy)=>({...base,data:{title_id:'SET_'+game,title:'SYNTHETIC Game '+game,trophy_id:String(trophy),name:trophy===1?'Hidden trophy':'SYNTHETIC trophy '+trophy,hidden:trophy===1,concealed:trophy===1,grade:'bronze',unlocked:false}}))).flat();
 await page.route('**/api/account/me',r=>r.fulfill({json:{email:'synthetic@example.test'}}));
 await page.route('**/api/account/profile',r=>r.fulfill({json:{handle:'synthetic',display_name:'SYNTHETIC owner'}}));
 await page.route('**/api/account/devices',r=>r.fulfill({json:[]}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:rows}));
 await page.route('**/api/players/synthetic/library**',r=>r.fulfill({json:rows}));
 await page.route('**/api/players/synthetic',r=>r.fulfill({json:{handle:'synthetic',display_name:'SYNTHETIC owner',library_visible:true,relationship:'none',visibility:'public',viewer_authenticated:false}}));
 return rows;
}

test('manual estimates preserve unknowns; reviewed provider rates preserve zero and hide secret metadata',async({page})=>{
 await fixture(page);let data=insights();let saved:any;let selected=0;
 await page.route('**/api/account/games/insights?**',r=>r.fulfill({json:data}));
 await page.route('**/api/account/games/howlongtobeat',r=>{saved=r.request().postDataJSON();data.howlongtobeat={...data.howlongtobeat,...saved};return r.fulfill({json:data});});
 await page.route('**/api/account/integrations/platprices/search?**',r=>r.fulfill({json:{status:'ok',games:[listing],stale:false}}));
 await page.route('**/api/account/games/platprices',r=>{selected++;data=insights(r.request().postDataJSON().platprices_id!==null);return r.fulfill({json:data});});
 await page.goto('/');await page.getByRole('button',{name:'View trophies for SYNTHETIC Game 0',exact:true}).click();
 await expect(page.locator('.completion-times dd')).toHaveText(['2 hours','Unknown','10 hours']);
 await page.getByRole('button',{name:'Edit completion times',exact:true}).click();
 await page.getByLabel('Main Story (hours)',{exact:true}).fill('3.5');
 await page.getByLabel('Completionist (100%) (hours)',{exact:true}).fill('');
 await page.getByRole('button',{name:'Save completion times',exact:true}).click();
 expect(saved).toEqual({source:'ps5_native',title_id:'SET_0',hltb_id:123,main_seconds:12600,extra_seconds:null,completionist_seconds:null});
 await expect(page.getByRole('status')).toHaveText('Completion times saved.');
 expect(selected).toBe(0);
 await page.getByRole('button',{name:'Find trophy earn rates',exact:true}).click();
 await expect(page.locator('.provider-candidates')).toBeVisible();
 await page.locator('.provider-candidates button').click();
 expect(selected).toBe(1);
 await expect(page.locator('.trophy-rarity').first()).toContainText('0% earned');
 await expect(page.locator('.trophy-rarity').first()).toContainText('100% not earned');
 await expect(page.locator('.trophy-rarity').nth(1)).toHaveText('Earn rate unknown');
 await expect(page.locator('.trophy-rarity').nth(2)).toHaveText('Earn rate unknown');
 await expect(page.getByRole('heading',{name:'Hidden trophy',exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:'Powered by PlatPrices',exact:true})).toHaveAttribute('href',listing.url);
 if(process.env.INSIGHTS_SCREENSHOT_DIR)await page.screenshot({path:process.env.INSIGHTS_SCREENSHOT_DIR+'/game-insights.png',fullPage:true});
 await page.getByRole('button',{name:'Remove listing',exact:true}).click();
 await expect(page.locator('.trophy-rarity')).toHaveCount(0);
});

test('shared viewers see estimates and cached rates without editing or provider searches',async({page})=>{
 await fixture(page,{shared:true});await page.route('**/api/players/synthetic/games/insights?**',r=>r.fulfill({json:insights(true)}));
 await page.goto('/players/synthetic');await page.getByRole('button',{name:'View trophies for SYNTHETIC Game 0',exact:true}).click();
 await expect(page.locator('.completion-times dd').first()).toHaveText('2 hours');
 await expect(page.getByRole('button',{name:'Edit completion times',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Change listing',exact:true})).toHaveCount(0);
 await expect(page.locator('.trophy-rarity').first()).toContainText('0% earned');
});

test('mobile dialog keeps the page position, one scrolling surface, and a visible SVG close button',async({page,isMobile,browserName})=>{
 await page.setViewportSize({width:390,height:844});await fixture(page,{many:true});
 await page.route('**/api/account/games/insights?**',r=>r.fulfill({json:insights(true)}));
 await page.goto('/');
 const opener=page.getByRole('button',{name:'View trophies for SYNTHETIC Game 16',exact:true});
 await opener.scrollIntoViewIfNeeded();const before=await page.evaluate(()=>scrollY);
 await opener.click();const dialog=page.getByRole('dialog');await expect(dialog).toBeVisible();
 await expect(page.locator('body')).toHaveCSS('position','fixed');
 const close=page.getByRole('button',{name:'Close trophies',exact:true});await expect(close.locator('svg')).toBeVisible();await expect(close).not.toHaveText('?');
 if(isMobile&&browserName==='webkit')await dialog.evaluate(el=>el.scrollBy(0,1100));
 else{const bounds=await dialog.boundingBox();await page.mouse.move(bounds!.x+bounds!.width/2,bounds!.y+bounds!.height*.7);await page.mouse.wheel(0,1100);}
 await expect.poll(()=>dialog.evaluate(el=>el.scrollTop)).toBeGreaterThan(0);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 const lockedTop=await page.locator('body').evaluate(el=>el.style.top);expect(lockedTop).toBe('-'+before+'px');
 for(const viewport of [{width:844,height:390},{width:320,height:568},{width:390,height:844}]){
  await page.setViewportSize(viewport);await expect(close).toBeInViewport();
  expect(await dialog.evaluate(el=>el.scrollWidth<=el.clientWidth)).toBe(true);
 }
 if(process.env.INSIGHTS_SCREENSHOT_DIR)await page.screenshot({path:process.env.INSIGHTS_SCREENSHOT_DIR+'/mobile-dialog.png'});
 await close.click();await expect(dialog).toHaveCount(0);await expect(opener).toBeFocused();
 expect(Math.abs((await page.evaluate(()=>scrollY))-before)).toBeLessThan(3);
});

test('switching games ignores a delayed provider response from the previous dialog',async({page})=>{
 await fixture(page,{many:true});let release:()=>void=()=>{};const gate=new Promise<void>(resolve=>{release=resolve;});
 await page.route('**/api/account/games/insights?**',async r=>{
  if(r.request().url().includes('SET_0')){await gate;await r.fulfill({json:insights(true)}).catch(()=>{});}else await r.fulfill({json:insights()});
 });
 await page.goto('/');await page.getByRole('button',{name:'View trophies for SYNTHETIC Game 0',exact:true}).click();
 await page.getByRole('button',{name:'Close trophies',exact:true}).click();
 await page.getByRole('button',{name:'View trophies for SYNTHETIC Game 1',exact:true}).click();
 await expect(page.locator('.completion-times')).toBeVisible();release();
 await expect(page.locator('.trophy-rarity')).toHaveCount(0);
});

test('integration setup describes HLTB account-sync limits and the free provider requirement',async({page})=>{
 await page.route('**/api/account/integrations',r=>r.fulfill({json:{platprices:{configured:false}}}));
 await page.goto('/integrations');
 await expect(page.getByRole('heading',{name:'Integrations',exact:true})).toBeVisible();
 await expect(page.getByText('Server setup needed',{exact:true})).toBeVisible();
 await expect(page.getByText('HowLongToBeat account linking and upload are not implemented yet. Use the game link to submit playtime manually.',{exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:'Export my playtime (CSV)',exact:true})).toHaveAttribute('href','/api/account/integrations/playtime.csv');
});

test('automatic HLTB estimates load with provenance and edition selection, without account credentials',async({page})=>{
 await fixture(page);
 let data:any={...insights(),howlongtobeat:{...completion,entry_mode:'provider',status:'ok',main_seconds:900,extra_seconds:null,stale:false,candidates:[]}};
 const candidate={hltb_id:456,title:'SYNTHETIC Game alternate edition',platforms:['PlayStation 5'],url:'https://howlongtobeat.com/game/456'};
 let selection:any;
 await page.route('**/api/account/games/insights?**',r=>r.fulfill({json:data}));
 await page.route('**/api/account/integrations/howlongtobeat/search?**',r=>r.fulfill({json:{status:'ok',candidates:[candidate]}}));
 await page.route('**/api/account/games/howlongtobeat/automatic',r=>{selection=r.request().postDataJSON();data.howlongtobeat={...data.howlongtobeat,...candidate,main_seconds:3600};return r.fulfill({json:data});});
 await page.goto('/');await page.getByRole('button',{name:'View trophies for SYNTHETIC Game 0',exact:true}).click();
 await expect(page.locator('.completion-times dd').first()).toHaveText('0.25 hours');
 await expect(page.getByText('Community estimates from HowLongToBeat, across platforms. Completionist time is not a platinum estimate.',{exact:false})).toBeVisible();
 await expect(page.locator('.provider-candidates')).toHaveCount(0);
 await page.getByRole('button',{name:'Match a HowLongToBeat game',exact:true}).click();
 await page.getByRole('button',{name:/SYNTHETIC Game alternate edition/}).click();
 expect(selection).toEqual({source:'ps5_native',title_id:'SET_0',hltb_id:456});
 await expect(page.locator('.completion-times dd').first()).toHaveText('1 hour');
 await expect(page.getByRole('link',{name:'View on HowLongToBeat',exact:false})).toHaveAttribute('href',candidate.url);
 await expect(page.locator('.hltb-source-title')).toHaveText(candidate.title);
 if(process.env.INSIGHTS_SCREENSHOT_DIR)await page.screenshot({path:process.env.INSIGHTS_SCREENSHOT_DIR+'/automatic-hltb.png'});
 await expect(page.locator('input[type="password"]')).toHaveCount(0);
});
