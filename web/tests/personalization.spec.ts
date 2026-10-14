import {test,expect} from '@playwright/test';

async function previewLabel(page:import('@playwright/test').Page){await page.evaluate(()=>{const banner=document.createElement('div');banner.textContent='SYNTHETIC UI PREVIEW • NO CONSOLE EVIDENCE';banner.style.cssText='padding:10px;text-align:center;background:#173b60;color:white;font:12px system-ui';document.querySelector('main')?.prepend(banner);(document.activeElement as HTMLElement)?.blur();window.scrollTo(0,0);});}

test('recent sort, one platform badge, hide/unhide and responsive library',async({page})=>{
 const base={profile_uuid:'fixture',profile_label:'Synthetic profile',source:'ps5_native',mock:false,artwork_url:null};
 let hidden=false;
 const rows=()=>['Z Recent','A Older','Unknown'].map((title,i)=>({...base,game_hidden:i===0&&hidden,kind:'activity',data:{title_id:'GAME'+i,title,complete:true,clock:'trusted',duration_seconds:120,started_at:i===2?null:`2026-10-${14-i}T10:00:00Z`}}));
 await page.route('**/api/account/me',r=>r.fulfill({json:{email:'synthetic@example.test'}}));
 await page.route('**/api/account/profile',r=>r.fulfill({json:{handle:'fixture',display_name:'Synthetic profile'}}));
 await page.route('**/api/account/devices',r=>r.fulfill({json:[{id:'fixture',profile_label:'Synthetic profile',revoked:false,last_sync:1}]}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:rows()}));
 await page.route('**/api/account/games/visibility',r=>{hidden=r.request().postDataJSON().hidden;return r.fulfill({json:{hidden}});});
 await page.goto('/');
 await expect(page.getByRole('combobox',{name:'Sort games'})).toHaveValue('recent');
 await expect(page.locator('.game-card h2')).toHaveText(['Z Recent','A Older','Unknown']);
 await expect(page.locator('.game-card').first().getByText('PS5',{exact:true})).toHaveCount(1);
 await page.getByRole('button',{name:'Hide Z Recent',exact:true}).click();
 await expect(page.locator('.game-card h2')).toHaveText(['A Older','Unknown']);
 await page.getByRole('button',{name:/^Hidden Games/}).click();
 await expect(page.locator('.game-card h2')).toHaveText(['Z Recent']);
 await page.reload();
 await expect(page.locator('.game-card h2')).toHaveText(['A Older','Unknown']);
 await page.getByRole('button',{name:/^Hidden Games/}).click();
 await page.getByRole('button',{name:'Unhide Z Recent',exact:true}).click();
 await expect(page.getByRole('heading',{name:'No hidden games',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Game collection',exact:true}).click();
 await expect(page.locator('.game-card h2')).toHaveText(['Z Recent','A Older','Unknown']);
 for(const width of [1440,820,390]){
  await page.setViewportSize({width,height:900});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await expect(page.getByRole('button',{name:'Hide Z Recent',exact:true})).toBeVisible();
 }
 await page.getByRole('button',{name:'Cards',exact:true}).click();
 await previewLabel(page);
 await page.screenshot({path:'/tmp/ui-rework/library-mobile.png',fullPage:true});
 await page.setViewportSize({width:1440,height:1000});
 await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:'/tmp/ui-rework/library-desktop.png',fullPage:true});
 await page.getByRole('button',{name:'View game details for Z Recent',exact:true}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.getByRole('dialog').getByRole('button',{name:'Hide game',exact:true}).click();
 await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('profile preview and favorite showcase save and render safely',async({page})=>{
 let profile={handle:'fixture',display_name:'Synthetic player',visibility:'public',bio:'',theme:'blue',avatar:'trophy',favorite:null as null|{source:string;title_id:string}};
 await page.route('**/api/account/profile',r=>{if(r.request().method()==='POST')profile={...profile,...r.request().postDataJSON()};return r.fulfill({json:profile});});
 await page.route('**/api/account/friends',r=>r.fulfill({json:{friends:[],incoming:[],outgoing:[],denied:[]}}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:[{source:'ps5_native',kind:'activity',mock:false,data:{title_id:'SET',title:'Synthetic favorite'}},{source:'ps5_native',game_hidden:true,kind:'activity',mock:false,data:{title_id:'HIDDEN',title:'Hidden fixture'}}]}));
 await page.route('**/api/players/fixture',r=>r.fulfill({json:{...profile,relationship:'none',viewer_authenticated:false,library_visible:true,favorite:profile.favorite?{...profile.favorite,title:'Synthetic favorite',artwork_url:null}:null}}));
 await page.route('**/api/players/fixture/library**',r=>r.fulfill({json:[]}));
 await page.goto('/friends');
 await page.getByRole('textbox',{name:'About you'}).fill('<script>synthetic</script>\nPlatinum hunter.');
 await page.getByRole('combobox',{name:'Profile theme'}).selectOption('violet');
 await page.getByRole('combobox',{name:'Avatar style'}).selectOption('orbit');
 await page.getByRole('combobox',{name:'Favorite game'}).selectOption('ps5_native|SET');
 await expect(page.getByRole('combobox',{name:'Favorite game'}).locator('option')).toHaveCount(2);
 await expect(page.locator('.profile-preview')).toHaveClass(/theme-violet/);
 await page.getByRole('button',{name:'Save profile',exact:true}).click();
 await expect(page.getByRole('status')).toHaveText('Profile saved');
 await page.getByRole('link',{name:/Open your profile/}).click();
 await expect(page.locator('.profile-hero')).toHaveClass(/theme-violet/);
 await expect(page.locator('.favorite-showcase')).toContainText('Synthetic favorite');
 await expect(page.locator('.profile-bio')).toHaveText('<script>synthetic</script>\nPlatinum hunter.');
 await expect(page.locator('.profile-bio script')).toHaveCount(0);
 await previewLabel(page);
 for(const width of [1440,390]){await page.setViewportSize({width,height:900});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:`/tmp/ui-rework/profile-${width}.png`,fullPage:true});}
});

test('hiding the featured game updates the owner showcase immediately',async({page})=>{
 let hidden=false;
 const entry={profile_uuid:'fixture',profile_label:'Synthetic profile',source:'ps5_native',kind:'activity',mock:false,data:{title_id:'SET',title:'Synthetic favorite',complete:false}};
 await page.route('**/api/account/me',r=>r.fulfill({json:{email:'synthetic@example.test'}}));
 await page.route('**/api/account/profile',r=>r.fulfill({json:{handle:'fixture',display_name:'Synthetic player'}}));
 await page.route('**/api/account/devices',r=>r.fulfill({json:[]}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:[{...entry,game_hidden:hidden}]}));
 await page.route('**/api/account/games/visibility',r=>{hidden=r.request().postDataJSON().hidden;return r.fulfill({json:{hidden}});});
 await page.route('**/api/players/fixture',r=>r.fulfill({json:{handle:'fixture',display_name:'Synthetic player',relationship:'self',viewer_authenticated:true,library_visible:true,favorite:hidden?null:{source:'ps5_native',title_id:'SET',title:'Synthetic favorite',artwork_url:null}}}));
 await page.goto('/players/fixture');
 await expect(page.locator('.favorite-showcase')).toBeVisible();
 await page.getByRole('button',{name:'Hide Synthetic favorite',exact:true}).click();
 await expect(page.locator('.favorite-showcase')).toHaveCount(0);
 await page.getByRole('button',{name:/^Hidden Games/}).click();
 await page.getByRole('button',{name:'Unhide Synthetic favorite',exact:true}).click();
 await expect(page.locator('.favorite-showcase')).toBeVisible();
});
