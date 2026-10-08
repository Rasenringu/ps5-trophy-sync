import {test,expect} from '@playwright/test';

test('secret names and locked artwork stay hidden; earned status and grade are explicit',async({page})=>{
 let lockedRequests=0;
 await page.route('**/forbidden-locked-icon.png',route=>{lockedRequests++;return route.abort();});
 const base={profile_uuid:'MOCK_PREVIEW',profile_label:'MOCK preview',source:'ps5_native',kind:'trophy',mock:false,artwork_url:null};
 const rows=[
  {...base,icon_url:'/forbidden-locked-icon.png',data:{title_id:'MOCK_SECRET',title:'MOCK secret game',trophy_id:'0',name:'DO NOT REVEAL THIS NAME',description:'DO NOT REVEAL THIS DESCRIPTION',hidden:true,grade:'gold',unlocked:false}},
  {...base,icon_url:null,data:{title_id:'MOCK_SECRET',title:'MOCK secret game',trophy_id:'1',name:'MOCK earned trophy',description:'MOCK earned description',hidden:true,grade:'bronze',unlocked:true,unlocked_at:null,clock:'unknown'}}];
 await page.route('**/api/account/me',route=>route.fulfill({json:{email:'mock-preview@example.test'}}));
 await page.route('**/api/account/devices',route=>route.fulfill({json:[]}));
 await page.route('**/api/account/library**',route=>route.fulfill({json:rows}));
 await page.goto('/');
 await page.getByRole('button',{name:'View trophies for MOCK secret game',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Hidden trophy',exact:true})).toBeVisible();
 await expect(page.getByText('DO NOT REVEAL THIS NAME',{exact:true})).toHaveCount(0);
 await expect(page.getByText('DO NOT REVEAL THIS DESCRIPTION',{exact:true})).toHaveCount(0);
 await expect(page.getByRole('heading',{name:'MOCK earned trophy',exact:true})).toBeVisible();
 await expect(page.getByText('MOCK earned description',{exact:true})).toBeVisible();
 await expect(page.getByText('✓ Earned',{exact:true})).toBeVisible();
 await expect(page.locator('.trophy-grade.gold')).toHaveText('Gold');
 await expect(page.locator('.trophy-grade.bronze')).toHaveText('Bronze');
 await expect(page.getByText('Rarity unavailable',{exact:true})).toHaveCount(0);
 await expect(page.getByText('Unlocked',{exact:true})).toHaveCount(0);
 await expect(page.getByText(/console time uncertain/)).toHaveCount(0);
 expect(lockedRequests).toBe(0);
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByRole('button',{name:'Close trophies',exact:true}).click();
 await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.getByRole('button',{name:'View trophies for MOCK secret game',exact:true}).focus();
 await page.keyboard.press('Enter');
 await expect(page.getByRole('dialog')).toBeVisible();
});
