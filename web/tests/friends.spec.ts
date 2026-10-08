import {test,expect} from '@playwright/test';
import {randomUUID} from 'node:crypto';
test('two players request, approve, compare and remove a friendship',async({browser})=>{
 const contexts=await Promise.all([browser.newContext(),browser.newContext()]);
 const pages=await Promise.all(contexts.map(c=>c.newPage()));
 const suffix=randomUUID().replaceAll('-','').slice(0,12);const handles=['friend_a_'+suffix,'friend_b_'+suffix];
 for(let i=0;i<2;i++){
  await pages[i].goto('/login');await pages[i].getByRole('button',{name:'Create an account',exact:true}).click();
  await pages[i].getByLabel('Email',{exact:true}).fill(handles[i]+'@example.test');await pages[i].getByLabel('Password',{exact:true}).fill('friend-test-password-123');
  await pages[i].getByRole('button',{name:'Register',exact:true}).click();await expect(pages[i].getByRole('heading',{name:'Your library',exact:true})).toBeVisible();
  await pages[i].goto('/friends');await pages[i].getByLabel('Display name',{exact:true}).fill('TEST Player '+i);await pages[i].getByLabel('Public handle',{exact:true}).fill(handles[i]);await pages[i].getByRole('button',{name:'Save profile',exact:true}).click();await expect(pages[i].getByText('Profile saved',{exact:true})).toBeVisible();
 }
 await pages[0].getByRole('searchbox').fill(handles[1]);await pages[0].getByRole('button',{name:'Search',exact:true}).click();await pages[0].getByRole('link',{name:/TEST Player 1/}).click();
 await pages[0].getByRole('button',{name:'Send friend request',exact:true}).click();await expect(pages[0].getByText('Request sent',{exact:true})).toBeVisible();
 await pages[1].reload();await pages[1].getByRole('button',{name:'Accept',exact:true}).click();await pages[1].getByRole('link',{name:'Compare trophies',exact:true}).click();await expect(pages[1].getByRole('heading',{name:'Compare trophies',exact:true})).toBeVisible();
 await expect(pages[1].getByText('No recorded trophies to compare yet.',{exact:true})).toBeVisible();
 await pages[1].setViewportSize({width:390,height:844});expect(await pages[1].evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await pages[1].getByRole('button',{name:'Remove friend',exact:true}).click();await expect(pages[1].getByRole('heading',{name:'Compare trophies',exact:true})).toHaveCount(0);
 for(const context of contexts)await context.close();
});
test('comparison supports all games and filters while secret trophy stays concealed',async({page})=>{
 const profile={handle:'test_friend',display_name:'TEST Friend',relationship:'friends',request_id:'TEST_LINK',viewer_authenticated:true};
 const trophy={trophy_id:'0',grade:'gold',hidden:true,name:'Hidden trophy',description:null,icon_url:null,mine:false,friend:true,mine_present:true,friend_present:true};
 const game={source:'ps5_native',title_id:'TEST_SET',title:'TEST game',artwork_url:null,total:1,mine_earned:0,friend_earned:1,trophies:[trophy]};
 await page.route('**/api/players/test_friend',r=>r.fulfill({json:profile}));
 await page.route('**/api/account/friends/test_friend/compare**',r=>r.fulfill({json:{friend:profile,games:[{...game,trophies:new URL(r.request().url()).searchParams.has('title_id')?[trophy]:[]}]}}));
 await page.goto('/players/test_friend');await page.getByRole('button',{name:/TEST game/}).click();await expect(page.getByRole('heading',{name:'Hidden trophy',exact:true})).toBeVisible();await page.getByLabel('Show comparison',{exact:true}).selectOption('friend');await expect(page.locator('.comparison-status .is-earned')).toHaveText('Earned');await page.getByLabel('Show comparison',{exact:true}).selectOption('mine');await expect(page.getByText('No trophies match this filter.',{exact:true})).toBeVisible();
 await page.getByLabel('Compare game',{exact:true}).selectOption('');await expect(page.getByRole('button',{name:/TEST game/})).toBeVisible();
});
