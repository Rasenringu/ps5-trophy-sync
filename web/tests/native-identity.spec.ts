import {test,expect} from '@playwright/test';

test('merged regional PS5 game shows trophies and all shared session totals on one card',async({page})=>{
 // Conspicuously synthetic API response; no user account or console contact.
 const title='MOCK Demon Slayer -Kimetsu no Yaiba- The Hinokami Chronicles';
 const base={profile_uuid:'shared',profile_label:'MOCK regional-release fixture',source:'ps5_native',mock:false,artwork_url:null,icon_url:null};
 const game={title_id:'NPWR23868_00',title};
 const rows=[...Array.from({length:47},(_,index)=>({...base,kind:'trophy',data:{...game,trophy_id:String(index),
  name:'MOCK trophy '+index,grade:'bronze',unlocked:index===0}})),
  {...base,kind:'activity',data:{...game,complete:true,duration_basis:'shared_total',duration_seconds:2248,session_count:3}}];
 await page.route('**/api/players/mock_regional',r=>r.fulfill({json:{handle:'mock_regional',display_name:'MOCK player',
  relationship:'none',viewer_authenticated:false,library_visible:true}}));
 await page.route('**/api/players/mock_regional/library**',r=>r.fulfill({json:rows}));
 await page.goto('/players/mock_regional');
 await expect(page.locator('.game-card')).toHaveCount(1);
 await expect(page.locator('.game-card .platform-pill')).toHaveText('PS5');
 await expect(page.getByText('1/47 recorded trophies unlocked',{exact:true})).toBeVisible();
 await expect(page.getByText('0h 37m recorded across 3 sessions',{exact:true})).toBeVisible();
 await expect(page.locator('.total-playtime')).toHaveText('0h 37m');
 await page.getByRole('button',{name:'View trophies for '+title,exact:true}).click();
 await expect(page.locator('.trophy-list li')).toHaveCount(47);
 await expect(page.getByRole('dialog').getByText('0h 37m',{exact:true})).toBeVisible();
});
