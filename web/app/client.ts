import {translateText} from './i18n';
export async function api(path: string, body?: unknown) {
  const response = await fetch('/api'+path, {method: body === undefined ? 'GET' : 'POST',
    credentials:'same-origin', headers: body === undefined ? {} : {'Content-Type':'application/json'},
    body: body === undefined ? undefined : JSON.stringify(body), cache:'no-store'}).catch(()=>{throw new Error(translateText('Unable to connect. Please try again.'));});
  const text = await response.text();
  let data; try { data = JSON.parse(text); } catch { throw new Error(translateText('Unable to connect. Please try again.')); }
  if (!response.ok) {const message=typeof data.detail === 'string' ? data.detail : 'Check the supplied fields and try again.';throw new Error(translateText(message==='Email or password is incorrect'?'Invalid email or password':message));}
  return data;
}
