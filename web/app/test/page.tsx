import {notFound} from 'next/navigation';
import LocalTest from './test-client';

export const dynamic = 'force-dynamic';

export default function TestPage() {
  if(process.env.ENABLE_LOCAL_TESTS!=='true')notFound();
  return <LocalTest enabled/>;
}
