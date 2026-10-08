import {test,expect} from '@playwright/test';
import fr from '../app/messages/fr.json';
import de from '../app/messages/de.json';
import pt from '../app/messages/pt.json';
import br from '../app/messages/pt-BR.json';
import es from '../app/messages/es.json';
import it from '../app/messages/it.json';

const languages=[['fr-FR',fr],['de-DE',de],['pt-PT',pt],['pt-BR',br],['es-ES',es],['it-IT',it]] as const;
for(const [locale,labels] of languages){
 test.describe(locale,()=>{
  test.use({locale,timezoneId:'Europe/Paris'});
  test('browser locale selects interface and requests publisher text; mobile trophies stay private',async({page})=>{
   let requested='';let forbiddenRequests=0;
   const base={profile_uuid:'MOCK_LOCALE',profile_label:'MOCK locale preview',source:'ps5_native',kind:'trophy',mock:false,artwork_url:null};
   const rows=[{...base,icon_url:'/forbidden-icon',data:{title_id:'MOCK',title:'MOCK '+locale,trophy_id:'0',name:'PRIVATE SECRET',description:'PRIVATE DESCRIPTION',hidden:true,unlocked:false,grade:'gold'}},
    {...base,icon_url:null,data:{title_id:'MOCK',title:'MOCK '+locale,trophy_id:'1',name:'MOCK translated '+locale,description:'MOCK description '+locale,hidden:false,unlocked:true,grade:'silver',unlocked_at:'2026-10-06T22:07:43Z'}}];
   await page.route('**/api/account/me',route=>route.fulfill({json:{email:'mock-locale@example.test'}}));
   await page.route('**/api/account/devices',route=>route.fulfill({json:[]}));
   await page.route('**/api/account/library**',route=>{requested=new URL(route.request().url()).searchParams.get('language')||'';return route.fulfill({json:rows});});
   await page.route('**/forbidden-icon',route=>{forbiddenRequests++;return route.abort();});
   await page.goto('/');
   await expect(page.getByRole('heading',{name:labels['Your library'],exact:true})).toBeVisible();
   await expect.poll(()=>requested.split(',')[0]).toBe(locale);
   await expect(page.locator('html')).toHaveAttribute('lang',locale==='pt-BR'?locale:locale.split('-')[0]);
   
   const card=page.getByRole('button',{name:labels['View trophies for {game}'].replace('{game}','MOCK '+locale),exact:true});
   await card.focus();await page.keyboard.press('Enter');
   await expect(page.getByRole('heading',{name:labels['Hidden trophy'],exact:true})).toBeVisible();
   await expect(page.locator('.trophy-grade.gold')).toHaveText(labels.Gold);
   await expect(page.locator('.trophy-grade.silver')).toHaveText(labels.Silver);
   await expect(page.getByText(labels['✓ Earned'],{exact:true})).toBeVisible();
   await expect(page.getByText('MOCK description '+locale,{exact:true})).toBeVisible();
   if(locale==='fr-FR')await expect(page.locator('time')).toHaveText('07/10/2026 00:07:43');
   await expect(page.getByText('PRIVATE SECRET',{exact:true})).toHaveCount(0);
   await expect(page.getByText('PRIVATE DESCRIPTION',{exact:true})).toHaveCount(0);
   expect(forbiddenRequests).toBe(0);
   await page.setViewportSize({width:390,height:844});
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
   await page.getByRole('button',{name:labels['Close trophies'],exact:true}).click();
   await expect(card).toBeFocused();
   await page.route('**/api/account/profile',r=>r.fulfill({json:{handle:'mock_player',display_name:'MOCK Player'}}));
   await page.route('**/api/account/friends',r=>r.fulfill({json:{friends:[],incoming:[],outgoing:[],denied:[]}}));
   await page.evaluate(()=>document.querySelector('.sidebar')!.setAttribute('data-locale-sentinel','preserved'));
   await page.getByRole('navigation').getByRole('link',{name:labels.Friends,exact:true}).click();
   await expect(page.locator('.sidebar')).toHaveAttribute('data-locale-sentinel','preserved');
   await expect(page.locator('html')).toHaveAttribute('lang',locale==='pt-BR'?locale:locale.split('-')[0]);
   await expect(page.getByRole('heading',{name:labels.Friends,exact:true})).toBeVisible();
   await expect(page.getByLabel(labels['Public handle'],{exact:true})).toHaveValue('mock_player');
   await expect(page.getByRole('heading',{name:new RegExp(labels['Requests received'])})).toBeVisible();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
   await page.goto('/login');
   await expect(page.getByRole('button',{name:labels['Sign in'],exact:true})).toBeVisible();
   await expect(page.getByLabel(labels.Password,{exact:true})).toBeVisible();
   await page.route('**/api/auth/login',route=>route.fulfill({status:401,json:{detail:'Email or password is incorrect'}}));
   await page.getByLabel(labels.Email,{exact:true}).fill('mock-locale@example.test');
   await page.getByLabel(labels.Password,{exact:true}).fill('mock-wrong-password');
   await page.getByRole('button',{name:labels['Sign in'],exact:true}).click();
   await expect(page.locator('p[role="alert"]')).toHaveText(labels['Invalid email or password']);
  });
 });
}
test('catalogs cover all messages and preserve interpolation fields',()=>{
 const parameters=(value:string)=>(value.match(/\{\w+\}/g)||[]).sort();
 for(const [,catalog] of languages){
  expect(Object.keys(catalog).sort()).toEqual(Object.keys(fr).sort());
  for(const key of ['Friends','Public handle','Requests received','Request declined','Total playtime','Compact list','Loading friends…','Loading profile…','Loading comparison…','Secret trophies stay hidden until you earn them.']){expect((catalog as Record<string,string>)[key]).toBeTruthy();expect((catalog as Record<string,string>)[key]).not.toContain('?');}
  for(const [key,value] of Object.entries(catalog)){expect(value.trim().length).toBeGreaterThan(0);expect(parameters(value)).toEqual(parameters(key));}
 }
});
test.describe('unsupported interface language',()=>{
 test.use({locale:'nl-NL'});
 test('falls back to English without changing the publisher language request',async({page})=>{
  await page.goto('/login');
  await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible();
  await expect(page.locator('html')).toHaveAttribute('lang','en');
 });
});
