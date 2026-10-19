'use client';
import {useLocale} from './i18n';

export type CollectionGame={id:string;title:string;total:number;earned:number;seconds:number|null;sessions:number};

export function CollectionGroups({games,sharedSeconds,sharedSessions,onOpen,expanded=false}:{
 games:CollectionGame[];sharedSeconds:number|null;sharedSessions:number;onOpen:(id:string)=>void;expanded?:boolean;
}){
 const {t}=useLocale();
 if(!games.length)return null;
 return <details className="collection-groups" open={expanded||undefined}>
  <summary>{t('Games in this collection')} <span>{games.length}</span></summary>
  <div className="collection-shared-time"><span>{t('Shared collection playtime')}</span>
   <strong>{sharedSeconds===null?t('Unknown'):t('{hours}h {minutes}m recorded across {count} sessions',{
    hours:Math.floor(sharedSeconds/3600),minutes:Math.floor(sharedSeconds%3600/60),count:sharedSessions})}</strong>
   <p>{t('Collection-level time is not split between games.')}</p>
  </div>
  <ul>{games.map(game=><li key={game.id}><button className="collection-game-open" onClick={()=>onOpen(game.id)}
   aria-label={t('View {game} in this collection',{game:game.title})}>
   <strong>{game.title}</strong><span className="collection-game-progress">{t('{earned}/{total} recorded trophies unlocked',{earned:game.earned,total:game.total})}</span>
   <span className="collection-game-playtime">{game.seconds===null?t('Playtime not available separately'):t('{hours}h {minutes}m recorded across {count} sessions',{
    hours:Math.floor(game.seconds/3600),minutes:Math.floor(game.seconds%3600/60),count:game.sessions})}</span>
   <span className="collection-game-link">{t('Explore trophies')} <span aria-hidden="true">↗</span></span>
  </button></li>)}</ul>
 </details>;
}
