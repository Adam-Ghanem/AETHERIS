# Mission Theater — Scientific presentation workflow

Mission Theater is an evidence-bound visualization and narrative layer **on top of** the existing `/api/v1/briefing` source pipeline. It does not retrain, forecast, or change the scientific core.

## Main workflow

1. Run `Start_AETHERIS.bat` on Windows; open the local browser app.
2. From the Mission Overview click **Open Mission Theater**. If there is no completed research yet, the app routes to the Evidence Command Center and asks for a research briefing.
3. Select geographic coordinates and a valid time period; click **Generate evidence briefing**. Actual NASA POWER input is required for normal use.
4. Click **Present research**. The presentation contains seven full-screen scenes. Arrow Right/Left or PageUp/PageDown navigates; Home/End jump to first/last; Escape closes.
5. Click **Offline deck** to download a portable HTML presentation. It embeds the current numerical findings and all slide assets, can be opened offline, and provides **Print / PDF** through the browser. Export the full evidence JSON separately for reproducibility.

## Technical contract

The presentation is activated by the custom browser event `aetheris:briefing-ready`, emitted only after the Evidence Command Center has received and rendered a structurally complete response. Required fields are `observations[]`, two `findings[]`, `evidence.briefing_sha256`, `location`, `period`, and optional contrasts. Invalid data cannot open the theater.

- All dynamic text is escaped before insertion as HTML.
- Each chart uses the relevant physical unit; no rescaling one unit into another.
- Source hashes are carried into the presentation; the SHA-256 fingerprint is for reproducibility, not proof of a climate conclusion.
- Browser-opened snapshots do **not** automatically refresh NASA data. The separate source-backed research workflow remains authoritative.
- A detectable fixture product name displays **SYNTHETIC TEST FIXTURE — NOT NASA OBSERVATIONS**.
- No external scripts, images, fonts, or APIs are needed to view the exported HTML.

## Scientific integrity

Temperature trends are in °C/decade and rainfall trends in mm/decade. HAC p-values are exploratory and not a causal explanation, especially after exploration of many signals. Shared complete calendar years are required for the paired data. The early-versus-late comparison is descriptive. Joint hot/dry screening thresholds are not a validated drought classification. NASA POWER is a gridded/model-derived point product, not a city-wide station record.

## Known limitations

- This mode presents *completed* source-backed research, not a full multi-location spatial analysis deck.
- The exported file is an immutable snapshot; regenerate it after changing any source data or period.
- Very large or unusually formatted datasets may need additional layout testing; current desktop/mobile tests use 25-year fixture data.
- Full browser end-to-end verification against the live NASA service was not performed here.
