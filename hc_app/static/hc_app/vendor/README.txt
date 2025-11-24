Place a production-ready Chart.js bundle here to avoid using the CDN fallback.

1. Download Chart.js (recommended: chart.umd.min.js or chart.min.js) from https://www.chartjs.org/ and place it as:

   hc_app/static/hc_app/vendor/chart.min.js

2. The dashboard template will try to load this file first; if it's not present the template will fall back to a CDN.

Why vendor? Some environments block external CDNs or have CSP restrictions. Vendoring ensures charts render even when offline or when external requests are blocked.
