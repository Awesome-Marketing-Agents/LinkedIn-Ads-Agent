# LinkedIn API Feasibility Analysis
## What Can (and Can't) You Build for the LinkedIn Ads Action Center

*Analysis Date: February 2026*

---

## TL;DR — The Verdict

**You can build ~75% of the Action Center with LinkedIn's official APIs.** The core loop — monitor performance → detect problems → recommend actions → execute changes — is fully supported. The remaining ~25% (mainly competitive intelligence, some creative asset management, and certain audience features) requires workarounds, third-party tools, or LinkedIn Marketing Partner status.

The biggest risk isn't technical capability — it's **access gating**. LinkedIn has a tiered permission system, and some of your most powerful features require private API access that only approved partners get.

---

## How LinkedIn API Access Actually Works

Before mapping APIs to your agents, you need to understand the access hierarchy — because this determines your entire build sequence.

### The Access Ladder

```
Level 1: Development Tier (anyone can get)
   └─ POST to 5 ad accounts, GET unlimited
   └─ Core campaign management + analytics
   └─ Good enough to build + test your MVP

Level 2: Standard Tier (apply after building on Dev)
   └─ No limit on ad accounts
   └─ Required if you want to serve multiple customers
   └─ LinkedIn reviews your app before granting

Level 3: Private APIs (invitation / application only)
   └─ Matched Audiences (DMP Segments)
   └─ Audience Insights
   └─ Media Planning
   └─ Requires "strong partnership fit"

Level 4: LinkedIn Marketing Partner (the golden ticket)
   └─ Higher rate limits
   └─ Co-marketing opportunities
   └─ Deeper API access
   └─ Metadata and Factors.ai are at this level
```

**What this means for you:** You can build and test your entire MVP on Development Tier with real ad accounts. But to ship a multi-customer product, you need Standard Tier. And for the most powerful features (audience syncing, predictive audiences), you need Private API access.

### Key API Products Available

| API Product | What It Does | Access Level | Relevance to Action Center |
|---|---|---|---|
| **Advertising API** | Create/manage campaigns, campaign groups, creatives, bidding | Dev → Standard | **CRITICAL** — core execution engine |
| **Ad Analytics API** | Performance metrics at account/campaign/creative level | Dev → Standard | **CRITICAL** — powers Performance Monitor Agent |
| **Conversions API** | Server-side conversion tracking, CRM attribution | Separate application | **HIGH** — enables true ROI measurement |
| **Lead Sync API** | Pull lead gen form submissions to CRM | Separate application | **HIGH** — lead quality review |
| **Matched Audiences API** | DMP segments, retargeting, list uploads | **Private** (requires approval) | **HIGH** — powers Audience Intelligence Agent |
| **Audience Insights API** | Audience composition, interests, content engagement | **Private** (requires approval) | **MEDIUM** — enriches audience recommendations |
| **Media Planning API** | Campaign forecasting against objectives | **Private** (requires approval) | **MEDIUM** — scenario modeling |
| **Community Management API** | Company page posts, engagement, brand mentions | Dev → Standard | **LOW** — organic, not paid |
| **Ad Budget Pricing API** | Suggested bids based on targeting criteria | Dev → Standard | **HIGH** — powers bid optimization |

---

## Agent-by-Agent Feasibility Breakdown

### Agent 1: Performance Monitor Agent — ✅ FULLY BUILDABLE

This is your most API-supported agent. LinkedIn's Ad Analytics API (`/adAnalytics`) is comprehensive.

**What the API gives you:**

- **Metrics at every level** — account, campaign group, campaign, and creative
- **Time granularity** — daily, monthly, or lifetime
- **Pivots** — slice data by creative, campaign, company, member demographics (job title, industry, seniority, company size, country)
- **Core metrics available:**
  - Impressions, clicks, CTR
  - Spend, CPC, CPM
  - Conversions (with attribution windows)
  - Lead form opens, leads (oneClickLeads)
  - Engagement metrics (likes, comments, shares, follows)
  - Video metrics (views, completions, watch time — new in 2026!)
  - Event metrics (views, watch time — new in 2026!)
  - Dwell time (how long ad is visible in viewport)
  - Frequency (via impressions / reach calculation)
  - **Revenue Attribution Metrics** (new in 202505!) — CRM leads, pipeline value, revenue for connected CRM accounts
- **Demographic pivots** — see performance broken down by job function, seniority, industry, company size, geography
- **Budget pricing** — `/adBudgetPricing` gives suggested/min/max bids based on targeting criteria

**What you can build with this:**

| Action Center Feature | How to Build It | Confidence |
|---|---|---|
| CTR monitoring + alerting | Poll `/adAnalytics` every few hours, compare CTR against thresholds | ✅ High |
| CPL tracking | Calculate from spend / conversions metrics | ✅ High |
| Spend pacing alerts | Compare daily spend against budget from campaign object | ✅ High |
| Creative fatigue detection | Track CTR decay curves per creative over time, predict fatigue from historical patterns | ✅ High |
| Anomaly detection (spend spikes, CTR drops) | Time-series analysis on daily metrics | ✅ High |
| Frequency monitoring | Impressions vs. unique reach (limited — LinkedIn doesn't expose exact reach per creative natively) | ⚠️ Medium |
| Revenue attribution | New `attributedRevenueMetrics` finder for accounts with connected CRM (Salesforce, HubSpot, Dynamics 365) | ✅ High |
| Demographic performance breakdown | Pivot by job function, seniority, industry etc. | ✅ High |

**Rate limit consideration:** LinkedIn limits data to 45 million metric values per 5-minute window across all queries. For a typical account with 10-20 campaigns and 50-100 creatives, you're well within limits polling every few hours. At scale (hundreds of customer accounts), you'll need to stagger polling intelligently.

**Concrete example — detecting creative fatigue:**
```
Day 1:  Creative A → CTR 1.42%
Day 7:  Creative A → CTR 1.31%  (−7.7%)
Day 14: Creative A → CTR 1.12%  (−21.1%)
Day 21: Creative A → CTR 0.89%  (−37.3%)  ← FATIGUE ALERT

Your agent would: 
1. Poll /adAnalytics daily with pivot=CREATIVE
2. Store CTR time series per creative
3. Fit a decay model (exponential or linear)
4. Alert when predicted CTR crosses a threshold (e.g., 25% decline from peak)
5. Trigger Creative Agent to generate replacements
```

---

### Agent 2: Optimization Agent — ✅ FULLY BUILDABLE

This agent recommends and executes pause/scale/bid changes. The Advertising API gives you full campaign management CRUD.

**What the API gives you:**

- **Campaign management** — Create, read, update campaigns via `/adCampaigns`
  - Change `status` (ACTIVE, PAUSED, ARCHIVED)
  - Update `dailyBudget` and `totalBudget`
  - Modify `bidAmount`, `bidStrategy` (manual CPC, maximum delivery, target cost)
  - Update `runSchedule` (start/end dates)
  - Modify `targetingCriteria`
- **Campaign Group management** — `/adCampaignGroups` for budget/status across groups
- **Creative management** — `/adCreatives` to pause/activate individual ads
- **A/B test setup** — Create multiple campaign variants with different parameters

**What you can build:**

| Action Center Feature | How | Confidence |
|---|---|---|
| "Pause Ad 3 in Campaign B" | PATCH campaign status to PAUSED | ✅ High |
| "Reallocate $500/week to Campaign A" | PATCH dailyBudget on target campaign | ✅ High |
| "Increase bid from $12 to $15 CPC" | PATCH bidAmount on campaign | ✅ High |
| "Switch from Maximum Delivery to Manual CPC" | PATCH bidStrategy | ✅ High |
| "Turn off LinkedIn Audience Network" | PATCH campaign targeting to exclude LAN placements | ✅ High |
| "Turn off Audience Expansion" | PATCH `enabledAudienceExpansion` flag on campaign | ✅ High |
| "Launch A/B test with 2 variants" | POST two campaigns with identical targeting, different variables | ✅ High |
| Budget reallocation across campaigns | Combination of PATCH calls adjusting multiple budgets | ✅ High |

**This is where your "default settings audit" becomes killer.** On onboarding, you can:
1. GET all campaigns for the account
2. Check each campaign for: `enabledAudienceExpansion`, LAN placement settings, `bidStrategy` (is it maximum delivery?), audience size (too broad? too narrow?)
3. Present findings: "We found 4 campaigns with Audience Expansion on, 3 using Maximum Delivery bidding, and 2 running on LinkedIn Audience Network. Estimated waste: $X/month."
4. User clicks [Fix All] → PATCH calls execute the changes

---

### Agent 3: Audience Intelligence Agent — ⚠️ PARTIALLY BUILDABLE

This is where LinkedIn's access gating starts to bite.

**What's available at Development/Standard tier:**

- **Targeting facets discovery** — `/adTargetingFacets` lists all available targeting dimensions (job titles, industries, locations, seniorities, company sizes, etc.)
- **Targeting entities** — `/adTargetingEntities` looks up specific values within facets
- **Audience size estimation** — `/audienceCounts` takes targeting criteria and returns estimated audience size
- **Campaign targeting CRUD** — Set/modify targeting on campaigns
- **Exclusion lists** — Exclude audiences (converted leads, specific companies) via targeting criteria

**What requires Private API access (Matched Audiences):**

- **DMP Segment creation** — Upload company lists or email lists to create custom audiences
- **DMP Segment management** — Add/remove users from segments
- **Website retargeting segments** — Create audiences from website visitor behavior
- **Predictive Audiences** — LinkedIn's ML-generated lookalike audiences
- **Ad Segments** — Engagement-based retargeting (video viewers, lead form openers)

**What you can build:**

| Feature | Access Level | Confidence |
|---|---|---|
| Translate ICP → LinkedIn targeting parameters | Dev/Standard | ✅ High |
| Estimate audience sizes and flag too narrow/broad | Dev/Standard | ✅ High |
| Build segment variations for testing | Dev/Standard | ✅ High |
| Set exclusions on campaigns (exclude converters) | Dev/Standard | ✅ High |
| Upload company lists for ABM targeting | **Private** (Matched Audiences) | ⚠️ Requires approval |
| Build retargeting from website visitors | **Private** (Matched Audiences) | ⚠️ Requires approval |
| Create engagement retargeting (video viewers, form openers) | **Private** (Matched Audiences) | ⚠️ Requires approval |
| Sync CRM segments to LinkedIn | **Private** (Matched Audiences) | ⚠️ Requires approval |
| Audience composition insights | **Private** (Audience Insights) | ⚠️ Requires approval |

**Practical implication:** Your MVP audience agent can do ICP → targeting translation, audience sizing, and segment optimization using Dev/Standard tier. But the really powerful stuff (retargeting management, CRM audience sync, engagement-based segments) needs Private API access. This is a strong reason to pursue LinkedIn Marketing Partner status early.

---

### Agent 4: Creative Agent — ⚠️ PARTIAL (API for deployment, AI for generation)

The Creative Agent has two jobs: (1) generate ad copy, and (2) deploy it. LinkedIn's API handles deployment but not generation (obviously).

**What the API gives you:**

- **Creative CRUD** — `/adCreatives` supports creating, reading, updating, and pausing creatives
- **Supported ad types via API:**
  - Single image ads (Sponsored Content)
  - Video ads
  - Carousel ads
  - Document ads
  - Text ads
  - Spotlight/Follower dynamic ads
  - Connected TV ads (new — via VAST tags)
  - Message ads / Conversation ads
- **Creative specs** — LinkedIn enforces character limits (headline ≤200 chars, intro text ≤600 chars for optimal display, CTA options)
- **Image/video upload** — Upload assets via the Assets API, then reference in creative

**What you can build:**

| Feature | How | Confidence |
|---|---|---|
| AI generates ad copy variants | LLM generates copy using brand voice + ICP + messaging pillars (NOT a LinkedIn API feature) | ✅ High (your AI, not LinkedIn's) |
| Deploy new creatives to LinkedIn | POST to `/adCreatives` with copy + asset references | ✅ High |
| Pause fatigued creatives | PATCH creative status | ✅ High |
| A/B test new copy against existing | Create new creatives in same campaign, compare via analytics | ✅ High |
| Upload creative assets (images) | POST to Assets API | ✅ High |
| Format copy to LinkedIn specs | Validate character counts against limits before submission | ✅ High |
| Carousel ad creation | POST multi-card creative | ✅ High |

**Key limitation:** LinkedIn's API does NOT provide a way to preview how an ad will render before publishing. You'd need to build your own preview component that mimics LinkedIn's ad format display. This is a UX concern, not a blocker.

**The creative refresh workflow is 100% buildable:**
```
1. Performance Monitor detects CTR decay on Creative A
2. Orchestrator triggers Creative Agent
3. Creative Agent (your LLM):
   - Pulls brand voice guidelines from your DB
   - Pulls messaging pillars
   - Pulls top-performing copy patterns from past analytics
   - Generates 3-5 variants with testing hypotheses
4. Human reviews on dashboard → clicks [Execute]
5. Creative Agent:
   - Uploads any new image assets via Assets API
   - POST new creatives to /adCreatives 
   - PATCHes old creative to PAUSED
6. Performance Monitor starts tracking new creatives
```

---

### Agent 5: Competitive Intelligence Agent — ❌ NOT NATIVELY BUILDABLE (but workarounds exist)

This is the biggest gap. LinkedIn does NOT offer an official API for the Ad Library.

**What's available:**

- LinkedIn's Ad Library is a **public web interface** at `linkedin.com/ad-library` — you can search by advertiser name, keyword, country, and date range
- LinkedIn does NOT provide an official programmatic API to query the Ad Library
- Third-party scraping services exist (SearchAPI, Apify scrapers) that provide structured JSON from the Ad Library, but these are:
  - **Unofficial** — they scrape the web interface
  - **Against LinkedIn's TOS** if used at scale via automated scraping
  - **Fragile** — can break when LinkedIn changes their frontend
  - **Potentially risky** for your LinkedIn Marketing Partner application

**Workaround options:**

| Approach | Pros | Cons | Risk Level |
|---|---|---|---|
| **Third-party Ad Library API** (SearchAPI.io, Apify) | Structured JSON, easy to integrate, near real-time | Unofficial, may violate TOS, costs money, fragile | ⚠️ Medium |
| **Build your own lightweight scraper** | Full control, customizable | Violates TOS, maintenance burden, can get blocked | ❌ High |
| **Manual monitoring + human input** | Fully compliant, zero risk | Doesn't scale, defeats the purpose | ✅ Low (but useless at scale) |
| **Partner with a competitive intelligence provider** (e.g., Pathmatics, Moat) | Compliant, professional data | Expensive, adds dependency, may not cover LinkedIn deeply | ✅ Low |
| **Wait for official API** | Fully supported when available | May never happen, or may be very restricted | ✅ Low |

**Recommendation:** For MVP, use a third-party service like SearchAPI.io (they charge per request, offer structured JSON, and handle the scraping). Position this as "competitive insights" powered by the LinkedIn Ad Library. Once you have LinkedIn Marketing Partner status, explore whether official access becomes available. The DSA (Digital Services Act) requires LinkedIn to provide this transparency data, so an official API may come eventually.

---

### Agent 6: Reporting Agent — ✅ FULLY BUILDABLE

The Ad Analytics API gives you everything you need for comprehensive reporting.

**What you can build:**

| Report Type | Data Source | Confidence |
|---|---|---|
| Weekly performance summary | `/adAnalytics` with weekly date range | ✅ High |
| Campaign comparison report | Analytics with pivot=CAMPAIGN | ✅ High |
| Creative performance ranking | Analytics with pivot=CREATIVE | ✅ High |
| Demographic breakdown (who's clicking) | Analytics with demographic pivots (job function, seniority, industry) | ✅ High |
| Company-level engagement (which companies saw your ads) | Analytics with pivot=MEMBER_COMPANY | ✅ High |
| Funnel metrics (impression → click → lead → MQL) | Analytics + CRM data via Conversions API | ✅ High |
| Revenue attribution | `attributedRevenueMetrics` finder (new 2025, requires CRM connection) | ✅ High |
| Spend efficiency trends | Time-series analysis on spend/conversion metrics | ✅ High |
| Benchmark comparison | Your analytics vs. industry benchmarks (you build the benchmark DB) | ✅ High |
| Budget waste quantification | Compare actual vs. optimal based on LAN/expansion/bidding analysis | ✅ High |

**The "Budget Waste Calculator" is especially powerful:**
```
Your reporting agent can calculate:

1. LAN Waste: Compare CTR/CPL on LAN vs. LinkedIn feed placements
   (using demographic pivots to approximate placement data)

2. Audience Expansion Waste: Compare performance of campaigns 
   with expansion on vs. off

3. Creative Fatigue Waste: Calculate spend on creatives past 
   their fatigue threshold

4. Bidding Waste: Compare Maximum Delivery cost vs. estimated 
   Manual CPC cost using /adBudgetPricing

5. Audience Overlap Waste: Identify campaigns targeting similar 
   audiences (cannibalizing each other)

Output: "This month you wasted $2,847:
  - Fatigued creatives: $1,200
  - LAN leakage: $667  
  - Overbidding: $580
  - Audience overlap: $400"
```

---

### Agent 7: Orchestrator Agent — ✅ FULLY BUILDABLE (your code, not LinkedIn's API)

The Orchestrator is entirely your logic layer. It sits above all other agents, synthesizes their signals, and generates the "3 plays this week" dashboard.

This is NOT dependent on any specific LinkedIn API — it's dependent on the **outputs** of your other agents. It's your AI model + business logic that:

1. Ranks opportunities by impact (estimated budget saved or leads gained)
2. Determines which execution agents to fire and in what sequence
3. Generates human-readable play descriptions
4. Packages each play with a ready-to-execute action plan

**This is your moat.** As the competitor analysis says — this orchestration intelligence is what nobody has built. The API capabilities are the same for everyone. Your differentiation is in the "brain" that connects the signals.

---

## The UTM / Tracking Gap

Your project doc mentions UTM generation and tracking setup. Here's the reality:

- LinkedIn's API supports **Dynamic UTM parameters** (new feature) — campaigns can auto-append UTMs with campaign name, creative ID, etc.
- You can set UTM parameters when creating campaigns via the API
- LinkedIn's **Conversions API** (CAPI) enables server-side conversion tracking — this is the gold standard for attribution because it doesn't depend on browser cookies

**What you can build:**
- Auto-generate UTM naming conventions across all campaigns
- Set up Conversions API integration for server-side tracking
- Map conversions back to specific campaigns/creatives/audiences
- With CRM integration, calculate true cost-per-meeting and cost-per-pipeline

---

## What You CANNOT Build (Hard Limits)

| Feature | Why Not | Workaround |
|---|---|---|
| **Real-time data streaming** | LinkedIn doesn't offer webhooks or push notifications for ad data; you must poll | Poll every 2-4 hours; most advertisers don't need real-time for campaign decisions |
| **Official competitor ad monitoring API** | No API for the Ad Library | Third-party scrapers or manual process |
| **Member-level data** | Privacy laws + LinkedIn policy prevent access to individual member data from ads | Use demographic aggregates (job function, seniority, industry) instead |
| **Cross-platform data** | LinkedIn API only returns LinkedIn data | Integrate separately with Meta, Google APIs for multi-channel view |
| **Creative rendering preview** | No API endpoint to render how an ad will look | Build your own preview component matching LinkedIn's ad formats |
| **Organic content analytics via Marketing API** | Marketing API focuses on paid; organic uses Community Management API | Use Community Management API separately (different permissions) |
| **Automated A/B test statistical analysis** | LinkedIn provides raw data, not statistical significance calculations | Build your own stats engine (Bayesian or frequentist) on top of analytics data |

---

## Build Sequencing Recommendation

Based on API access tiers and feature dependencies, here's the optimal build order:

### Phase 1: MVP (Development Tier — start now)
*Everything here works with basic API access for up to 5 ad accounts*

1. **Performance Monitor Agent** — poll analytics, detect anomalies, track CTR decay
2. **Default Settings Audit** — scan campaigns for LAN, Audience Expansion, Maximum Delivery
3. **Optimization Agent** — pause/scale/bid recommendations with one-click execution
4. **Reporting Agent** — weekly performance summaries + waste quantification
5. **Basic Orchestrator** — synthesize signals from above into "plays this week"

**Why this order:** These features deliver instant, quantifiable value (the "aha moment") and require only Dev Tier access. You can onboard beta users immediately.

### Phase 2: Creative Engine (Development Tier + your AI)

6. **Creative Agent** — LLM-powered copy generation + creative deployment via API
7. **Fatigue → Refresh workflow** — connect Performance Monitor's fatigue detection to Creative Agent
8. **A/B test framework** — automated test design with statistical rigor

### Phase 3: Audience Power (Requires Standard + Private API applications)

9. Apply for **Standard Tier** (you'll need this before serving multiple customers)
10. Apply for **Matched Audiences Private API** (retargeting, DMP segments, CRM sync)
11. Apply for **Conversions API** (server-side tracking)
12. **Audience Intelligence Agent** — CRM sync, retargeting management, segment optimization

### Phase 4: Competitive Intelligence (Third-party integration)

13. **Competitive Intelligence Agent** — integrate third-party Ad Library data
14. Competitor messaging tracking over time
15. Competitive opportunity alerts

### Phase 5: LinkedIn Marketing Partner Application

16. With traction (customers, case studies), apply for **LinkedIn Marketing Partner** status
17. Higher rate limits, co-marketing, deeper access

---

## Rate Limits & Operational Constraints

| Constraint | Detail | Impact on Action Center |
|---|---|---|
| **Rate limits not published** | Vary by endpoint and access level; check Developer Portal analytics | Must build adaptive polling that respects limits |
| **45M metric values / 5-min window** | Analytics data cap | Fine for single accounts; need staggering at scale (100+ customers) |
| **429 Too Many Requests** | Standard throttling response | Implement exponential backoff + request queuing |
| **API versions sunset monthly** | Must migrate to latest version regularly | Budget engineering time for version upgrades |
| **OAuth token refresh** | Tokens expire; need refresh flow | Standard OAuth implementation |
| **Data storage restrictions** | LinkedIn TOS requires you can identify, segregate, and selectively delete stored data | Architecture must support per-customer data isolation + deletion |

---

## Cost Structure

The LinkedIn Marketing API itself is **free to access** — no per-call charges. Your costs are:

1. **Engineering time** — building and maintaining the integration
2. **Infrastructure** — servers, databases, AI compute for LLM agents
3. **LinkedIn ad spend** — your customers still pay LinkedIn for actual ad delivery
4. **Third-party tools** — if using Ad Library scraping services ($50-200/month depending on volume)
5. **LinkedIn Partnership** — if you reach Partner tier, there may be commercial terms (not publicly documented)

---

## Key Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **Private API access denied** | High | Build MVP on public APIs first; demonstrate traction before applying. Matched Audiences is the biggest loss — workaround is to guide users to set up retargeting in Campaign Manager manually while your tool handles everything else. |
| **LinkedIn builds native "Action Center"** | Medium | Their Recommendations tab is primitive. Incentive misalignment (they optimize for their revenue) limits how good it can get. Your independence is a feature. |
| **Rate limits throttle your polling** | Medium | Implement smart caching, staggered polling, and request budgeting. Partner status increases limits. |
| **API version deprecation** | Low-Medium | Budget 2-4 weeks/year for version migrations. LinkedIn sunsets old versions ~6 months after new release. |
| **TOS violation (competitive intelligence)** | Medium | Use third-party services (SearchAPI) rather than scraping directly. Position as "industry transparency data" not "scraping." |

---

## Self-Check Questions

Test your understanding of the API landscape:

**Question 1:** You want to build the "default settings audit" feature. A customer connects their account and you want to check if Audience Expansion is enabled on their campaigns. What API endpoint do you use, and what access tier do you need?

**Question 2:** Your Performance Monitor detects that Creative A has dropped 35% in CTR over 3 weeks. The Orchestrator generates a "Creative Refresh" play. Walk through the exact sequence of API calls needed to: (a) pause the old creative, (b) deploy a new one, and (c) start tracking the new one's performance.

**Question 3:** You want to build the "Budget Waste Calculator" that shows "$2,847 wasted this month." For the "LAN leakage" component, what data would you pull from the API, and what's the limitation you'd face?

**Question 4:** A customer asks "which companies are seeing my ads?" Can you answer this from the API? What privacy limitations exist?

**Question 5:** Why does the Matched Audiences API being "Private" matter more than you might initially think? What specific Action Center features become impossible without it?

*(Answers follow — try working through them first)*

---

### Answers

**A1:** GET `/adCampaigns` for the ad account — each campaign object includes `enabledAudienceExpansion` (boolean), `bidStrategy`, targeting criteria, and placement settings. This works on **Development Tier**. You'd iterate over all campaigns and flag the problematic settings.

**A2:** The sequence is:
1. PATCH `/adCreatives/{creative_id}` → set `status: PAUSED` on old creative
2. (If new image needed) POST to Assets API to upload the image asset
3. POST `/adCreatives` with the new copy, asset reference, and `status: ACTIVE` within the same campaign
4. The new creative automatically starts delivering. Poll `/adAnalytics` with `pivot=CREATIVE` to track it.
No special permissions needed beyond Dev Tier.

**A3:** This is tricky. LinkedIn's Analytics API doesn't have a direct "LAN vs. LinkedIn Feed" placement breakdown as a standard pivot. You'd need to infer it from campaign settings (is LAN enabled?) and potentially compare performance of LAN-enabled vs. LAN-disabled campaigns. The limitation: you can't get per-impression placement data (this impression was on LinkedIn vs. this one was on an audience network site). You'd estimate based on industry benchmarks (typically 20-30% of spend goes to LAN when enabled) and then calculate: "If LAN is enabled and your CPL is $45 on this campaign vs. $28 on your non-LAN campaigns, the delta suggests ~$667/month in LAN waste."

**A4:** Yes — use the `/adAnalytics` endpoint with `pivot=MEMBER_COMPANY`. This returns company-name-level data showing which companies saw your ads, along with impression/click/engagement metrics. **Privacy limitation:** LinkedIn approximates data at granular levels to protect member privacy. You get company names, not individual member names. Also, the results may include companies NOT in your targeting (due to members working at multiple companies, job changes, or audience expansion).

**A5:** Without Matched Audiences, you lose:
- **Retargeting audience management** (Task 22 in your doc) — can't programmatically create/update retargeting segments from website visitors or engagement
- **CRM audience sync** — can't upload company or contact lists as targeting segments
- **Exclusion list automation** — can't auto-exclude converted leads at the audience level (you can exclude at campaign targeting level, but that's less powerful)
- **Engagement retargeting** — can't create audiences of "people who watched 50% of our video" or "people who opened the lead form but didn't submit"
This means your Audience Intelligence Agent becomes a "targeting optimizer" rather than a full "audience management engine." It's a meaningful reduction in value, especially for the retargeting management workflow that your doc identifies as "maintenance work most teams forget to do."
