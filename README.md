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

---

## [Rishay Auto](rishay-auto.html)

A holistic, unbiased car affordability calculator. Enter the car you're considering and your finances, and it estimates every real cost of ownership — not just the loan payment — to tell you whether you can actually afford it.

**[Open the live tool](https://rishayd.github.io/rishayprojects/rishay-auto.html)**

- **Personalized inputs** — vehicle price, down payment, trade-in, sales tax, fees, APR, and loan term, plus your monthly income and other expenses. You can also paste a link to the listing you're looking at, kept purely as a clickable reference (this is a static page with no backend, so it can't scrape the listing site — you enter the car's specs yourself).
- **Auto-estimated running costs** — monthly insurance, maintenance, fuel/energy cost, and depreciation rate all get sensible defaults based on the vehicle type, condition, and fuel type you pick, and every default is editable once you have real numbers (an actual insurance quote, etc.).
- **Fuel vs. electric aware** — computes gas cost from MPG and gas price, or electricity cost from efficiency (kWh/100mi) and electricity price, depending on what you select.
- **Loan balance vs. car value chart** — projects your remaining loan balance against the car's estimated depreciated value over the loan term, and flags when (or if) you'd have positive equity — a real risk with small down payments and long loan terms that most calculators ignore.
- **20/4/10 rule check** — down payment ≥ 20%, term ≤ 4 years, total transportation cost ≤ 10% of income — plus a total-obligations-vs-income gauge and a plain-language verdict (e.g. "Comfortably affordable" / "Outside a healthy budget").

Insurance, maintenance, fuel economy, and depreciation are rough national-average estimates by vehicle type, not real quotes — the tool is upfront about this and every assumption is an editable field.

---

## Tech

Plain HTML/CSS/JavaScript in every project. [Chart.js](https://www.chartjs.org/) (via CDN) renders the charts. No build tools, no framework, no backend, no analytics.

## Disclaimer

For informational purposes only. Not financial advice.
