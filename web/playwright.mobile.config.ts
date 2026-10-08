import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',testMatch:'auth-errors.spec.ts',workers:1,reporter:'list',
  outputDir:'/tmp/ps5-sync-mobile-results',use:{baseURL:'http://host.docker.internal:3000',headless:true},
  projects:[{name:'mobile-webkit',use:{browserName:'webkit'}},{name:'mobile-chromium',use:{browserName:'chromium'}}]});
