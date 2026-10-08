import {test,expect} from '@playwright/test';

test('compact rows fill the library and align progress across different title lengths',async({page})=>{
 // Synthetic layout fixtures; no console extraction or authentication claim.
 const rows=['Short title','A much longer game title with several words that should wrap naturally'].map((title,i)=>({
  profile_uuid:'LAYOUT_FIXTURE',profile_label:'Layout fixture',source:'ps5_native',kind:'trophy',mock:false,artwork_url:null,icon_url:null,
  data:{title_id:'LAYOUT_'+i,title,trophy_id:'0',name:'Fixture trophy',grade:'bronze',unlocked:true}
 }));
 await page.route('**/api/account/me',r=>r.fulfill({json:{email:'layout@example.test'}}));
 await page.route('**/api/account/devices',r=>r.fulfill({json:[]}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:rows}));
 await page.goto('/');await expect(page.locator('.game-card')).toHaveCount(2);
 for(const width of [1920,1440,1150,1024,900,800,761,760,600,390,320]){
  await page.setViewportSize({width,height:1000});
  const geometry=await page.locator('.game-grid').evaluate(grid=>{
   const bounds=grid.getBoundingClientRect();
   const cards=Array.from(grid.querySelectorAll('.game-card')).map(card=>{
    const rect=card.getBoundingClientRect(),progress=card.querySelector('.progress-track')!.getBoundingClientRect();
    const art=card.querySelector('.game-art')!.getBoundingClientRect(),title=card.querySelector('h2')!.getBoundingClientRect();
    return {left:rect.left,right:rect.right,progressLeft:progress.left,progressRight:progress.right,artRight:art.right,titleLeft:title.left};
   });
   return {left:bounds.left,right:bounds.right,cards,overflow:document.documentElement.scrollWidth>innerWidth};
  });
  expect(geometry.overflow,'horizontal overflow at '+width).toBe(false);
  for(const card of geometry.cards){
   expect(Math.abs(card.left-geometry.left),'row left at '+width).toBeLessThan(1);
   expect(Math.abs(card.right-geometry.right),'row width at '+width).toBeLessThan(1);
   expect(card.artRight,'artwork remains left at '+width).toBeLessThanOrEqual(card.titleLeft);
  }
  expect(Math.abs(geometry.cards[0].progressLeft-geometry.cards[1].progressLeft),'progress alignment at '+width).toBeLessThan(1);
  expect(Math.abs(geometry.cards[0].progressRight-geometry.cards[1].progressRight),'progress alignment at '+width).toBeLessThan(1);
 }
 await page.getByRole('button',{name:'Cards',exact:true}).click();
 await expect(page.locator('.game-grid')).not.toHaveClass(/compact-list/);
 await page.getByRole('button',{name:'View trophies for Short title',exact:true}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
});
