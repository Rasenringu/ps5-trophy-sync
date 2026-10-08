import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',workers:1,reporter:'list',
  outputDir:'/tmp/ps5-sync-browser-results',use:{baseURL:'http://localhost:3000',headless:true,
    launchOptions:{args:['--host-resolver-rules=MAP localhost host.docker.internal']}}});
