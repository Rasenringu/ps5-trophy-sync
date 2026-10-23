import {test,expect} from '@playwright/test';

test('unverified console dates explain the gap while known foreground time still counts',async({page})=>{
 const base={profile_uuid:'MOCK_CLOCK',profile_label:'MOCK clock fixture',source:'ps5_native',mock:false,artwork_url:null,icon_url:null};
 const game={title_id:'MOCK_CLOCK_GAME',title:'MOCK clock game'};
 const rows=[{...base,kind:'trophy',data:{...game,trophy_id:'0',name:'MOCK unsupported trophy',grade:'bronze',unlocked:null,state_reason:'unsupported_native_flags'}},
  {...base,kind:'activity',data:{...game,event_id:'MOCK_COMPLETE',complete:true,duration_seconds:1236,clock:'uncertain',duration_basis:'native_foreground_seconds',consistency:'sqlite_read_transaction',profile_binding:'activity_header_single_local_user',started_at:null,ended_at:null,timestamp_status:'after_observation'}},
  {...base,kind:'activity',data:{...game,event_id:'MOCK_START_ONLY',complete:false,duration_seconds:null,clock:'unknown',duration_reason:'missing_session_end'}}];
 await page.route('**/api/account/me',r=>r.fulfill({json:{email:'mock-clock@example.test'}}));
 await page.route('**/api/account/devices',r=>r.fulfill({json:[]}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:rows}));
 await page.goto('/');
 await expect(page.locator('.game-card').getByText('0h 20m recorded across 1 sessions',{exact:true})).toBeVisible();
 await expect(page.locator('.game-card .last-played')).toHaveCount(0);
 await page.getByRole('button',{name:'View trophies for '+game.title,exact:true}).click();
 await expect(page.getByText('Console dates could not be verified. Recorded playtime is preserved.',{exact:true})).toBeVisible();
 await expect(page.getByText('The console has not provided a confirmed unlock state.',{exact:true})).toBeVisible();
 await page.getByText('Recorded play sessions',{exact:true}).click();
 await expect(page.getByRole('cell',{name:'20m 36s',exact:true})).toBeVisible();
 await expect(page.getByText('No session end was recorded.',{exact:true})).toBeVisible();
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test('PS4 imported trophy set and its exact activity binding share one card',async({page})=>{
 const base={profile_uuid:'MOCK_PS4',profile_label:'MOCK profile',source:'ps4_bc',mock:false,artwork_url:null,icon_url:null};
 const game={title_id:'NPWR00001_00',title:'MOCK PS4 imported game'};
 const rows=[...Array.from({length:3},(_,id)=>({...base,kind:'trophy',data:{...game,trophy_id:String(id),name:'MOCK trophy '+id,grade:'bronze',unlocked:id===2?null:id===1}})),
  {...base,kind:'activity',data:{...game,event_id:'MOCK_PS4_SESSION',activity_source:'ps5_native',complete:true,duration_seconds:192,clock:'uncertain',duration_basis:'native_foreground_seconds',consistency:'sqlite_read_transaction',profile_binding:'activity_header_single_local_user'}}];
 await page.route('**/api/account/me',route=>route.fulfill({json:{email:'mock-ps4@example.test'}}));
 await page.route('**/api/account/devices',route=>route.fulfill({json:[]}));
 await page.route('**/api/account/library**',route=>route.fulfill({json:rows}));
 await page.goto('/');
 const card=page.locator('.game-card').filter({hasText:game.title});
 await expect(card).toHaveCount(1);await expect(card.locator('.platform-pill')).toHaveText('PS4');
 await expect(card.getByRole('progressbar')).toBeVisible();
 await expect(card.getByText('0h 3m recorded across 1 sessions',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'View trophies for '+game.title,exact:true}).click();
 await expect(page.getByText('MOCK trophy 2',{exact:true})).toBeVisible();
 await expect(page.getByText('State unknown',{exact:true})).toBeVisible();
});
test('native duration counts independently of clock; unknown sessions do not inflate playtime',async({page})=>{
 const base={profile_uuid:'MOCK_PLAYTIME',profile_label:'MOCK playtime preview',source:'ps5_native',mock:false,artwork_url:null,icon_url:null};
 const rows=[{...base,kind:'trophy',data:{title_id:'MOCK',title:'MOCK game',trophy_id:'0',name:'MOCK trophy',grade:'bronze',unlocked:true}},
  {...base,kind:'activity',data:{title_id:'MOCK',title:'MOCK game',event_id:'MOCK_NATIVE',complete:true,duration_seconds:108,clock:'uncertain',duration_basis:'native_foreground_seconds',consistency:'sqlite_read_transaction',profile_binding:'activity_header_single_local_user',started_at:'2026-10-08T10:47:26Z',ended_at:'2026-10-08T10:49:09Z'}},
  {...base,kind:'activity',data:{title_id:'MOCK',title:'MOCK game',event_id:'MOCK_MISSING',complete:false,duration_seconds:null,clock:'unknown'}},
  {...base,kind:'activity',data:{title_id:'MOCK',title:'MOCK game',event_id:'MOCK_UNVERIFIED',complete:true,duration_seconds:9999,clock:'uncertain'}}];
 rows.push({...base,kind:'activity',data:{...rows[1].data,event_id:'MOCK_NEWER',duration_seconds:3600,started_at:'2026-10-08T12:47:26Z',ended_at:'2026-10-08T13:47:26Z'}} as typeof rows[number]);
 rows.push({...base,kind:'activity',data:{title_id:'CUSA03804',title:'MOCK PS4 playtime game',event_id:'MOCK_ONLY',complete:true,duration_seconds:9999,clock:'uncertain',duration_basis:'native_foreground_seconds',consistency:'sqlite_read_transaction',profile_binding:'activity_header_single_local_user'}} as typeof rows[number]);
 await page.route('**/api/account/me',route=>route.fulfill({json:{email:'mock-playtime@example.test'}}));
 await page.route('**/api/account/devices',route=>route.fulfill({json:[]}));
 await page.route('**/api/account/library**',route=>route.fulfill({json:rows}));
 await page.goto('/');
 await expect(page.getByRole('button',{name:'View game details for MOCK PS4 playtime game',exact:true})).toBeVisible();
 const activityCard=page.locator('.game-card').filter({hasText:'MOCK PS4 playtime game'});
 await expect(activityCard.locator('.platform-pill')).toHaveText('PS4');
 await expect(activityCard.getByRole('progressbar')).toHaveCount(0);
 await expect(activityCard.locator('.grade-counts')).toHaveCount(0);
 await expect(page.getByText('1h 1m recorded across 2 sessions',{exact:true})).toBeVisible();
 await expect(page.getByText(/Last played:/).first()).toBeVisible();
 await expect(page.locator('.total-playtime')).toHaveText('3h 48m');
 await expect(page.locator('.game-grid')).toHaveClass(/compact-list/);
 await page.getByRole('button',{name:'Cards',exact:true}).click();
 await page.reload();
 await expect(page.getByRole('button',{name:'Cards',exact:true})).toHaveAttribute('aria-pressed','true');
 await page.getByRole('button',{name:'Compact list',exact:true}).click();
 await page.getByRole('button',{name:'View trophies for MOCK game',exact:true}).click();
 await expect(page.getByText('Recorded playtime',{exact:true})).toBeVisible();
 await page.getByText('Recorded play sessions',{exact:true}).click();
 await expect(page.getByRole('cell',{name:'1m 48s',exact:true})).toBeVisible();
 await expect(page.locator('tbody tr').nth(0).locator('td').nth(2)).toHaveText('60m 0s');
 await expect(page.locator('tbody tr').nth(1).locator('td').nth(2)).toHaveText('1m 48s');
 await expect(page.getByRole('cell',{name:'9999s',exact:true})).toHaveCount(0);
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('playtime-only PS4 entry displays its authorized application icon',async({page})=>{
 const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jJXcAAAAASUVORK5CYII=','base64');
 await page.route('**/api/account/me',route=>route.fulfill({json:{email:'mock-art@example.test'}}));
 await page.route('**/api/account/devices',route=>route.fulfill({json:[]}));
 await page.route('**/api/account/library**',route=>route.fulfill({json:[{
  profile_uuid:'MOCK',profile_label:'MOCK profile',source:'ps5_native',mock:false,kind:'activity',
  artwork_url:'/api/account/device-artwork/MOCK_IMAGE',icon_url:null,
  data:{title_id:'CUSA03804',title:'MOCK Attack on Titan',complete:true,duration_seconds:192,
   clock:'uncertain',duration_basis:'native_foreground_seconds',consistency:'sqlite_read_transaction',profile_binding:'activity_header_single_local_user'}}]}));
 await page.route('**/api/account/device-artwork/MOCK_IMAGE',route=>route.fulfill({contentType:'image/png',body:png}));
 await page.goto('/');
 const card=page.locator('.game-card').filter({hasText:'MOCK Attack on Titan'});
 await expect(card.getByRole('img',{name:'MOCK Attack on Titan'})).toBeVisible();
 await expect(card.locator('.platform-pill')).toHaveText('PS4');
 await expect(card.getByRole('progressbar')).toHaveCount(0);
});
