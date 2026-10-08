import {test,expect} from '@playwright/test';
test('native duration counts independently of clock; unknown sessions do not inflate playtime',async({page})=>{
 const base={profile_uuid:'MOCK_PLAYTIME',profile_label:'MOCK playtime preview',source:'ps5_native',mock:false,artwork_url:null,icon_url:null};
 const rows=[{...base,kind:'trophy',data:{title_id:'MOCK',title:'MOCK game',trophy_id:'0',name:'MOCK trophy',grade:'bronze',unlocked:true}},
  {...base,kind:'activity',data:{title_id:'MOCK',title:'MOCK game',event_id:'MOCK_NATIVE',complete:true,duration_seconds:108,clock:'uncertain',duration_basis:'native_foreground_seconds',consistency:'sqlite_read_transaction',profile_binding:'activity_header_single_local_user',started_at:'2026-10-08T10:47:26Z',ended_at:'2026-10-08T10:49:09Z'}},
  {...base,kind:'activity',data:{title_id:'MOCK',title:'MOCK game',event_id:'MOCK_MISSING',complete:false,duration_seconds:null,clock:'unknown'}},
  {...base,kind:'activity',data:{title_id:'MOCK',title:'MOCK game',event_id:'MOCK_UNVERIFIED',complete:true,duration_seconds:9999,clock:'uncertain'}}];
 rows.push({...base,kind:'activity',data:{...rows[1].data,event_id:'MOCK_NEWER',duration_seconds:3600,started_at:'2026-10-08T12:47:26Z',ended_at:'2026-10-08T13:47:26Z'}} as typeof rows[number]);
 rows.push({...base,kind:'activity',data:{title_id:'MOCK_APP_WITHOUT_TROPHIES',title:'MOCK unwanted app',event_id:'MOCK_ONLY',complete:true,duration_seconds:9999,clock:'trusted'}} as typeof rows[number]);
 await page.route('**/api/account/me',route=>route.fulfill({json:{email:'mock-playtime@example.test'}}));
 await page.route('**/api/account/devices',route=>route.fulfill({json:[]}));
 await page.route('**/api/account/library**',route=>route.fulfill({json:rows}));
 await page.goto('/');
 await expect(page.getByRole('button',{name:'View trophies for MOCK unwanted app',exact:true})).toHaveCount(0);
 await expect(page.getByText('1h 1m recorded across 2 sessions',{exact:true})).toBeVisible();
 await expect(page.getByText(/Last played:/)).toBeVisible();
 await expect(page.locator('.total-playtime')).toHaveText('1h 1m');
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
