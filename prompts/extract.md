# Extraction prompt — pull Wego-relevant passages from earnings transcripts

You are reading a quarterly earnings call transcript from a publicly-traded travel company. Your job is to extract every passage that is materially relevant to **Wego.com's** competitive position.

## What Wego is

Wego is a travel metasearch engine, dual-HQ'd in Singapore and Dubai. Revenue ~$46.7M (2026), profitable, ~15M monthly users, ~$2B/month in flight + hotel referrals. Revenue mix: **MENA 65%, India outbound 20%, SEA 15%**. Business model: 2–4% commission per flight referral, 10%+ per hotel referral. Direct competitors: Skyscanner, Kayak, Trip.com, ixigo, MakeMyTrip, Almosafer, Tajawal, Traveloka.

## What to extract — relevance lenses

Pull any passage that touches one or more of these lenses:

1. **MENA / Middle East / GCC / Saudi / UAE / Egypt** — booking trends, demand commentary, Iran-war effects, Saudi Vision 2030, Ramadan/Hajj seasonality, Dubai/Riyadh hubs.
2. **India / Indian outbound / South Asia / Pakistan / Bangladesh** — booking volume, corridor pricing, ChatGPT/AI adoption in India, Indian OTA competition.
3. **SEA / Southeast Asia / Indonesia / Singapore / Malaysia / Thailand / Vietnam / Philippines** — APAC OTAs, intra-APAC travel, Trip.com competition, multi-destination patterns.
4. **AI / agentic distribution / ChatGPT / OpenAI / generative AI / LLM / Apps SDK / MCP / voice booking** — strategic posture, partnership commentary, traffic/conversion data from AI channels.
5. **Capital allocation / M&A / acquisitions / divestitures / share buybacks / capex** — what they bought, what they're considering, what they sold.
6. **Marketing spend / performance marketing / Google AI Overviews / SEO erosion / CAC / ROAS** — distribution-cost commentary, channel-mix shifts.
7. **Partnership / partner mix / direct connect / GDS / NDC / API integrations / hotel chains / airlines** — any partnership move involving Wego's competitive set or partners.
8. **Look-to-book / conversion / metasearch dynamics / OTA-vs-meta / commoditization** — the structural dynamics of meta-distribution.
9. **Forward guidance / outlook / cuts / raises / uncertainty** — especially MENA-specific or AI-specific guidance.

## What to ignore

- General macro commentary unless tied to a Wego region
- Detailed accounting line items (depreciation, tax rates, FX) unless materially MENA-relevant
- North America domestic, Europe domestic, China domestic — ignore unless company explicitly ties them to Wego's regions
- Routine corporate housekeeping (CFO transitions, audit notes, etc.) — only flag if strategically meaningful

## Output format

For each relevant passage, output a JSON object on a single line (one per line, JSONL):

```json
{"lens": "<one of the 9 lenses above>", "speaker": "<CEO/CFO/exec name + title>", "quote": "<exact verbatim quote, 1–4 sentences>", "context": "<1 line of surrounding context — what question was being answered, what was the topic>"}
```

Aim for **8–15 passages per transcript**. Quality over quantity. Direct quotes only — no paraphrasing in the `quote` field.

## After the JSONL block

Output one line:

```
EXTRACTION_DONE: <N> passages extracted from <COMPANY> <QUARTER>
```
