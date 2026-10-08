import {translateText} from './i18n';
export async function api(path: string, body?: unknown) {
  const response = await fetch('/api'+path, {method: body === undefined ? 'GET' : 'POST',
    credentials:'same-origin', headers: body === undefined ? {} : {'Content-Type':'application/json'},
    body: body === undefined ? undefined : JSON.stringify(body), cache:'no-store'}).catch(()=>{throw new Error(translateText('Unable to connect. Please try again.'));});
  const text = await response.text();
  let data; try { data = JSON.parse(text); } catch {
    if(response.status===403 && text.trim()==='Same-origin request required')
      throw new Error(translateText('Open the public website URL to sign in or register.'));
    if(response.headers.get('cf-mitigated')==='challenge')
      throw new Error(translateText('Cloudflare requires a browser security check. Reload the website and try again.'));
    throw new Error(translateText('The server returned an unexpected response (HTTP {status}). Please try again.',{status:response.status}));
  }
  if (!response.ok && data?.code==='origin_mismatch' && typeof data.website_url==='string')
    throw new Error(translateText('The website origin check rejected this request. Open {url} and try again.',{url:data.website_url}));
  if (!response.ok) {const message=typeof data.detail === 'string' ? data.detail : 'Check the supplied fields and try again.';throw new Error(translateText(message==='Email or password is incorrect'?'Invalid email or password':message));}
  return data;
}
