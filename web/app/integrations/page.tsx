'use client';
import {useEffect,useState} from 'react';
import {api} from '../client';
import {useLocale} from '../i18n';

export default function Integrations(){const{t}=useLocale();const[configured,setConfigured]=useState<boolean|null>(null),[error,setError]=useState('');
 useEffect(()=>{api('/account/integrations').then(data=>setConfigured(data.platprices.configured)).catch(e=>setError(e.message));},[]);
 return <><div className="page-heading"><div><p className="eyebrow">{t('YOUR COLLECTION')}</p><h1>{t('Integrations')}</h1><p>{t('More context for your games, with your console records kept intact.')}</p></div></div>{error&&<p role="alert" className="error">{error}</p>}
 <div className="integration-grid"><section className="social-panel"><span className="integration-status">{t('Automatic completion estimates')}</span><h2>HowLongToBeat</h2><p>{t('Open a game to load Main Story, Main + Extras and Completionist estimates. Choose the correct edition when needed, or save manual estimates.')}</p><p>{t('HowLongToBeat account linking and upload are not implemented yet. Use the game link to submit playtime manually.')}</p><p>{t('Your recorded hours are not proof that you finished a game. Review them before submitting a completion time.')}</p>{configured!==null&&<a className="button secondary" href="/api/account/integrations/playtime.csv">{t('Export my playtime (CSV)')}</a>}</section>
 <section className="social-panel"><span className="integration-status">{configured===null?t('Checking…'):t(configured?'Configured on server':'Server setup needed')}</span><h2>{t('Trophy earn rates')}</h2><p>{t('Powered by PlatPrices')}</p><p>{t('See the percentage of PlayStation players who earned each trophy, with the source and update date.')}</p><p>{t('A noncommercial free PlatPrices API key is configured by the host. No PSN account is needed.')}</p><a className="text-link" href="https://platprices.com/developers.php" target="_blank" rel="noopener noreferrer">{t('Free API details')} ↗</a></section></div></>;
}
