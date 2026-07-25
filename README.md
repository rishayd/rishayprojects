# Rishay Refi

A single-file, client-side mortgage tracker and refinance calculator. Enter your own loan details and it tells you what your equity, loan-to-value, and monthly payment actually look like — and whether refinancing at today's rate would be worth it.

**[Open the live tool](rishay-refi.html)** (or clone the repo and open `rishay-refi.html` directly in a browser — no build step, no server, no dependencies beyond a CDN-hosted charting library).

## What it does

- **Personalized loan input** — enter your purchase price, down payment %, interest rate, loan term, and start date. Every figure on the page is derived from these inputs, not hardcoded.
- **Amortization math** — remaining balance, monthly payment (P&I), and interest-vs-principal split are computed with standard amortization formulas from your inputs (or you can paste in the exact remaining balance from your loan statement to override the estimate).
- **Equity & LTV snapshot** — down payment, principal paid, and current loan-to-value ratio, visualized as a stacked equity bar.
- **Refinance calculator** — adjustable sliders for a rate threshold, new loan term, and estimated closing costs, showing monthly/annual savings, break-even period, lifetime interest saved, and a plain-language verdict (e.g. "Strong candidate" / "Wait for lower rates").
- **Rate history chart** — 6-month/1-year/3-year view of mortgage rate trends against your rate and your alert threshold.
- **Notification preferences** — UI for email/SMS/push alert toggles and a trigger condition (present as a settings surface; wiring these to a real notification backend is a future step).

## How data is stored

Everything you enter is saved to your browser's `localStorage` — nothing is sent to a server, logged, or shared. Clearing your browser data clears your saved loan.

## Tech

Plain HTML/CSS/JavaScript. [Chart.js](https://www.chartjs.org/) (via CDN) renders the rate history chart. No build tools, no framework, no backend.

## Data sources

The market-rate figures shown are illustrative starting values (based on Freddie Mac PMMS historical trends) — the "today's market rate" field is a manual input you keep current yourself, since this is a static page with no live data feed. Swap in [FRED's MORTGAGE30US series](https://fred.stlouisfed.org/series/MORTGAGE30US) for the actual current 30-year average.

## Disclaimer

For informational purposes only. Not financial advice.
