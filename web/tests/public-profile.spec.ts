import {test,expect} from '@playwright/test';

test('public profile reuses the library without exposing secret text or private sessions',async({page})=>{
 const player={handle:'fixture_player',display_name:'Fixture player',relationship:'none',request_id:null,viewer_authenticated:false,library_visible:true};
 const entry={profile_uuid:'shared',profile_label:'Fixture player',source:'ps5_native',mock:false,artwork_url:null,icon_url:null};
 const rows=[{...entry,kind:'trophy',data:{title_id:'FIXTURE',title:'Fixture game',trophy_id:'0',grade:'gold',name:'Hidden trophy',description:null,hidden:true,concealed:true,unlocked:true}},
  {...entry,kind:'activity',data:{title_id:'FIXTURE',title:'Fixture game',complete:true,duration_seconds:7200,duration_basis:'shared_total',session_count:3}}];
 await page.route('**/api/players/fixture_player',r=>r.fulfill({json:player}));
 await page.route('**/api/players/fixture_player/library**',r=>r.fulfill({json:rows}));
 await page.goto('/players/fixture_player');
 await expect(page.getByRole('heading',{name:'Fixture player',exact:true})).toBeVisible();
 await expect(page.locator('.total-playtime')).toHaveText('2h 0m');
 await expect(page.getByText('2h 0m recorded across 3 sessions',{exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:'Sign in to send a request',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'View trophies for Fixture game',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Hidden trophy',exact:true})).toBeVisible();
 await expect(page.getByText('Earn this trophy to reveal its name and description.',{exact:true})).toBeVisible();
 await expect(page.getByText('Recorded play sessions',{exact:true})).toHaveCount(0);
 await expect(page.locator('main').getByRole('heading',{name:'Console profiles',exact:true})).toHaveCount(0);
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('owner profile shows the same library and excludes revoked/demo data without test controls',async({page})=>{
 await page.route('**/api/players/fixture_owner',r=>r.fulfill({json:{handle:'fixture_owner',display_name:'Fixture owner',relationship:'self',request_id:null,viewer_authenticated:true,library_visible:true}}));
 await page.route('**/api/account/me',r=>r.fulfill({json:{email:'fixture-owner@example.test'}}));
 await page.route('**/api/account/profile',r=>r.fulfill({json:{handle:'fixture_owner',display_name:'Fixture owner',visibility:'friends'}}));
 await page.route('**/api/account/devices',r=>r.fulfill({json:[{id:'active',profile_label:'Active console',revoked:false,status:'paired',last_sync:1},{id:'revoked',profile_label:'Old console',revoked:true,status:'revoked',last_sync:1}]}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:[...['active','revoked'].map(profile=>({profile_uuid:profile,profile_label:profile,source:'ps5_native',kind:'trophy',mock:false,data:{title_id:profile,title:profile+' game',trophy_id:'0',name:'Fixture trophy',grade:'bronze',unlocked:true}})),{profile_uuid:'active',source:'ps5_native',kind:'trophy',mock:true,data:{title_id:'demo',title:'Demo game',trophy_id:'0',grade:'gold',unlocked:true}}]}));
 await page.goto('/players/fixture_owner');
 await expect(page.getByRole('button',{name:'View trophies for active game',exact:true})).toBeVisible();
 await expect(page.getByText('Old console',{exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'View trophies for revoked game',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'View trophies for Demo game',exact:true})).toHaveCount(0);
 await expect(page.getByRole('checkbox',{name:'Include clearly labeled mock test imports',exact:true})).toHaveCount(0);
 await expect(page.getByRole('link',{name:'Local sample test',exact:true})).toHaveCount(0);
 await expect(page.getByRole('link',{name:'Console profiles',exact:true})).toHaveAttribute('href','/connections');
 await expect(page.getByRole('link',{name:'My profile',exact:true})).toHaveAttribute('href','/players/fixture_owner');
});
