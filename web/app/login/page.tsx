'use client';
import {useLocale} from '../i18n';
import {useState} from 'react';
import {api} from '../client';
export default function Login() {const {t,locale,preferences,browserLocale,ready:localeReady}=useLocale();
  const [register,setRegister] = useState(false), [error,setError] = useState(''), [busy,setBusy] = useState(false);
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); setBusy(true); setError('');
    const f = new FormData(e.currentTarget);
    try { await api(register ? '/auth/register' : '/auth/login', {email:f.get('email'),password:f.get('password')});
      const next = new URLSearchParams(location.search).get('next');
      location.href = next && /^\/(pair|test)(\?|$)/.test(next) ? next : '/';
    } catch(e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  return <section className="auth-wrap"><p className="eyebrow">{t("YOUR PRIVATE COLLECTION")}</p><h1>{register ? t("Create your account") : t("Welcome back")}</h1><p className="lead">{t("Keep your console profiles, trophies and play sessions in your own private library. No PSN credentials needed.")}</p>
    {error && <p role="alert" className="error">{error}</p>}<form onSubmit={submit}>
      <label>{t("Email")}<input type="email" name="email" autoComplete="email" maxLength={254} required/></label>
      <label>{t("Password")}<input type="password" name="password" minLength={12} maxLength={128} autoComplete={register?'new-password':'current-password'} required/></label>
      <p className="muted">{t("Use at least 12 characters.")}</p><button disabled={busy}>{busy?t("Please wait…"):register?t("Register"):t("Sign in")}</button>
    </form><button className="quiet auth-switch" onClick={()=>setRegister(!register)}>{register?t("Already have an account? Sign in"):t("Create an account")}</button></section>;
}
