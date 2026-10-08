import {test,expect} from '@playwright/test';
import fr from '../app/messages/fr.json';

test.use({locale:'fr-FR',viewport:{width:393,height:852},isMobile:true,hasTouch:true});
const cases=[
 {name:'structured origin rejection',status:403,contentType:'application/json',
  body:JSON.stringify({detail:'Same-origin request required',code:'origin_mismatch',website_url:'https://trophy-sync.party'}),
  expected:fr['The website origin check rejected this request. Open {url} and try again.'].replace('{url}','https://trophy-sync.party')},
 {name:'legacy plain text origin rejection',status:403,contentType:'text/plain',body:'Same-origin request required',
  expected:fr['Open the public website URL to sign in or register.']},
 {name:'proxy error is distinct from connectivity failure',status:502,contentType:'text/html',body:'<html>Bad gateway</html>',
  expected:fr['The server returned an unexpected response (HTTP {status}). Please try again.'].replace('{status}','502')},
 {name:'Cloudflare challenge',status:403,contentType:'text/html',body:'<html>Security check</html>',headers:{'cf-mitigated':'challenge'},
  expected:fr['Cloudflare requires a browser security check. Reload the website and try again.']},
];
for(const item of cases){
 test('mobile registration explains '+item.name,async({page})=>{
  // All API calls intercepted: no accounts or hosted requests are created.
  await page.route('**/api/**',r=>r.fulfill({status:401,json:{detail:'Sign in again'}}));
  await page.route('**/api/auth/register',r=>r.fulfill({status:item.status,contentType:item.contentType,body:item.body,headers:item.headers}));
  await page.goto('/login');
  await page.getByRole('button',{name:fr['Create an account'],exact:true}).click();
  await page.locator('input[name=email]').fill('MOCK-mobile@example.test');
  await page.locator('input[name=password]').fill('MOCK-test-password-123');
  await page.getByRole('button',{name:fr.Register,exact:true}).click();
  await expect(page.locator('p[role=alert]')).toHaveText(item.expected);
 });
}
