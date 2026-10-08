import type { NextConfig } from 'next';
const config: NextConfig = {
  poweredByHeader: false,
  // Native UCP uploads are bounded to 64 MiB by the API. The default 10 MiB
  // rewrite buffer truncates larger bodies while forwarding their full length.
  experimental: {proxyClientMaxBodySize: 64 * 1024 * 1024, proxyTimeout: 70000},
  async headers() {
    const headers=[
      {key:'X-Content-Type-Options',value:'nosniff'},
      {key:'X-Frame-Options',value:'DENY'},
      {key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},
      {key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'},
    ];
    if(process.env.PUBLIC_ORIGIN?.startsWith('https://'))headers.push({key:'Strict-Transport-Security',value:'max-age=31536000'});
    return [{source:'/:path*',headers}];
  },
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${process.env.API_INTERNAL_URL || 'http://api:8000'}/:path*` }];
  },
};
export default config;
