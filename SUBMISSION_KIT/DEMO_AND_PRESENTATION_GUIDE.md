# AETHERIS — live demo and pitch guide

## Recommended 3–4 minute demo narrative

**Opening (20 seconds).** “Earth-system change is often reduced to a chart. AETHERIS asks a harder question: what changed, where, how much, and how reliable is our evidence?”

**1. Show the data source (35 seconds).** Open Earth Explorer, choose Beni Mellal or another supported point, define a historical period, and run an investigation. Open the evidence ledger; explain NASA POWER, `T2M`, units, monthly-to-annual aggregation and limitations. Let real results speak; do not quote any fixed numbers before verifying them on screen.

**2. Demonstrate scientific inference (45 seconds).** Show annual series, OLS trend, confidence interval, Theil–Sen comparison and the Scientific Quality Passport. Point to missing-month checks and the leave-one-year-out sensitivity chart.

**3. Demonstrate discovery across regions (55 seconds).** Open Research Campaign Studio, choose Beni Mellal, Marrakech, Casablanca and Ouarzazate, and launch. This calls NASA POWER for two independent variables per selected point. Compare trends **within** each variable (never compare °C directly with mm). Drag the historical year explorer and show the annual values and internal-baseline departures.

**4. Make findings reproducible (40 seconds).** Download campaign CSV and evidence JSON. Download the offline campaign HTML presentation. Optionally show the separate Reproducibility Capsule in Evidence Command Center and run its verifier.

**Closing (20 seconds).** “We do not hide gaps, fabricate climate maps, or claim to prove causes. We turn NASA climate data into inspectable evidence that more people can understand and challenge.”

## Demo setup checklist

- [ ] Extract `AETHERIS` to a normal local Windows folder (not inside ZIP).
- [ ] Start `Start_AETHERIS.bat`; ensure Python dependencies are installed.
- [ ] Open `http://127.0.0.1:8765`.
- [ ] Run `Verify_Live_NASA.bat` from a network that allows NASA POWER API access.
- [ ] Check live period/variable availability and show an actual result.
- [ ] Pre-open the Research Campaign Studio and use a modest period if NASA source latency is high.
- [ ] Test the JSON, CSV, offline HTML and Scientific PDF exports.
- [ ] Verify the presentation on the intended screen and browser.
- [ ] Use a real project-repository URL and demo URL in the official submission.
- [ ] Identify actual team members and credit their respective contributions.

## If NASA API is unavailable during the demo

Explain clearly that the upstream data provider cannot be reached. The app reports errors instead of substituting fake science. You may show previously **authentic exported research** only if it retains its original metadata. Do not pass synthetic test screenshots off as NASA observations.

## Scientific questions the jury may ask

**Is a warming or drying trend automatically significant?** No. Trend magnitude and statistical evidence are distinct; p-values depend on assumptions and do not establish causation.

**Are the selected point results city-wide averages?** No. NASA POWER supplies gridded/model-derived point values.

**Why use a robust slope?** Theil–Sen gives a complementary view of sensitivity to extreme observations. Agreement is a diagnostic, not a guarantee of scientific validity.

**Is the AI model deployed?** The optional AI bridge is not a pretrained model; only claim AI capabilities that are actually connected and verified.

**What is the scientific innovation?** The reproducible workflow makes provenance, multiple-signal comparison, multi-point exploratory inference and uncertainty inspectable by non-specialists.
