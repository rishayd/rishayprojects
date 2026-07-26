# Rishay's Projects

Small, single-file personal finance tools. Each one is plain HTML/CSS/JavaScript — no build step, no server, no backend. Everything you type in stays in your browser's `localStorage`; nothing is ever sent anywhere.

**Live:** [Rishay Refi](https://rishayd.github.io/rishayprojects/rishay-refi.html) · [Rishay Auto](https://rishayd.github.io/rishayprojects/rishay-auto.html)

---

## [Rishay Refi](rishay-refi.html)

A client-side mortgage tracker and refinance calculator. Enter your own loan details and it tells you what your equity, loan-to-value, and monthly payment actually look like — and whether refinancing at today's rate would be worth it.

**[Open the live tool](https://rishayd.github.io/rishayprojects/rishay-refi.html)**

- **Personalized loan input** — purchase price, down payment %, interest rate, loan term, and start date. Every figure on the page is derived from these inputs, not hardcoded.
- **Amortization math** — remaining balance, monthly payment (P&I), and interest-vs-principal split, computed from your inputs (or paste in your exact remaining balance from a loan statement to override the estimate).
- **Equity & LTV snapshot** — down payment, principal paid, and current loan-to-value ratio, visualized as a stacked equity bar.
- **Refinance calculator** — adjustable sliders for a rate threshold, new loan term, and estimated closing costs, showing monthly/annual savings, break-even period, lifetime interest saved, and a plain-language verdict.
- **Rate history chart** — 6-month/1-year/3-year view of mortgage rate trends against your rate and your alert threshold.

The market-rate figures are illustrative starting values (based on Freddie Mac PMMS historical trends) — "today's market rate" is a manual input you keep current yourself. Swap in [FRED's MORTGAGE30US series](https://fred.stlouisfed.org/series/MORTGAGE30US) for the actual current 30-year average.

**Why the notification toggles don't do anything:** the email/SMS/push cards under "Notification settings" are UI only — clicking them doesn't send you anything. Making that real would need a backend: server-side storage for your threshold and contact info (since it has to check even when the page is closed), a scheduled job polling a live rate feed, and third-party services to actually deliver email/SMS/push. That's a deliberate line this project doesn't cross — Rishay Refi is meant to stay a single static file with no server, no database, and nothing about you stored anywhere but your own browser. It's built to be used as a standalone, on-demand check: open it whenever you want to know if refinancing makes sense right now, rather than something that watches rates for you in the background. The notification settings are left in as a sketch of what a "real" version could look like.

---

## [Rishay Auto](rishay-auto.html)

A holistic, unbiased car affordability calculator. Enter the car you're considering and your finances, and it estimates every real cost of ownership — not just the loan payment — to tell you whether you can actually afford it.

**[Open the live tool](https://rishayd.github.io/rishayprojects/rishay-auto.html)**

- **Real vehicle lookup** — cascading Year → Make → Model → Trim selectors pull actual government-rated data live from the [EPA's fueleconomy.gov API](https://www.fueleconomy.gov/feg/ws/index.shtml): fuel type, combined MPG (or kWh/100mi for EVs), and vehicle class, which in turn auto-picks the right category for insurance/maintenance/depreciation defaults. It's a free, public API that explicitly allows browser-side requests (`Access-Control-Allow-Origin: *`), so this stays a static page with no backend or proxy of its own — the only outside request it makes. If your exact car isn't in the lookup, every field it would have filled in is still there to enter by hand.
- **Personalized financing inputs** — vehicle price, down payment, trade-in, sales tax, fees, APR, and loan term, plus your monthly income and other expenses.
- **Auto-estimated running costs** — monthly insurance, maintenance, and depreciation rate get sensible defaults based on the vehicle's category, condition, and fuel type, and every default is editable once you have real numbers (an actual insurance quote, etc.). Fuel/energy cost itself is computed from real EPA efficiency once you use the lookup.
- **Fuel vs. electric aware** — computes gas cost from MPG and gas price, or electricity cost from efficiency (kWh/100mi) and electricity price, depending on what you select.
- **Loan balance vs. car value chart** — projects your remaining loan balance against the car's estimated depreciated value over the loan term, and flags when (or if) you'd have positive equity — a real risk with small down payments and long loan terms that most calculators ignore.
- **20/4/10 rule check** — down payment ≥ 20%, term ≤ 4 years, total transportation cost ≤ 10% of income — plus a total-obligations-vs-income gauge and a plain-language verdict (e.g. "Comfortably affordable" / "Outside a healthy budget").

Fuel economy comes from the EPA once you use the lookup; insurance, maintenance, and depreciation are still rough national-average estimates by vehicle category, not real quotes — the tool is upfront about this and every assumption is an editable field. There's no listing-URL field, since a static page can't scrape a car listing site — the lookup above is the honest alternative: real government data instead of a link that doesn't actually do anything.

---

## Tech

Plain HTML/CSS/JavaScript in every project. [Chart.js](https://www.chartjs.org/) (via CDN) renders the charts. No build tools, no framework, no backend, no analytics.

## Disclaimer

For informational purposes only. Not financial advice.
