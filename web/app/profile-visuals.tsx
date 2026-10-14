import {TrophyMark} from './components';
export function ProfileAvatar({avatar,name}:{avatar:string;name:string}){
 return <span className={'person-avatar profile-avatar avatar-'+avatar} aria-hidden="true">{avatar==='initial'?name.slice(0,1):avatar==='orbit'?<svg viewBox="0 0 48 48" fill="none"><circle cx="24" cy="24" r="7" fill="currentColor"/><ellipse cx="24" cy="24" rx="21" ry="10" transform="rotate(-35 24 24)" stroke="currentColor" strokeWidth="2"/><circle cx="38" cy="10" r="3" fill="currentColor"/></svg>:avatar==='diamond'?<svg viewBox="0 0 48 48" fill="none"><path d="m24 5 18 19-18 19L6 24 24 5Z" stroke="currentColor" strokeWidth="2"/><path d="m24 13 10 11-10 11-10-11 10-11Z" fill="currentColor"/></svg>:<TrophyMark/>}</span>;
}
