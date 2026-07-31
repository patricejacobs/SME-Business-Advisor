# Guyana operating context — payments, logistics, utilities, labour, sectors

last_verified: 2026-07-18

**Confidence tags:** **[V]** verified · **[M]** single credible secondary source · **[U]** uncertain,
conflicting or stale · **[I]** inference from verified facts, not a sourced claim ·
**[R]** regional Caribbean proxy standing in for missing Guyana data.

**A warning about sources.** Guyana is small enough that a large share of English-language search
results are AI-generated SEO filler. Two examples caught in research: one source claimed PayPal
supports Guyanese merchants (false — send-only); another listed "First Citizens Bank" and "NCB
Guyana" as local providers (neither operates in Guyana). **Anything tagged [U] should be verified
before a client commits money.**

---

## 0. The one thing to understand first

| Indicator | Value | Confidence |
|---|---|---|
| Real GDP growth 2025 | 19.3% | [V] |
| **Non-oil GDP growth 2025** | **14.3%** | [V] |
| Inflation (Apr 2026) | 3.4% | [V] |
| GDP per capita (PPP, 2024) | US$83,483 | [V] |
| **Median monthly income** | **~G$50,000 (~US$240)** | [U] |
| Exchange rate | Official G$208.50; **cambio G$222–225** | [V] |

**[I] The central commercial fact about Guyana is the gap between those two income rows.** GDP per
capita of US$83,483 is oil GDP divided by the population and bears no relationship to household
purchasing power. A small business sells into a market where the median worker earns about US$240 a
month, while operating in a cost environment inflated by a sector paying international rates. **Every
pricing, wage and rent decision sits in that gap.**

**⚠ Population figures conflict, and this matters for market sizing.** DataReportal reports **837,000**
(Oct 2025) [V]; Guyana's Chief Statistician announced the population **surpassed 1,025,334 in July
2026** [V]. **[I]** The most likely explanation is immigration that international estimates lag on,
plus a census rebase. **Use ~800k for conservative market sizing and note the upside.**

---

## 1. Payments and banking

### Cash still dominates

**[V]** The US Commercial Service states plainly that Guyana remains a cash-based society; cards are
used only at higher-end supermarkets, restaurants and hotels. Many gas stations still decline cards.
A World Bank payments project recorded ~99.9% of payments made through paper instruments — cash,
cheques and vouchers — though **that is a pre-2020 baseline, not 2026.**

### FAST PAY — live since 2 June 2026

**[V]** Guyana's real-time payments system allows customers across participating banks to send and
receive instantly, 24/7, via mobile or internet banking. Integrated with **India's UPI**, making
Guyana the first Caribbean country with a live UPI-linked real-time payments system.

**[I] It is weeks old. Merchant adoption, fees and reliability are unproven. Treat it as a strong
medium-term tailwind for B2B settlement and a reason to design systems that can accept bank-push
payments — but do not build a 2026 cash-flow model assuming customers will use it.**

### Mobile money

**MMG (Mobile Money Guyana)** is dominant. **[V]** Owned by GTT/One Communications;
**network-agnostic** and **requires no bank account** — only a phone and a registered account.
Supports bill payments, P2P, top-ups, **merchant purchases**, e-gift cards. **MMG Merchant Services**
lets a business accept payments into a merchant wallet settled to a bank or MMG account. Registration
requires ID, email and proof of address; no registration fee.

**⚠ [U] MMG merchant fee rates are not published anywhere.** Request the merchant schedule directly.

**[U] Scale:** ~70,000 customers and 750+ merchants/agents as of 2021; current figures unobtainable.
**Alternative: Digicel MyCash** [V] — wallet supporting transfers, bill payment, top-ups and inbound
remittances, with an agent network.

### Card acceptance — smaller than most people assume

**[V]** Republic Bank: **300+ merchant locations countrywide.** GBTI: **235 POS terminals nationwide.**

**[I] Those numbers are the story. Roughly 300 and 235 terminals in an entire country. Card
acceptance is a Georgetown, upper-tier phenomenon — not a national payment method. A small retailer
outside the capital who invests in POS is buying capability their customers largely cannot use.**

**⚠ [U] No Guyanese bank publishes merchant discount rates.** The only figures found (2.5–4.0% per
transaction, payout fees G$500–1,500, FX markup 1.5–3.5%) come from a source that also listed
non-existent Guyanese banks. **Do not rely on them. Get written quotes from Republic and GBTI.**

### Online payment gateways — the critical constraints

| Provider | Status for Guyanese merchants | Confidence |
|---|---|---|
| **Stripe** | ❌ **NOT available as a merchant country** | [V] |
| Stripe Global Payouts | ✅ Guyana added 15 Dec 2025 — can **receive** cross-border payouts. **Not a merchant account** | [V] |
| **PayPal** | ⚠️ **SEND-ONLY.** Can pay for purchases; **cannot receive payments or withdraw** | [V] |
| Shopify (platform) | ✅ Usable | [V] |
| Shopify Payments | ❌ Not available in Guyana | [V] |
| **WiPay** | ✅ Launched in Guyana; card, bank account and **cash vouchers**, online and in-person | [V] |
| First Atlantic Commerce | ✅ Regional gateway serving Caribbean merchants and banks | [V] |
| MMG | ✅ Merchant wallet, integrable | [V] |

**[I] Bottom line for a Guyanese merchant selling online: you can build on Shopify or WooCommerce,
but checkout must run through WiPay, First Atlantic Commerce, a local bank gateway, or MMG. If you
sell internationally you cannot collect via Stripe or PayPal normally — the realistic options are a
foreign entity (with its own tax and FX consequences), a merchant-of-record service, or Stripe
Global Payouts as a recipient. Anyone who says "just use Stripe" has not checked.**

### Foreign exchange — the binding constraint on importers

**[V]** Guyana introduced a **nine-point foreign exchange control plan in September 2025** after USD
outflows nearly quadrupled in a year to ~US$1.2 billion. The measures:

1. Any FX request for importing goods requires a **copy of the commercial invoice**
2. On arrival, invoice and **bill of lading must go to both GRA and the bank**
3. Banks **cannot release FX** without certified invoice, bill of lading and GRA compliance
4. Banks submit documentation to the Bank of Guyana for **central reconciliation**
5. Banks must ensure **personal credit cards are not used to settle business obligations**
6. **Penalties** for related-party transactions and inflated invoicing used for capital flight
7. Anyone taking foreign currency out of Guyana must **declare its source**
8. Local-content oil and gas companies must **hold local accounts** for foreign currency earnings
9. A **single-window post-clearing system** — prior transactions must reconcile before new requests

**[V] Reported effect:** US companies report difficulty and delays accessing USD to pay suppliers,
repatriate profits, pay royalties and service foreign debt.

**⚠ Note the tension in the official record.** The State Department describes Guyana as operating a
de jure float with funds freely convertible — while the same source set documents active rationing.
**[I] The de jure position and the de facto experience have diverged. Plan for the de facto.**

**[I] Operating implications for a small importer:**
- **Your paperwork chain is now a cash-flow dependency, not just a compliance task.** Sloppy supplier
  invoicing will delay FX access
- **Do not plan to settle supplier obligations on a personal credit card** — explicitly targeted
- Build **longer lead times** into working capital assumptions for FX access, on top of shipping
- **[V]** GRA publishes its own customs exchange rate that does not match commercial bank rates —
  this affects landed-cost calculations

### Correspondent banking — improving

**[V] The historic damage:** some Guyanese banks saw correspondent transactions decline by **as much
as 27% between 2014 and 2016** due to de-risking; several had relationships terminated.

**[V] Now materially improving.** The Bank of Guyana has licensed **Citibank, Crown Agents Bank and
One American**. These will **not take retail deposits** — they are representative/wholesale
operations expanding access to international capital markets, trade finance and development
financing. Crown Agents Bank has a 30-year history as a correspondent partner to Guyana.

**[I] A Citibank presence is a meaningful signal. But as representative offices they will not
directly serve a small business — the benefit reaches an SME indirectly, through its local bank,
over time.**

### The banks

**[V] Licensed commercial banks:** Republic Bank (Guyana), GBTI, Demerara Bank, Citizens Bank,
Bank of Baroda (Guyana), Scotiabank.

**⚠ Correcting a common error.** Republic Bank did **not** acquire Scotiabank Guyana in 2019 — the
sale was **blocked by the Bank of Guyana** on competition grounds. A 2021 agreement to sell to First
Citizens (Trinidad) **expired and was terminated in June 2022**. From **1 November 2025** Bank of
Nova Scotia transferred its Guyana branch operations to **Scotiabank Guyana Inc.**, a locally
registered wholly-owned subsidiary. **Scotiabank remains. First Citizens does not operate in Guyana.**

**[V]** Firms commonly use letters of credit, bank drafts and manager's cheques. **Creditinfo Guyana**
provides credit assessments. **[U/R]** No Guyana-specific evidence on prevailing trade credit terms —
treat net-30 assumptions as unknown.

### Remittances

**[V]** 3.27% of GDP in 2023, but inflows rose from ~US$380m (2019) to **~US$549m (2023), +44%**.
**[I]** The falling percentage against rising absolute value is an artefact of oil GDP growth.
**For a consumer-facing SME outside Georgetown, diaspora money is a real part of the customer's
wallet.**

**⚠ Data gap: Guyana is not covered by the World Bank Global Findex. There is no reliable public
figure for Guyanese bank account ownership or digital payment usage.** Anyone quoting one is
estimating.

---

## 2. E-commerce and digital

### Connectivity — better than commonly assumed

**[V]** DataReportal, reference date October 2025:

| Metric | Value | Penetration |
|---|---|---|
| **Internet users** | **684,000** | **81.7%** |
| Cellular connections | 706,000 | 84.3% |
| — 3G/4G/5G | — | 89.5% of connections |
| **Social media identities** | **577,000** | **69.0%** (+14.6% YoY) |
| Urban / rural | — | 27.5% / 72.5% |
| Median age | 26.2 years | — |

**⚠ Sharp conflict with the official US figure.** trade.gov states internet penetration at
approximately 52% as of 2024. **[I] These are irreconcilable. DataReportal typically counts anyone
with any access; trade.gov may be citing fixed-broadband subscription. The truth is probably that
*access* is high and *quality, regular* access is considerably lower. Do not build a business case
on either number alone.**

**[V] Fibre is the enabling story.** One Communications' FTTH network passes **more than
three-quarters of Guyanese households — 170,000+ homes and businesses** (Nov 2025). Digicel announced
further expansion May 2026. First 5G launched 2023; **Bartica received its first direct domestic
fibre-optic submarine cable in August 2025**; number portability launched 10 Feb 2025.
**[V] GTT rebranded to One Communications on 6 September 2024.**

### Social commerce — this is the actual e-commerce channel

**[V] Facebook is overwhelmingly dominant** — ad reach equals **69.0% of the total population**,
growing 14.6% YoY. Instagram reaches 193,000 (23.0%), Messenger 377,000 (45.1%).

**[V] How Guyanese SMEs actually sell:** Facebook pages and groups have become the storefronts, with
WhatsApp the primary channel for enquiries and promotions. Home-based and informal businesses market
via Facebook posts and WhatsApp broadcasts, coordinating orders through messaging apps
**without e-commerce websites.**

**[I] This is the single most important practical fact in this section. For most Guyanese small
businesses the correct e-commerce strategy is *not* to build a website. It is a Facebook page, a
WhatsApp Business number, MMG for payment, and a courier for delivery. That stack costs almost
nothing, matches how customers already behave, and sidesteps the gateway problem entirely. A website
is a later-stage decision, justified by scale or by selling outside Guyana.**

**[V] Formal e-commerce is nascent.** An **e-commerce bill has been prioritised but is still not
tabled in parliament.** Regulatory gaps persist in data protection, AI regulation and cybersecurity;
an ICT Masterplan 2030 is planned. **[U]** Local marketplaces include BUY.gy and ShopGT; scale
unverified.

### Delivery and courier

**[V] Food delivery:** **GT Eats** is the leading platform — Georgetown-based, founded 2022, fully
digital and cashless, distance-based fees, real-time tracking. **Service limited to greater
Georgetown.**

**[V] Parcel and general courier** — a real and growing ecosystem: **Headstart Delivery** (Georgetown,
East Coast, East Bank, West Coast, West Bank, Linden, Berbice, plus pickup/ship to Regions 1 and 9),
**A2Z Couriers** (nationwide), Xpress Delivery Service, BAC Couriers. **[U]** ~16 delivery services
operating in Georgetown as of October 2025.

**[V] International express:** FedEx, UPS and DHL all serve Guyana, but true overnight service is
rarely achievable given distance (five hours from Miami, six from New York) and frequent
weather-related flight delays.

### Consumer payment behaviour online

**[V]** Cash on delivery remains widely used alongside debit cards and local bank transfers. Trust is
a documented barrier — cybercrime, fraud and privacy concerns deter online shopping, compounded by
the absence of e-commerce legislation.

**[I] Design for cash on delivery from day one. It is not a fallback in this market; for a large
share of customers it is the only option they trust. That has direct consequences: a reconciliation
process, driver cash-handling controls, and working capital to cover goods in transit.**

---

## 3. Logistics and supply chain

### Import process

**[V] Everything runs through ASYCUDA World.** The importer or licensed customs broker files an
**electronic Single Administrative Document (eSAD)** attaching invoice, bill of lading/airway bill,
exemption letters, import licence and CARICOM Certificate of Origin where applicable.

**Mandatory:** bill of lading/airway bill, commercial invoice, **TIN** (every importer must be
GRA-registered), applicable permits, valuation support.

**[V] Valuation disputes are a live risk.** If Customs disputes declared value, the broker files a
**C32A** — a sworn oath the value is true. If Customs is unsatisfied it issues a **C32B** setting a
new value and recalculated taxes.

**[I] A small importer with thin supplier paperwork can be uplifted on value and hit with unbudgeted
duty and VAT. Budget a contingency, and insist on properly detailed commercial invoices — doubly
important now that those same invoices gate FX access.**

**[V] Import licences** are needed only for controlled goods, issued by MINTIC. The restricted list
covers meat, fruit, beet sugar, wheat flour, rice, sugar, cooking oils, animal feeds, plants and
vegetables, pharmaceuticals, cosmetics, petroleum products, fertilizer, telecom apparatus, aircraft,
firearms, and scrap/copper waste.

**[V] Multi-agency approvals are the hidden delay.** Food, drugs and cosmetics need GA-FDD and
Ministry of Health clearance. trade.gov states additional agency approvals "significantly increase
the time required" and that processes remain "time consuming and cumbersome."

**[V]** Electronic payment of customs declarations is available through **GBTI and Demerara Bank**.

### Duties, VAT and levies

| Charge | Rate | Basis |
|---|---|---|
| Common External Tariff | **5–20%** typical | CIF [V] |
| CET, agricultural | up to **40%** | CIF [V] |
| **VAT** | **14%** | CIF **+ duty + all other taxes** [V] |
| Environmental levy | **G$10/unit** | per non-returnable beverage container [V] |
| Excise — alcohol | 40% | value incl. freight, insurance, duty [V] |
| Excise — tobacco | 100% | same [V] |
| Excise — fuel | 50% | same [V] |

**[I] The tax stack compounds.** VAT applies to the duty-inclusive value, so a 20% CET item lands at
roughly **CIF × 1.20 × 1.14 ≈ 1.37× CIF** before broker, port and haulage.

**[V] VAT registration threshold is G$15 million** in annual taxable supplies. **[I] Below it you
cannot reclaim input VAT on imports — a genuine cash-flow trap for a growing importer sitting just
under the line.**

**[V] Budget 2026 changes effective 16 Feb 2026:** VAT removed on vehicles under 1500cc (under 4
years old) and hybrids under 2000cc; **all import duties and taxes eliminated on ATVs and outboard
engines up to 150hp**; **VAT removed on fertilisers, agrochemicals, pesticides, and farming/mining
machinery**; VAT removed on locally manufactured furniture.

**[V] Renewable energy technologies are VAT-exempt on import. [I] This materially improves
solar-plus-battery economics against a diesel generator — see section 4.**

### Customs brokers

**[V]** GRA's own guidance assumes broker involvement; the eSAD, C32A mechanism and multi-agency
permit chain all reward familiarity. GRA maintains a register of licensed brokers.

**[V] GRA statutory fees** (government charges, *not* the broker's service fee): broker licence
G$15,000/yr; processing customs forms G$1,000; entering and clearing G$2,000; customs seal G$500;
out-of-hours service G$4,000; ship clearance G$10,000–20,000 by tonnage.

**⚠ [U] Broker service fees are not published anywhere. Obtain three written quotes.**

### Freight — routes, costs, lead times

**From the USA (the dominant SME route)**
- **[U] FCL indicative:** Miami→Georgetown ~US$3,160 (20ft), ~US$3,960 (40ft), quoted ranges
  US$2,300–5,800 and US$3,900–8,200. These are broker marketing figures — **treat ~US$3,000–5,000 for
  a 20ft as an order-of-magnitude band**
- **[V] Weekly consolidator:** Laparkan sails **Mondays** to Georgetown, operating its own Guyana
  offices rather than agents
- **[U] Barrel/small-parcel:** Laparkan GtPAK ~US$8.35 first pound + US$3.40/additional pound,
  inclusive of clearance and Georgetown delivery. **[I] The practical channel for a micro-importer
  moving under a cubic metre**
- **[U] Transit:** 3–6 weeks door-to-door

**From China [U]** — transit 35–55 days port-to-port; FCL ~6 weeks, **LCL 8–12 weeks**; air 4–7 days.
Rates June 2026: Yantian→Georgetown 40HC US$7,351–7,987 all-in. LCL ~US$120/CBM; FCL crossover
around 12–15 CBM.

**From Trinidad — and the chronic risk it creates**
- **[V]** Guyana depends heavily on Trinidad transshipment. MSC runs weekly Georgetown–Port of
  Spain–Paramaribo; CMA CGM sails weekly Port of Spain→Suriname/Guyana/French Guiana
- **[V] This actively fails.** The Shipping Association of Guyana reported Port of Spain congestion
  limiting loading of Guyana-bound containers, forcing lobbying to prioritise Guyana berthing
  (April 2026); hurricane disruption affected cargo flow in Nov 2025
- **[V]** CMA CGM has applied a **Port Congestion Surcharge specifically to Georgetown**

**[V] Where the bottleneck actually is.** Vessel port stay at Georgetown averages just **1.2 days**.
**[I] The delay is not Georgetown berthing — it is the Trinidad transshipment leg and ground-side
clearance. Add 1–2 weeks to any Trinidad-routed shipment.**

### Port infrastructure

**[V] Georgetown is shallow and river-constrained:** ~2 nautical miles of river frontage, 39 berths,
six main wharves at **2.5–6.0 m depth at low water**, **maximum draught ~8.2 m**. Main private
terminal operators: **John Fernandes Ltd, Muneshwers Ltd, GNIC**.

**[I] Guyana cannot receive mainline vessels directly. Everything arrives on small feeders, mostly
via Trinidad — which is precisely why unit freight is high and why one upstream disruption cascades
through the whole import chain.**

**[V] Deep-water port — two tracks, both pre-operational:** a private JV (Muneshwers + John
Fernandes) in advanced funding talks; and the **Berbice Deep-Water Port** (~US$285m, 9–10 m depth),
with Bechtel advancing design and a US EXIM Bank letter of interest issued April 2026.
**[I] Neither is operating. Do not model 2026–2028 freight costs on the assumption they will be.**

### Roads and domestic distribution

**[V] The new Bharrat Jagdeo Demerara River Bridge opened 6 October 2025** — 2.6–2.8 km cable-stayed,
four lanes, 50 m vessel clearance, built for **US$260.8m with no cost overruns**. **Toll-free, 24/7**,
with clearance for ships to pass underneath — **eliminating the old floating bridge's retraction
closures** that used to strand trucks.

**[I] A genuine, already-delivered improvement. East Bank ↔ West Bank/West Coast logistics is now
materially more predictable, and scheduled retraction windows are no longer a delivery-planning
constraint. It also creates opportunity along the West Bank/Region Three corridor.**

**[V] Essequibo is ferry-dependent and tide-driven.** Parika–Supenaam runs from 05:00 with further
sailings around 10:00–12:00, 16:00 and 18:30 — but **Essequibo departure times follow the tides and
change daily**; T&HD publishes a fresh day-by-day schedule monthly, "subject to change without
notice." Online booking via FerryPass.gy covers Parika–Supenaam, Parika–Bartica, Leguan and Wakenaam.

**[I] A tide-driven, month-by-month schedule is not something you can promise a customer against. Any
Essequibo delivery commitment needs a ±1 day tolerance, and vehicle slots must be pre-booked.**

**[U] Bartica/riverine:** MV Makouria departs Parika 05:00 daily, Bartica 12:00, no Sunday service.
Ferry 3–4 hours; speedboat ~1 hour at ~G$2,500 per person. **[I] Speedboats move people and small
parcels; vehicles and pallets must wait for the ferry.**

**[V] Lethem / Region 9 — transforming right now:**
- **Linden–Mabura Hill (121 km): 86% complete, ~100 km paved, targeted completion August 2026.**
  Travel time on that stretch has fallen from up to ten hours to about one
- Full programme: **450 km** upgraded to all-weather standard. On completion, **Linden→Lethem drops
  from 12+ hours to about four**
- **Phase 2 (Mabura–Lethem) is not yet delivered.** The unpaved section remains seasonally unreliable

**⚠ [U] Georgetown→Lethem trucking rates: not found.**

**[V] Domestic air:** Trans Guyana Airways serves 50+ hinterland destinations and is the **only
ISSA-certified operator** in Guyana; it cut hinterland airfares 7% in January 2026. Air Services
Limited offers charters and medevac. **⚠ Published domestic air *cargo* tariffs not found.**

**[V] Brazil border (Lethem–Bonfim):** the Takutu River Bridge opened 2009. Both governments have
committed to improving customs and immigration procedures — which implies current friction — and
frame the Linden–Lethem road as opening access to a **northern Brazil market of ~20 million people**.

**⚠ Critical caveat: no data on Lethem–Bonfim trade volumes, tariff treatment or border formalities.
Guyana is CARICOM, Brazil is Mercosur — there is no free-trade access. Do not assume tariff-free
flow.**

### Warehousing

**[V] Observed listings:** 21,800 sq ft, East Bank Demerara at **G$3.2m/month** (~US$0.70/sq ft/mo);
4,800 sq ft, Water & Schumaker Streets, price on application; 3,600 sq ft storage land, Eccles.

**[U] One data point is not a market rate.** Smaller units almost certainly price higher per sq ft.
Purpose-built racked dry warehousing is thin — most listings are adapted buildings.

**[U] Bonded warehousing** exists in law (Customs Act Ch. 82:01) but **no published application
procedure or fee schedule was found. Confirm with GRA.**

---

## 4. Utilities and infrastructure

### Electricity — tariffs

**[V] GPL published tariff, effective 11 April 2021 and still operative:**

| Class | Fixed (G$/mo) | Energy (G$/kWh) | ≈ USD/kWh |
|---|---|---|---|
| **Commercial (B)** | 2,467.00 | **56.38** | **~US$0.27** |
| Industrial (C) | 1,760.22 | 50.93 | ~US$0.244 |
| Industrial (D) | 1,760.22 | 48.78 | ~US$0.233 |
| Residential (>75 kWh) | 351.04 | 43.43 | ~US$0.208 |

**[I] At ~US$0.27/kWh, commercial power costs roughly 2–3× typical US commercial rates. For anything
electricity-intensive — cold storage, food processing, laundry, machining — energy is a first-order
line item, not overhead.** Note also that the commercial fixed charge (G$2,467) is *higher* than the
industrial one: a small commercial customer pays a larger standing charge than a factory.

### Electricity — reliability

**[V] Improving but still poor:**

| Metric | 2024 | 2025 | 2025 target |
|---|---|---|---|
| **SAIDI** (avg outage minutes) | 125 | **84** | 80 |
| **SAIFI** (interruptions) | 126 | **86** | 85 |

**[V] The problem is the network, not capacity.** GPL has **>250 MW** of reliable capacity against
~210 MW demand, but T&D infrastructure is described by the Prime Minister as "brittle."
**GPL lost 25% of all power generated in 2024** — 12% commercial (illegal connections), the rest
technical.

**[V] Recent failures were construction strikes:** June 2026, an excavator struck a transmission line
between Golden Grove and Sophia; April 2026, road-expansion equipment contacted high-voltage cables.
**[I] Guyana's construction boom is itself a leading cause of outages. Expect this to continue.**

### Generators — a counter-intuitive finding

**[V] Fuel prices:** diesel **G$168.00/litre (US$0.80/L)**, Feb 2026; gasoline G$235.00/litre.

**[I] Running-cost calculation:** a small diesel genset consuming ~0.35 L/kWh at G$168/L implies
**~G$59/kWh in fuel alone** — before capital, servicing and oil. GPL's commercial rate is
**G$56.38/kWh**.

**A generator in Guyana is reliability insurance, not a cheaper alternative to the grid.** State this
explicitly to clients — businesses sometimes assume self-generation saves money. It does not. And
since **renewable technologies are VAT-exempt on import**, solar-plus-battery is the better economic
hedge for a business that needs continuity.

### The Karpowership dependency

**[V]** Guyana leans on two Turkish powerships: 60 MW at Meadow Bank and 36 MW at Everton, against
>220 MW peak demand. **The 2026 standoff was serious** — the contract expired 21 May 2026,
Karpowership granted only a one-week extension and demanded a rate rise from US$0.076 to
US$0.095/kWh (an extra **G$3.4 million per day**) under explicit threat of supply interruption.
**Resolved 1 July 2026:** a two-year contract at 36 MW / US$0.095 per kWh, taking the annual bill to
**US$28,780,832**.

**[I] Rising wholesale supply cost creates upward pressure on retail tariffs. Do not assume the April
2021 tariff schedule holds indefinitely.**

### Gas-to-Energy (Wales) — repeatedly delayed

**[V] The timeline has slipped continuously.** Originally expected end-2024; as of June 2026 the
contractor commits to **one of four turbines online by end-2026**, all gas turbines by **Q1 2027**,
combined-cycle by **June 2027**. **The two-year delay has cost ~US$884 million above initial cost.
The promised 50% electricity cost cut has not materialised.**

**[I] Recommendation: model electricity at current tariffs through at least end-2027. Treat any
reduction as upside, never as baseline.**

### Water

**[U] Tariffs — aggregator-sourced; GWI's official pricing page failed to load. Verify directly.**

| Category | Rate |
|---|---|
| **Non-residential, metered** | **G$143/m³** + G$500/mo fixed |
| Non-residential unmetered — small | G$2,850/mo |
| — medium | G$7,600/mo |
| — large commercial | G$14,250/mo |
| — large industrial | G$22,800/mo |
| **New non-residential connection** | **G$16,000** |

Water is cheap in absolute terms: G$143/m³ ≈ US$0.68 per cubic metre.
**[V]** Treated-water coverage rose from 52% (2020) to 77% (end-2025).

**[V] But pressure is a genuine operational problem.** South Georgetown residents faced nearly three
weeks of unusually low pressure, with reports that ground-level tanks could not fill. A major project
aimed to raise pressure from **2 psi to 6 psi**, short of its 10 psi target.

**[I] Storage tanks and booster pumps are not optional. At 2–6 psi, mains pressure will not reliably
fill an elevated tank, let alone run equipment. Any premises fit-out must budget for a ground tank, a
pump, and an elevated or pressurised tank. And since water treatment and pumping depend on GPL, a
power outage is often also a water outage — size storage for both.**

### Internet

**[V] ENet (E-Networks) — the most transparent pricing available:**
**300 Mbps: G$8,900/mo** (~US$43) · 350/100 Mbps: G$13,100/mo · 1,000/500 Mbps: G$26,300/mo.
Coverage: Georgetown, Linden, Anna Regina, Corriverton, New Amsterdam.

**[V] Structurally important:** ENet has **removed the distinction between business and residential
internet**. **[I] A small business can buy retail-priced fibre — but should not expect a business SLA
at these prices.**

**⚠ [U] One Communications (GTT) and Digicel Business pricing could not be obtained. Get direct
quotes.**

**[V] Starlink launched in Guyana April 2025**, orderable directly with ~4–6 week kit shipping.
**[U] Pricing:** Residential Lite G$7,400/mo; Residential G$11,000/mo; Roam Unlimited G$21,000/mo.

**[I] Starlink at ~G$11,000/mo (~US$53) is cheaper than ENet's mid-tier fibre and works where no
fibre exists. For a business in Lethem, Bartica, Mahdia or Region 9, Starlink is the primary
connectivity answer, not a backup.**

### Commercial rent

**[V] Observed priced listings (Georgetown):**

| Location | Size | Rent | Derived |
|---|---|---|---|
| **Regent Street** | ~5,000 sq ft | **US$6,000/mo** | ~US$1.20/sq ft/mo |
| **Station St, Kitty** | 1,500 sq ft | **US$2,900/mo** | ~US$1.93/sq ft/mo |
| **East Bank Demerara** (warehouse) | 21,800 sq ft | **G$3.2m/mo** | ~US$0.70/sq ft/mo |

**[U] Indicative structure:** prime Georgetown retail/office ~US$1.20–2.00/sq ft/month; East Bank
warehouse ~US$0.70/sq ft/month. **This is three data points. Do not treat as market rates without a
broker's opinion.**

**[V] Rents are rising sharply** — forward projections of ~15–20%/yr in premium Georgetown
neighbourhoods and up to 25% on the East Bank Demerara commercial corridor.

**[I] With 15–25% annual escalation projected, lease term length and escalation caps are among the
highest-value negotiation points available to a small business in Georgetown right now. Lock in
length; cap the escalator.**

**⚠ No priced listings found for New Amsterdam, Linden, Anna Regina or Lethem. Contact local
brokers — do not assume a discount ratio.**

---

## 5. Labour market

### Wages — the structural fact

**[V] Private sector minimum wage: G$60,147/month** (G$2,776/day, G$347/hour), set by National
Minimum Wage Order No. 20 of 2022, effective 1 July 2022. Still G$60,147 as of late 2025; a December
2025 motion to raise it to G$100,000 was tabled. **⚠ [U] Status as of July 2026 unconfirmed.**

**[V] Public sector floor: G$100,000/month.** Part-time government workers went from G$40,000 to
G$50,000.

**[I] There is a ~66% gap between the private legal minimum and the public sector floor. This is the
most important wage fact for a Guyanese SME. A business paying the legal minimum is paying materially
below what the state pays for unskilled labour — which makes G$100,000, not G$60,147, the effective
reservation wage.**

### Statutory employment costs

| Item | Rule |
|---|---|
| **NIS employee** | 5.6% of gross [V] |
| **NIS employer** | **8.4%** of gross [V] |
| NIS ceiling | G$280,000/mo insurable earnings [V] |
| **PAYE threshold (2026)** | **G$140,000/month** (raised from 130,000) [V] |
| PAYE rates (2026) | **25%** up to G$3.36m/yr chargeable; **35%** above [V] |
| Child deduction | G$10,000/mo per child under 18 [V] |
| Standard hours | 8/day, 40/week over ≤5 days [V] |
| Annual leave | 12 days/yr (1–10 yrs service); 24 days/yr after 10 [V] |
| Maternity | 13 weeks, +13 for complications; NIS-paid [V] |
| **Severance** | 1 wk/yr (yrs 1–5); 2 wks/yr (6–10); 3 wks/yr (10+), capped at 52 weeks [V] |
| **Corporate tax** | 40% commercial / 25% non-commercial; **agriculture and agro-processing fully exempt from 2026** [V] |

*(Cross-check these against `guyana-compliance.md`, which is the authoritative file for statutory
obligations.)*

**[I] Practical cost:** on a G$100,000 wage, employer NIS adds G$8,400 → **true cost ~G$108,400
(~US$519)/month**. Below G$140,000 there is no PAYE. **This is why many SMEs cluster wages at or just
under 140,000 — it is the point where the employee's take-home is maximised per dollar of employer
cost.**

### Salary ranges by role

**⚠ READ THIS BEFORE THE TABLE. Guyana has no published official occupational wage survey.** Every
figure below comes from international salary aggregators modelling from thin samples with often stale
base years. **All rows are [U] and very likely understated**, because Guyana has had rapid nominal
wage growth since 2022 and these datasets anchor to pre-boom baselines.

**Calibrate against these verified anchors instead:** average gross monthly salary ~G$100,000;
**median monthly income ~G$50,000** — the mean being double the median tells you the distribution is
heavily skewed by a small high-paid oil/professional tier. Public sector floor G$100,000. PAYE
threshold G$140,000. Entrepreneurs report raising wages **~30% over two years**.

| Role | Indicative G$/month | ≈ USD |
|---|---|---|
| Construction labourer (unskilled) | 60,000 – 100,000 | 290 – 480 |
| Retail clerk / shop assistant | 60,000 – 110,000 | 290 – 525 |
| Cleaner | ~87,000 | ~415 |
| Security guard | ~50,000 – 95,000 | 240 – 450 |
| Driver | ~51,000 (likely understated) | ~245 |
| Admin / office clerk | 80,000 – 150,000 | 380 – 720 |
| Chef / cook | 70,000 – 160,000 | 335 – 765 |
| **Welder** | **86,000 – 184,000** | 415 – 880 |
| Electrician / technician | 100,000 – 200,000 | 480 – 960 |
| Heavy equipment operator | 120,000 – 250,000+ | 575 – 1,200+ |
| **Accountant / bookkeeper** | 58,000 – 352,000 (ACCA at top) | 275 – 1,690 |
| IT / software developer | ~79,000 – 250,000 | 375 – 1,195 |

**[V] Certified oil-sector trades break this table entirely.** 6G welders, pipefitters and
electricians with offshore endorsements command day rates that rival executive salaries. Petroleum
engineers, drilling supervisors, subsea technicians and HSE managers are often **paid in USD with
housing, transport and international allowances.**

**[I] Budgeting advice: ignore the aggregator tables. Budget off (i) G$100,000 as the effective
reservation wage for unskilled staff, (ii) G$140,000 as the tax-free ceiling that shapes offers, and
(iii) a 20–40% premium above those for any certified trade.**

### Employment and participation

| Indicator | Value | Period |
|---|---|---|
| **Unemployment** | **6.8%** (from 14.5% in Q3 2021) | Q4 2024 [V] |
| **Labour force participation** | **56.5%** | Q4 2024 [V] |
| Youth unemployment (national survey) | **12.1%** (from 31.9%) | Q4 2024 [V] |
| Youth unemployment (ILO modelled) | **24.9%** | 2025 [V] |
| Employers as % of employed | 12.0% (from 5.4%) | Q4 2024 [V] |

**⚠ Two cautions.** The national and ILO youth unemployment figures differ by a **factor of two** and
are not reconcilable — the survey was reinstated after a multi-year gap, so the 2021→2024 comparison
spans a methodological discontinuity. And older sources still cite 14.5% unemployment from 2021 data;
that is superseded. **Note also the ~14-month publication lag — there is no 2025 or 2026 labour data.**

**[I] Read the participation rate carefully. At 56.5%, over 40% of working-age Guyanese are outside
the labour force entirely. Low unemployment plus low participation is the signature of a labour
market where much activity is informal or discouraged — not of genuine full employment.**

### The skills shortage

**[V] It is real and quantified.** 81% of occupations in strongest demand require higher technical
education or a degree; **~53,000 additional workers needed within five years** across construction,
healthcare and agriculture. Construction alone has an ILO-projected gap of **8,905 workers over five
years**.

**[V] Training pipeline:** Board of Industrial Training ~**3,587 beneficiaries in 2025** — welding,
heavy-duty equipment operation, electrical installation, commercial food preparation, IT, A/C
refrigeration, cosmetology. **All government TVET institutions became tuition-free from January
2025.** GOAL scholarships: 54,627 cumulative awards 2021–2026, but only **~6,624 completions (~12%)**.

**[I] The arithmetic doesn't close. BIT throughput of ~3,600/year is an order of magnitude below the
stated ~53,000 five-year need, and GOAL's 12% completion rate means scholarship volume badly
overstates skills actually added. An SME should assume it will have to train in-house — and that
anyone it trains becomes a poaching target.**

### Oil sector effects on wages and retention

**[V]** Wage inflation is broad — **~30% rises over two years** reported by entrepreneurs.
**Poaching reaches the state itself:** the Police Commissioner publicly linked a Guyana Police Force
retention crisis directly to energy-sector competition. **68% of the oil sector workforce is
Guyanese.** Exxon and major contractors publicly back government pressure for "fair pay for skilled
Guyanese workers" — **upward wage pressure is being institutionalised, not resisted.** Dutch disease
is acknowledged by Exxon itself. **But wages have NOT kept pace outside oil** — in agriculture,
mining and services, wages have not matched the cost-of-living increases the boom created.

**[I] If the police force cannot hold staff against oil-sector pay, a private SME certainly cannot
compete on wages. What has reset is expectations — staff benchmark against packages including USD
pay, housing and transport allowances. The retention levers actually available to an SME are
non-wage: flexibility, training-with-bond, family employment, visible promotion paths, and paying at
or above the G$140,000 tax-free line.**

### Migration

**[V] Brain drain is extreme and has NOT reversed despite the oil boom.** Guyana has lost
approximately **89% of its tertiary-educated population** to emigration. The UNDP 2026 report ranks
Guyana **12th globally and 4th in Latin America and the Caribbean** for brain drain, with the highest
human-capital-loss score in South America — **above Venezuela and Suriname**. Return migration is
marginal: ~2,000 re-migrant applications since 2020 against a diaspora of 500,000+.

**[V] Immigrant labour:** **Venezuelans ~25,000 officially (~3% of population)**, likely higher.
**Critical legal point: a three-month renewable stay permit does not confer the right to dependent
employment** — formal employment requires an employer-sponsored work permit. **64% reported being
unemployed (2021).** **Haitians** are CARICOM members but **excluded from CSME free movement**.
Cubans enter visa-free.

**[V/U] Work permits:** the employer must initiate — individuals cannot self-apply. **[U]** Fee
G$28,700 (~US$140), valid three years; applications must be filed **before** obtaining Permission to
Land. Employers must show GRA tax compliance and current NIS contributions. **[V] CARICOM nationals
with a CSME Skills Certificate are exempt — the certificate costs G$1,500 and does not expire.**

**[I] Two practical conclusions. First, the CSME Skills Certificate route (G$1,500, no expiry, no
permit) is dramatically cheaper and faster than a work permit — for an SME needing skilled staff,
recruiting a qualifying CARICOM national is the path of least resistance. Second, Venezuelan labour
is abundant and cheap but legally hazardous: employing a stay-permit holder in dependent employment
without a sponsored work permit is non-compliant, and the enforcement risk sits with the employer.**

---

## 6. Business culture, informality and failure modes

### Business culture

**⚠ [U] on this entire subsection.** Available sources are business-etiquette guides rather than
research. Treat as orientation, not evidence.

Consistent themes: **relationship-first** negotiation, expect multiple meetings, avoid hard-pressure
tactics · **meetings open with personal and family conversation** — this is the trust-building
mechanism, not small talk to be skipped · titles and hierarchy matter until first names are invited ·
**consensus decision-making lengthens timelines** but produces more durable agreements ·
**ethnic and religious diversity requires deliberate neutrality** — Guyanese politics is ethnically
polarised and all sources advise avoiding sensitive topics.

**[V] Ethnic composition and commercial history:** Indo-Guyanese ~40%, concentrated in rural
agricultural regions; Afro-Guyanese ~29%, predominating in urban centres. Portuguese (Madeiran)
arrived 1835 and by the 1850s–60s held a near-monopoly on retail trade. Chinese arrived from 1853 and
by the 1890s held 50% of food shops and 90% of liquor shops.

**⚠ Correcting a common assumption: no evidence of a significant Lebanese trading community in
Guyana.** This appears to be a conflation with Trinidad, Jamaica or Suriname.

**[I] The historical pattern is ethnically-clustered trade specialisation, and contemporary residue
is likely — supplier credit, informal lending and referral networks running along family and
community lines. But no current research quantifies this. A newcomer without an existing network
should expect supplier terms and credit access to come more slowly than for an incumbent family firm.**

**⚠ No Guyana-specific research on family business prevalence or succession outcomes exists.**

### The informal economy

**[V] Two measures, both cited in the US State Department's 2024 report:**
**informal employment ~50% of workers** (Guyana Bureau of Statistics) and
**informal economy ~35% of total economic activity** (IMF).
**[I] These are not contradictory** — one counts workers, the other output; informal work is
lower-productivity, hence a smaller output share than headcount share.

**[V] Corroborating signal:** the government frames the new Development Bank as "an instrument of
formalisation — pulling informal operators into the visible economy where they become taxable,
auditable, and legible to credit."

**[I] This is arguably the largest structural challenge facing a compliant Guyanese SME. Roughly half
your competitors, suppliers and potential employees operate informally — no VAT, no NIS, no PAYE, no
registration. A formalised business carries a real cost disadvantage (8.4% employer NIS, 14% VAT,
licensing) against informal competitors selling identical goods. Acknowledge this honestly when
advising formalisation, and lead with what formalisation *unlocks* — credit, contracts, procurement —
rather than pretending the cost is not real.**

### Business registration

**[V] Sequence and cost:** DCRA business name registration **G$6,500** first registration, G$2,500
annual renewal, **up to 3 business days** → GRA TIN, application free, **G$1,000** for the
certificate → VAT registration if above G$15m → NIS employer registration → local council business
licence → sector-specific licences. Company incorporation takes **5–10 business days**; express
processing reduces this to 2–5 days [U].

**[V] Timing has genuinely improved** — registration fell from three weeks to **under one week**
through digitisation.

**[I] Total headline cost is ~G$7,500 (~US$36) for name plus TIN. Registration cost is not the
barrier. The barrier is subsequent compliance burden and the ongoing advantage of remaining
invisible.**

**⚠ On Ease of Doing Business:** Guyana ranked 134th of 190 in the final editions. **The World Bank
discontinued the report in 2021. Anyone citing a current Guyana DB rank is citing stale data.**

### Corruption and bureaucracy

**[V] Transparency International CPI 2025: Guyana scores 40/100, ranked 84 of 182.** Guyana is one of
only a small number of countries in the Americas to have **improved significantly since 2012**. But
TI flags a countervailing trend: harassment and intimidation of independent media and civil society
curtailing oversight.

**[V] Bureaucratic friction**, per the State Department: government processes remain "slow and
somewhat confusing," particularly public procurement, with tenders sometimes changing and being
re-issued; many businesses find the taxation system "confusing and complicated."

**⚠ [U] On "who you know": sources support opaque procurement and a relationship-driven culture, but
no survey data quantifies bribery incidence in Guyana. Do not assert a prevalence figure.**

### Access to finance

**[V]** Weighted average lending rate 7.79–7.90%; for business loans specifically banks charge
**8–14%** and *"require property collateral on terms that effectively exclude most of the
entrepreneurial population."*

**[I] 8–14% is not prohibitive. The requirement for registered real property as security is —
because most small operators do not hold clean transported title, and in agriculture the land is
often held on lease rather than freehold.** See `guyana-finance-ecosystem.md` for the full picture.

### Failure modes

**[V] The one substantive academic study is the IDB's *Small Business Survival in Guyana*** — a
country-wide survey of **380 SMEs**. Survival was consistently explained by **gender, location, and
economic activity**. SMEs operate "in a less than auspicious business climate, and their failure rate
is high." Lack of access to credit is "one of the perennial complaints."

**⚠ Notably, undercapitalisation was NOT identified as an independent determinant of survival.**

| Failure mode | Confidence |
|---|---|
| **Access to credit / collateral** | **[V]** — best evidenced |
| **Competition from informal operators** | [V] inference from verified data |
| **Staff recruitment and retention** | [V] |
| **Wage cost escalation** | [V] |
| **Tax complexity** | [V] |
| **Procurement opacity** | [V] |
| Crime / security costs | [V] on crime; [U] on cost |
| Record-keeping weakness | [U] inferred |
| Undercapitalisation | **⚠ [U] contradicted by the one study** |
| Competition from imports | **[U] no Guyana-specific evidence. Do not assert** |
| Family / succession issues | [U] gap |

### Crime and security

**[V] Improving in aggregate:** serious crimes fell to **801 in 2025 from 1,070 in 2024 (−25%)**, the
lowest in a decade.

**[V] But businesses are specifically targeted.** Armed robberies including carjackings "occur
regularly, especially in businesses and shopping districts," frequently in Georgetown. Criminals are
often organised, travel in groups, **conduct surveillance on targets**, and use handguns, knives,
machetes or cutlasses.

**[V] The risk is concentrated in time and place: Region Four-A (Georgetown) records the highest
number of armed robberies, between 6pm and midnight.** Intensified police deployment in those hours
produced 63 fewer attacks than 2024.

**[I] That is actionable. If a client operates a cash business in Georgetown, the single
highest-value security intervention is managing the 6pm–midnight window — closing procedures, cash
handling, banking runs, lighting and staffing.**

**Praedial larceny — [V] that it exists and is policy-relevant; [U]/[R] on scale.** Guyana-specific
quantification is essentially absent; most searches return Jamaican, Barbadian and Antiguan data.
**[V] One Guyana-specific data point:** the main method of disposing of stolen produce is the
**higgler trade (32.1%)**. **[V] Cattle rustling is active and adapting** — in February 2026 Berbice
rustlers shifted to a "brand and run" scheme, illegally branding calves and claiming ownership. The
Agriculture Minister stressed that **unbranded animals are effectively unrecoverable**. **[V] The
legal deterrent is weak** — a fine of not less than G$15,000 (~US$72) or 10 months' imprisonment.
**[I] A G$15,000 minimum fine is not a deterrent at 2026 price levels.**

**[I] Practical advice for an agricultural client: brand or tag every animal. Per the Minister's own
statement, it is the difference between a recoverable asset and a total loss.**

---

## 7. Key sectors for SMEs

### Agriculture and agro-processing

**[V] Budget 2026 removes corporate taxes on agriculture and agro-processing businesses.**
**[I] This is the single largest fiscal incentive available to a Guyanese small business today.**

**[V]** Agriculture is ~23.2% of non-oil GDP. Budget 2026 allocates **G$113.2 billion** — Drainage &
Irrigation G$81.9bn, Sugar G$13.4bn, **Agro-processing G$745m** (fruit pulping hubs, cold storage,
packaging, agro-processor training, Parika agro-processing port), Fisheries G$2.3bn.

| Sub-sector | Status |
|---|---|
| **Rice** | **Strongest performer.** ~810,000–825,000 t in 2025, up from ~500–550k in 2020. Cuba bought **US$124.41m** in 2025 [V] — **[I] note the concentration risk in a politically fragile buyer** |
| **Sugar (GuySuCo)** | **Structurally distressed.** 59,200 t in 2025, missing target; worker turnout hit an **all-time low of 30%** [V]. **[I] Not a supplier opportunity — an opportunity as a source of released labour and land** |
| **Coconut** | **Genuine SME opportunity.** ~33,000 acres, up 7,100 since 2020. Guyana supplies ~20% of regional demand. Value-added: water, oil, fibre, bio-fertiliser [V] |
| **Brackish-water shrimp** | **Standout growth.** Monthly output went from <10,000 kg (2021) to ~145,000 kg (2026) — **a 1,365% increase** [V] |
| **Capture fisheries** | **Declining sharply.** Seabob fell from 24,800 t (2012) to **9,165 t (2021)** [V]. **⚠ MSC certification ran to 5 Feb 2025 — renewal unconfirmed** |
| **Poultry** | Guyana imports **>52 million hatching eggs** annually [V]. **[I] The gap is the opportunity** |
| **Livestock** | **Guyana is certified free of foot-and-mouth disease** — materially improves export access [V] |

**⚠ Correcting a common assumption: "25 by 2025" was not achieved.** The CARICOM target to cut the
region's food import bill by 25% has been **formally extended to 2030**. **[I] The metric shifted
from import-bill reduction to production tonnage — easier to hit and easier to subsidise. Plan around
production contracts, not import-substitution rhetoric.**

**⚠ The single most important thing to verify before an agri-export plan: CARICOM market access is
not free in practice.** A dated source indicates Trinidad permits only pineapples, pumpkins and
plantains from Guyana, with partial embargoes affecting Antigua, Barbados and Trinidad [U]. A
verified 2025 datapoint is consistent — melons and papayas to Barbados totalled only **US$425,790**.
**Confirm current SPS status with New GMC.**

**[V] Land tenure:** state land is granted by licence, permit or lease. **[I] A lease is weak
collateral for bank credit** — which is why the zero-collateral Development Bank product matters most
in agriculture.

**[V] Processing infrastructure is thin** — limited canning and drying capacity prevents processed
foods reaching markets. **[I] Stated as a constraint, but it reads as the clearest white-space
opportunity in the sector.**

### Retail and distribution

**[V] The defining competitive dynamic is Chinese-owned retail.** Local retailers say they cannot
match on pricing or range, citing direct factory access in China. **Government has ruled out banning
Chinese businesses**, requiring instead that they pay taxes and abide by selling rules. The policy
response is capital access, not protection. Local casualties are real.

**[I] Strategic read: do not advise a client to compete on price in undifferentiated dry goods. The
defensible positions are perishables and fresh-chain quality, credit and relationship retail,
delivery and service, specialty and halal lines, and B2B distribution into hospitality and the oil
sector — none of which the low-cost import model serves well.**

**[V] Consumer demand is genuinely expanding.** Giftland Mall (~200,000 sq ft), Royal International,
MovieTowne. **78 fast-food restaurants** as of April 2026, up 11.27% from 2023 [U]. Three additional
Starbucks cafés announced July 2026. trade.gov notes explicit unmet demand for **halal menus, spicier
flavours and healthy fast-casual.**

### Construction

**[V] The housing pipeline is the most bankable SME demand signal in Guyana:**

| Metric | Figure |
|---|---|
| Budget 2026 housing programme | **G$159.1 billion** |
| 2026 target: house lots | **15,000+** |
| 2025 actual: lots allocated | **13,000** |
| **2025 actual: homes built by state** | **~570** |
| Cumulative lots since 2020 | **53,000+** |

**[I] Note the gap that matters most: 13,000 lots allocated in 2025 but only ~570 homes built by the
state. The overwhelming majority of construction on those lots is owner-driven, executed by small
contractors and tradespeople. That — not the government contract — is the SME market.**

**[V] Skilled trades shortage:** ILO projects demand for **8,905 construction workers over five
years**. **[I] A trade-skills training business, a labour-supply agency, or a trades business that
invests in apprenticeships is arguably a better risk-adjusted bet than a contracting firm competing
for the same scarce workers.**

**[V] There is a formal route into public work for small contractors.** NPTAB runs an annual
**National Registration Process for works below G$15,000,000** via the Bidders Registry. Key rules:
contractors qualifying above G$15m must not register in the below-15m category; **sub-contracting is
strictly prohibited**; bidders must declare other businesses registered in their own or immediate
family members' names, with false declaration causing disqualification.

**[U] Materials:** lumber ~G$110,000/ton, stone ~G$17,500/ton, cement ~G$48,000/ton (developer blog —
directional only). **[V]** Cement shortages have been persistent.

### Tourism and hospitality

**[V] Arrivals are strong:** Jan–Jul 2025 **242,655, +18%**; by October 2025 arrivals had already
exceeded full-year 2024. Source markets: **US 41%, Caribbean 31%, Canada 7%, Latin America 7%,
Europe 6%**.

**[I] Crucial interpretive point: with 41% US and 31% Caribbean in an oil economy, a large share of
these "visitor arrivals" is business travel and diaspora VFR, not leisure tourism. Arrival counts
should not be read as leisure-market size. Business travel is Georgetown-concentrated, weekday-skewed
and price-insensitive — a fundamentally different business from eco-lodges.**

**[V] Hotel supply is expanding fast** — ~400 rooms added in 2024; **1,000+ additional rooms**
announced via Courtyard by Marriott, Four Points by Sheraton and AC Marriott [U on whether these
opened on schedule]; Hilton dual-brand slated for 2027; Pegasus completed a US$100m expansion.

**[I] The SME opportunity is not to build hotels — that market is being taken by international
capital. It is the supply chain into them: laundry, F&B supply, landscaping, housekeeping
contracting, uniforms, maintenance, tour packaging, transport.**

**[V] Short-term rentals:** Georgetown had **242 active Airbnb listings** (Aug 2024–Jul 2025), 93.4%
entire home/apartment, from ~US$70/night, many marketing "5 minutes from Oil and Gas Head Offices."
**[I] 242 listings in a capital absorbing a 1,000-room branded hotel wave is a thin STR market. The
margin is in corporate extended-stay — monthly furnished rentals for oil-sector contractors — which
is far less exposed to new hotel supply than nightly leisure rentals.**

### Transport

**[U]** ~19 minibus routes, mostly starting in or contained within Georgetown; fares G$200–400 in the
city, G$1,000–1,500 Georgetown–Linden; **cash only, no national transport card**.

**[V] Fares are regulated and enforcement is active.** In May 2026 government warned operators that
**no fare increases had been approved** for minibuses, hire cars, taxis, speedboats or airport taxis,
and that all operators must display approved fare structures.

**[I] This is a material constraint. A minibus or taxi SME faces cost inflation — fuel, parts, driver
wages in a labour-short market — against administratively fixed revenue. Margins are squeezed from
both ends. Advise caution.**

**[V] Ride-hailing:** **Book-A-Ride** and **LINK** operate in Georgetown. **Uber and Bolt are absent
from Guyana.** **[I] An open field with no global incumbent, in a city with rising incomes and poor
formal transit, is genuinely attractive — but it is fair to assume the global players' absence
reflects market-size and payments-infrastructure judgments rather than oversight.**

**[V] Oil-sector logistics:** **Vreed-en-Hoop Shorebase (VEHSI)** opened January 2025 — ~40 acres,
US$260–300m, a JV between Guyanese NRG Holdings and Jan De Nul, described as "the biggest local
content win to date."

### ICT services — the sector where narrative and evidence diverge most

**[V] Government targets:** originally 10,000 BPO jobs by 2025, revised **up to 15,000**; a broader
**25,000 ICT jobs within five years**; **G$2 billion+** allocated for ready-made call centre
facilities.

**[V] The actual trajectory:**
- **itel CX closed its Guyana operations — 400+ job losses**
- **Midas BPO ceased operations**
- **Teleperformance** closed a location, citing "lateness and absenteeism"
- itel's stated reason: **rising cost of doing business**, making it hard to find and retain
  qualified candidates
- **Qualfon** remains

**[I] My assessment: the low-cost labour arbitrage that built Guyana's BPO sector has been destroyed
by the oil boom itself. Oil-driven wage inflation removed the cost advantage; 6.8% unemployment
removed the labour surplus. An SME should not enter voice BPO. The 15,000-job target is not supported
by evidence, and G$2bn of purpose-built call-centre space is at risk of being stranded.
Higher-value, lower-headcount services — specialised back office, finance and accounting, technical
support — are the only defensible niche.**

**⚠ A warning about sources.** Searches for Guyanese software companies returned directory pages
naming firms with specific products and client claims that **could not be corroborated through any
independent source**, from sites showing clear hallmarks of AI-generated SEO filler. **No reliable
picture of Guyana's indigenous software industry or freelancing volumes could be established.**
**[I] A sector with real scale usually leaves a verifiable trail; its absence is itself informative.**

### Personal services

**⚠ The weakest-evidenced section, deliberately so.** Barbering, salons, cleaning, events and
childcare are overwhelmingly informal micro-enterprise, and **no official Guyanese statistics on
their size, employment or revenue surfaced.**

**[V] Food vending and food service — regulated, and enforced.** Anyone handling food commercially,
**including street vendors**, needs a **Food Handler's Certificate** from the Public Health
Department, **valid one year**. All eating houses, restaurants, provision stores and cold storages
must register with the **Food and Hygiene section of the Georgetown M&CC**, which conducts regular
inspections. **[V, 2018]** Certificate cost G$5,000 — current fee unverified.

**[V] Security services — the most formalised segment.** Firms must be approved by the **Private
Investigators and Security Guards Licensing and Advisory Board**. Established players include
**Amalgamated Security Services (Guyana)** holding ISO 9001, ISO 18788 and PSC-1.

**[I] Security has the clearest demand drivers of any personal-services segment — oil facilities,
hotel construction, mall retail, high-value residential, and praedial larceny in agriculture. It is
also a Local Content Act candidate (95% floor). But Amalgamated's certification shows the bar
international clients set; an SME without it is confined to the domestic low-margin end.**

**[V] Pharmacy — a clean, actionable checklist.** Requires: **Fire Certificate** (Guyana Fire
Service), **Sanitary Certificate** (M&CC or RDC), updated **Business Registration**, **Drug
Certificate** (Poison Control Board, MoH), and a **Licensed Pharmacist Certificate**.

**[I] Barbering, salons, cleaning, events, childcare — no verified data.** What can be reasoned from
verified facts elsewhere: a population that has just crossed 1 million with 42% under 25,
unemployment at 6.8%, and rising disposable income is demographically favourable for grooming, beauty
and events; commercial cleaning demand should track the verified hotel and mall build-out.
**These are structural inferences, not measurements. Anyone acting on them should do primary local
market research.**

---

## 8. Cross-cutting judgements

**Where the evidence points strongest, for an SME:**
1. **Agro-processing** — zero corporate tax from Budget 2026, G$745m of state infrastructure, and an
   official acknowledgement that processing capacity is the binding constraint
2. **Brackish-water shrimp / aquaculture** — 1,365% growth off a small base, targets met
3. **Construction trades and trade-skills training** — 8,905-worker gap, 15,000 lots/year,
   overwhelmingly owner-driven building
4. **Oil-sector supply services under the Local Content Act** — 40 ring-fenced areas, free
   certification (see `guyana-finance-ecosystem.md` §8)
5. **Security services** — formalised, certifiable, with demand from every other sector on this list
6. **Social-commerce retail** — Facebook + WhatsApp + MMG + courier is a near-zero-capex stack
   matching actual customer behaviour

**Where to counsel caution:**
1. **Voice BPO** — three operator exits, wage arbitrage destroyed
2. **Undifferentiated retail** — structural cost disadvantage against Chinese-owned operators;
   government has explicitly ruled out protection
3. **Minibus/taxi operation** — administratively fixed fares against free-floating costs
4. **Sugar-adjacent ventures** — 30% labour turnout, missed targets, active restructuring threat
5. **Capture fisheries** — production down ~85% from the 2012 peak; MSC status unconfirmed
6. **Any plan assuming cheaper electricity before 2028**

**Three counter-intuitive findings worth carrying into client conversations:**
- **A generator is insurance, not savings.** At G$168/L diesel, fuel alone (~G$59/kWh) exceeds GPL's
  commercial tariff of G$56.38/kWh. The VAT exemption on renewables makes solar-plus-battery the
  better economic hedge
- **Registration cost is not the barrier to formalisation** (~US$36 all-in). Compliance burden and
  the ongoing advantage of invisibility are
- **Undercapitalisation was not confirmed as a survival determinant** by the one Guyana-specific SME
  survival study — credit *access* and collateral were

---

## 9. Verify before committing money

**High priority:**
1. **Current SPS/embargo status for Guyanese produce into Trinidad, Barbados and Antigua** (New GMC)
   — make-or-break for any agri-export plan
2. **Customs broker service fees** — only GRA statutory fees are published; get three written quotes
3. **Merchant discount rates** from Republic Bank and GBTI, and **MMG's merchant fee schedule**
4. **Whether the private-sector minimum wage remains G$60,147** — a motion to raise it to G$100,000
   was live in December 2025
5. **GWI's official tariff schedule** — the pricing page was unreachable
6. **One Communications and Digicel business internet pricing**

**Secondary:** commercial rents outside Georgetown · Georgetown→Lethem trucking rates and domestic air
cargo tariffs · whether MSC certification for Guyana seabob was renewed past 5 Feb 2025 · whether the
announced Marriott/Sheraton rooms actually opened · Lethem–Bonfim border procedures and tariff
treatment · bonded warehouse application procedure and fees.

**Known data that simply does not exist publicly:** Guyanese bank account ownership and digital
payment usage (Guyana is not covered by World Bank Findex) · an official occupational wage survey ·
credit union sector SME lending volumes · bribery incidence · family business prevalence and
succession outcomes · security spend as a share of SME costs · Guyana-specific praedial larceny loss
quantification · indigenous software industry scale.
