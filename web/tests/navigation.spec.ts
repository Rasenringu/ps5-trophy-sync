import {test,expect} from '@playwright/test';

test('navigation selects one destination and follows the current profile handle',async({page})=>{
 let handle='fixture_owner';
 await page.route('**/api/account/profile',r=>r.fulfill({json:{handle,display_name:'Fixture owner',visibility:'friends'}}));
 await page.route('**/api/account/me',r=>r.fulfill({json:{email:'nav@example.test'}}));
 await page.route('**/api/account/devices',r=>r.fulfill({json:[]}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:[]}));
 await page.route('**/api/account/friends',r=>r.fulfill({json:{friends:[],incoming:[],outgoing:[],denied:[]}}));
 await page.route('**/api/players/*',r=>r.fulfill({json:{handle:new URL(r.request().url()).pathname.split('/').pop(),display_name:'Fixture player',relationship:new URL(r.request().url()).pathname.endsWith(handle)?'self':'none',request_id:null,viewer_authenticated:true,library_visible:false}}));
 for(const [route,label] of [['/','My library'],['/players/fixture_owner','My profile'],['/friends','Friends'],['/players/other_player','Friends'],['/connections','Console profiles'],['/pair','Pair console']]){
  await page.goto(route);
  const nav=page.getByRole('navigation',{name:'Main navigation'});
  await expect(nav.locator('[aria-current="page"]')).toHaveCount(1);
  await expect(nav.getByRole('link',{name:label,exact:true})).toHaveAttribute('aria-current','page');
  await expect(nav.locator('a.active')).toHaveCount(1);
 }
 handle='renamed_player';await page.evaluate(()=>window.dispatchEvent(new Event('profileupdated')));
 await expect(page.getByRole('navigation').getByRole('link',{name:'My profile',exact:true})).toHaveAttribute('href','/players/renamed_player');
 await page.getByRole('navigation').getByRole('link',{name:'Console profiles',exact:true}).click();
 await expect(page).toHaveURL(/\/connections$/);
 await expect(page.getByRole('heading',{name:'Console profiles',exact:true}).first()).toBeVisible();
 // Route changes must preserve the document and shell, avoiding full reloads
 // that flash the initial language and remove the signed-in profile link.
 await page.evaluate(()=>{document.documentElement.dataset.navigationSentinel='preserved';document.querySelector('.sidebar')!.setAttribute('data-navigation-sentinel','preserved');});
 const documentRequests:string[]=[];
 page.on('request',request=>{if(request.isNavigationRequest()&&request.resourceType()==='document')documentRequests.push(request.url());});
 for(const [route,label] of [['/friends','Friends'],['/pair','Pair console'],['/players/renamed_player','My profile'],['/','My library']]){
  await page.getByRole('navigation').getByRole('link',{name:label,exact:true}).click();
  await expect(page).toHaveURL(new RegExp(route==='/'?'/$':route+'$'));
  await expect(page.locator('html')).toHaveAttribute('data-navigation-sentinel','preserved');
  await expect(page.locator('.sidebar')).toHaveAttribute('data-navigation-sentinel','preserved');
  await expect(page.getByRole('navigation').locator('[aria-current="page"]')).toHaveCount(1);
 }
 expect(documentRequests).toEqual([]);
});
