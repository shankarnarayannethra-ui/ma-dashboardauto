# DealScope Auto-Updating M&A Dashboard

A multi-page static M&A dashboard that refreshes recent merger and acquisition headlines automatically with GitHub Actions.

## Run locally

Open this folder in VS Code and launch `index.html` with Live Server. The checked-in `generated-deals.js` file lets the site work without a backend.

To refresh news locally:

```bash
python scripts/update_news.py
```

## Enable automatic updates on GitHub

1. Push the complete folder to a GitHub repository.
2. Open **Settings → Actions → General** and ensure workflows have **Read and write permissions**.
3. Open the **Actions** tab and run **Update M&A news** once using **Run workflow**.
4. The workflow will then run about every six hours and commit an updated `generated-deals.js`.
5. For GitHub Pages, choose your repository branch and the root folder as the publishing source.

## Important limitations

- Automated records are headline matches from Google News RSS, not fully verified deal research.
- Headlines can include rumors, commentary, or duplicate coverage.
- The dashboard clearly marks these items as **AUTO** and **News detected**.
- Open the original source before relying on deal value, parties, status, or strategic analysis.
- Publisher pages remain subject to their own subscriptions, licenses, and terms.

Curated records in `data.js` retain richer analysis and scorecards.
