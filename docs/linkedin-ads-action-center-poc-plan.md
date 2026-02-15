# LinkedIn Ads Action Center — POC/MVP Plan

## Using Glacis's Live LinkedIn Ad Account as the Testing Ground

---

## The POC Philosophy

A POC isn't about building all 7 agents. It's about proving one thing — **that an AI system can look at your LinkedIn Ads data, identify a specific problem or opportunity you didn't know about, and present a ready-to-execute fix that actually works.**

If you can demonstrate that loop once — signal → diagnosis → recommendation → execution → measurable result — you've validated the entire concept. Everything else is just scaling the number of signals and agents.

---

## The Minimum Viable Loop

### Week 1-2: Data Ingestion Layer (the "ears")

**What to build:** A script or lightweight backend that pulls data from your Glacis LinkedIn Ad account via the LinkedIn Marketing API.

**What to pull:**
- Campaign-level metrics: impressions, clicks, CTR, spend, CPL, conversions — daily for the last 90 days
- Ad-level metrics: same metrics but per individual ad creative
- Audience demographics: which job titles, industries, seniorities are actually seeing and clicking your ads
- Campaign settings: is LAN on? Audience Expansion? What bidding strategy?

**Technical approach:** LinkedIn's Marketing API (specifically the Ad Analytics API) gives you access to all of this. You'll need an OAuth token from the Glacis ad account. Python + requests library is enough. Store the data in a simple Postgres database or even a structured JSON file to start.

**The critical output:** A structured data snapshot that an LLM can reason over. Something like:

```
Campaign: "Supply Chain AI — VP Ops"
Status: Active, running 24 days
Budget: $150/day
Total Spend: $3,600
Impressions: 45,200
Clicks: 641
CTR: 1.42% (Day 1-10 avg: 1.68%, Day 15-24 avg: 0.89%)
CPL: $18.67
Active Ads: 2 (Ad A: CTR 1.61%, Ad B: CTR 0.94%)
LAN: Enabled
Audience Expansion: Enabled
Bidding: Maximum Delivery (CPM)
Audience Size: 34,000
Top Job Titles: VP Operations (23%), Director Supply Chain (18%), VP Supply Chain (12%)
```

**Why this first:** Without data, nothing else works. This is the foundation. And pulling it is a solved problem — LinkedIn's API documentation is solid.

---

### Week 2-3: The Analysis Agent (the "brain")

**What to build:** Take the structured data snapshot and feed it to Claude (or GPT-4) with a carefully crafted system prompt that acts as your Performance Monitor + Optimization Agent combined.

**The system prompt should include:**
- Industry benchmarks (0.44-0.65% average CTR, creative fatigue at 25-35% CTR decline, frequency thresholds, etc.)
- Rules for detecting problems (CTR declining week-over-week, one ad dramatically outperforming another, LAN enabled, Audience Expansion on, Maximum Delivery bidding selected)
- A structured output format for recommendations

**What the agent should produce:** A list of "plays" ranked by estimated impact. Each play has a diagnosis, a recommendation, and a specific action.

**Example output:**

```
PLAY 1: Creative Fatigue Detected [HIGH PRIORITY]
─────────────────────────────────────────────────
Diagnosis: Campaign "Supply Chain AI — VP Ops" CTR has 
declined 47% from 1.68% to 0.89% over 14 days. This 
matches the classic fatigue curve (25-35% decline 
threshold breached). Ad B (CTR 0.94%) is significantly 
underperforming Ad A (CTR 1.61%).

Estimated waste: ~$540/month at current trajectory 
(spending on declining impressions at inflated effective CPL).

Recommendation: 
1. Pause Ad B immediately (saving ~$60/day)
2. Generate 3 new ad variants to test alongside Ad A
3. Monitor for 7 days, pause any variant below 1.2% CTR

Action: [Generate New Ad Variants] [Pause Ad B]


PLAY 2: Default Settings Leak [MEDIUM PRIORITY]
─────────────────────────────────────────────────
Diagnosis: LinkedIn Audience Network (LAN) is enabled. 
Industry data shows LAN traffic quality is consistently 
low for B2B campaigns. Audience Expansion is also enabled, 
which stretches targeting beyond your defined ICP.

Estimated waste: 15-25% of impressions likely served 
outside LinkedIn feed or to non-ICP audiences (~$540-900/month).

Recommendation:
1. Disable LinkedIn Audience Network
2. Disable Audience Expansion
3. Switch from Maximum Delivery to Manual CPC bidding

Action: [Show Me the Settings to Change]


PLAY 3: Budget Reallocation Opportunity [MEDIUM PRIORITY]  
─────────────────────────────────────────────────
Diagnosis: Ad A is performing at 1.61% CTR (2.5x above 
platform average). This is a strong performer that could 
absorb more budget.

Recommendation:
1. Increase daily budget on this campaign by 20% ($30/day)
2. Reallocate from underperforming campaigns if any exist

Action: [Show Campaign Comparison]
```

**Why this approach:** You're not building a complex multi-agent system. You're feeding structured data into an LLM with expert-level context. The "agent" is really just a well-prompted API call. This is buildable in days, not weeks.

---

### Week 3-4: The Creative Agent (the "hands")

**What to build:** When Play 1 says "Generate New Ad Variants," the user clicks and a second agent fires. This one takes your existing ad copy, brand context, ICP definition, and messaging pillars as input, and generates 3-5 new ad copy variants.

**Inputs it needs:**
- Your current best-performing ad copy (pulled from the data layer)
- Your ICP (VP-level supply chain leaders at large manufacturers)
- Your messaging pillars (from the Glacis positioning work you've already done)
- LinkedIn ad specs (headline: 70 chars, body: 150 chars for single image, CTA options)
- What you're testing (different hook type? different pain point? different proof point?)

**Example output:**

```
VARIANT 1: Pain-Point Hook
Headline: "Still Managing Orders Manually in 2026?"
Body: "AI agents are automating order management for 
manufacturers. VP Supply Chain leaders are cutting 
processing time by 73%. See how."
CTA: Learn More
Testing hypothesis: Pain-point question hook vs current 
benefit-statement hook

VARIANT 2: Stat-Led Hook  
Headline: "73% Faster Order Processing with AI Agents"
Body: "Leading manufacturers are replacing manual order 
management with AI. No integration headaches. Live in 
weeks, not months."
CTA: Learn More
Testing hypothesis: Specific stat in headline vs 
question format

VARIANT 3: Social Proof Hook
Headline: "How [Industry] Leaders Automate Order Management"
Body: "The top manufacturers aren't hiring more ops 
people. They're deploying AI agents that handle 
exceptions, track shipments, and close the loop 
automatically."
CTA: Learn More
Testing hypothesis: Peer-reference hook vs direct 
benefit hook
```

**Why this matters for the POC:** This is where the "action center" becomes tangible. The user didn't go to a blank page and stare at a cursor trying to write ads. The system diagnosed the problem (fatigue), recommended the fix (new variants), and produced the solution (3 ready-to-review options). That's the full loop.

---

### Week 4-5: The Dashboard (the "face")

**What to build:** A simple web UI (React or even just a Notion-like page) that displays the plays. This doesn't need to be beautiful. It needs to be functional.

**The minimum viable dashboard has three sections:**

**Section 1: Account Health Score**
A single number (0-100) based on weighted factors: creative freshness, CTR trends, default settings, audience targeting quality, budget efficiency. Glacis might score 62/100 today.

**Section 2: This Week's Plays**
The 2-4 recommendations from the Analysis Agent, each with the diagnosis, estimated impact, and action buttons. At POC stage, the "action buttons" can just link to LinkedIn Campaign Manager with instructions. They don't need to execute via API yet.

**Section 3: Campaign Performance Timeline**
A simple chart showing CTR and CPL trends over time for each campaign. The key insight is the visual — when you SEE the fatigue curve declining, the recommendation to refresh creative becomes obvious.

**Tech stack for POC:** Could be a React artifact, a simple Next.js app, or even a Streamlit dashboard in Python. At POC stage, don't over-engineer. The insight quality matters infinitely more than the UI quality.

---

## What You're Actually Testing

The POC isn't testing "can I build 7 agents." It's testing these specific hypotheses:

| # | Hypothesis | How You Validate |
|---|-----------|-----------------|
| 1 | **Can the system detect problems I didn't know about?** | Run the analysis agent on the Glacis account. Did it find anything you hadn't already noticed? If it surfaces a real insight you missed (maybe LAN is burning budget on a campaign you forgot to check, or a creative started fatiguing 3 days ago), that's validation. |
| 2 | **Are the recommendations actually good?** | Take the plays it generates. Would you actually do these things? Are they things a smart LinkedIn Ads manager would recommend? If yes, the analysis logic works. If the recommendations are generic or wrong, the prompting needs work. |
| 3 | **Does the creative agent produce usable output?** | Generate the ad variants. Are they good enough to run? You don't need perfection — you need "80% there, I'd tweak one line and ship it." If you're rewriting from scratch, the agent isn't delivering value. |
| 4 | **Does executing the recommendations actually improve results?** | Implement Play 1 and Play 2 on the Glacis account. Wait 2 weeks. Did CTR improve? Did CPL drop? Did you save the estimated budget waste? If yes, you have quantified proof that the system works. |

---

## The Timeline

| Week | What You Build | What You Validate |
|------|---------------|------------------|
| 1-2 | Data ingestion from LinkedIn API | Can I reliably pull structured campaign data? |
| 2-3 | Analysis agent (LLM + benchmarks + rules) | Does it find real problems I didn't know about? |
| 3-4 | Creative agent (ad copy generation) | Are the outputs good enough to run? |
| 4-5 | Simple dashboard UI | Does seeing the plays in a dashboard change how I manage ads? |
| 5-8 | Execute recommendations on Glacis account, measure results | Did performance actually improve? By how much? |

---

## What You DON'T Build for the POC

This is equally important:

- **Don't build automated execution via API.** Clicking [Execute] should show you what to change in Campaign Manager. You make the changes manually. API-based execution is a v2 feature.
- **Don't build real-time monitoring.** Pull data once daily via a cron job or even manually. Real-time is unnecessary for a weekly cadence of plays.
- **Don't build competitive monitoring.** That's a separate agent with separate data sources. It's nice-to-have, not core to the POC loop.
- **Don't build the orchestrator agent.** With only 2-3 agents, you don't need orchestration. You can hard-code the sequence: pull data → run analysis → surface plays.
- **Don't build multi-user or authentication.** It's just you, using it on the Glacis account. Authentication is a scaling concern.

---

## POC Success Criteria

Before you start, define what "this worked" looks like:

1. **The system surfaces at least 2 problems I hadn't noticed** in the first analysis run
2. **At least 1 creative variant is good enough to run** with minimal editing
3. **Implementing the recommendations improves performance** — specifically, CTR improves by 15%+ or CPL drops by 15%+ within 2 weeks of executing the plays
4. **The weekly time I spend managing LinkedIn Ads drops** from X hours to Y hours

If you hit 3 out of 4, you have a validated POC worth investing in.

---

## Pre-Code Validation Exercise

**Before writing a single line of code, run the analysis agent manually.** Pull your current Glacis LinkedIn Ads data from Campaign Manager right now, paste it into Claude, and ask it to analyze using the benchmarks and rules discussed above. See what it finds. If the manual version surfaces valuable insights, the automated version will too. If the manual version produces generic junk, you have a prompting problem to solve before building anything.
