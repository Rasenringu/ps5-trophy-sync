import {test,expect} from '@playwright/test';
import {randomUUID} from 'node:crypto';

test('test route is disabled normally; explicit development mode supports guided imports',async({page})=>{
  await page.goto('/test');
  if(await page.getByRole('heading',{name:'404',exact:true}).count()){await expect(page.getByRole('link',{name:'Local sample test',exact:true})).toHaveCount(0);return;}
  await expect(page.getByRole('heading',{name:'Test locally',exact:true})).toBeVisible();
  await expect(page.getByText('MOCK TEST — NO PS5 CONNECTION',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Create test pairing code',exact:true})).toBeDisabled();
  await expect(page.getByRole('button',{name:'Import sample data',exact:true})).toBeDisabled();
  await page.getByRole('link',{name:'Sign in or register to start the test',exact:true}).click();
  await page.getByRole('button',{name:'Create an account',exact:true}).click();
  await page.getByLabel('Email',{exact:true}).fill('local-guide-test-'+randomUUID()+'@example.test');
  await page.getByLabel('Password',{exact:true}).fill('local-guide-test-password-123');
  await page.getByRole('button',{name:'Register',exact:true}).click();
  await expect(page).toHaveURL(/\/test$/);
  await page.getByRole('button',{name:'Create test pairing code',exact:true}).click();
  await expect(page.getByRole('button',{name:'Approve simulated profile',exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Import sample data',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Approve simulated profile',exact:true}).click();
  await page.getByRole('button',{name:'Import sample data',exact:true}).click();
  await expect(page.getByText('Sample imported.',{exact:false})).toBeVisible();
  await page.getByRole('button',{name:'Test repeat import',exact:true}).click();
  await expect(page.getByText('Repeat import recognized. No duplicate trophies or sessions were added.',{exact:true})).toBeVisible();
  const rows=await page.evaluate(async()=>await (await fetch('/api/account/library')).json());
  expect(rows).toHaveLength(4);
  expect(rows.every((row:{mock:boolean})=>row.mock)).toBe(true);
  await page.getByRole('link',{name:'Open your library',exact:true}).click();
  await expect(page.getByRole('heading',{name:'MOCK local test game',exact:true})).toHaveCount(0);
  await page.getByRole('checkbox',{name:'Include clearly labeled mock test imports',exact:true}).check();
  await expect(page.getByRole('heading',{name:'MOCK local test game',exact:true})).toBeVisible();
  await expect(page.getByText('1/2 recorded trophies unlocked',{exact:false})).toBeVisible();
  await expect(page.getByText('0h 30m recorded across 1 sessions',{exact:false})).toBeVisible();
  await page.goto('/connections');
  await page.getByRole('button',{name:'Disconnect console',exact:true}).click();
  await expect(page.getByRole('button',{name:'Disconnect console',exact:true})).toHaveCount(0);
});
