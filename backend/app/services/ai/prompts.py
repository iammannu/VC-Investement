"""
Prompt templates for memo generation.
Each section prompt is parameterized and returns structured markdown.
"""

EXTRACTION_PROMPT = """
You are a senior VC analyst assistant. Extract structured data from this pitch deck text.

PITCH DECK TEXT:
{text}

Return a JSON object with these exact fields (use null if not found):
{{
  "startup_name": "string or null",
  "website": "string or null",
  "founding_year": number or null,
  "stage": "pre-seed|seed|series-a|series-b|growth or null",
  "industry": "string or null",
  "geography": "string or null",
  "problem_statement": "2-3 sentence description or null",
  "solution": "2-3 sentence description or null",
  "founders": [
    {{"name": "string", "role": "string", "background": "string or null"}}
  ],
  "traction_metrics": [
    {{"metric": "string", "value": "string", "period": "string or null"}}
  ],
  "revenue_model": "string or null",
  "funding_ask": "string or null",
  "use_of_funds": "string or null",
  "team_size": number or null
}}
"""

EXECUTIVE_SUMMARY_PROMPT = """
You are a senior VC analyst at a top-tier investment firm writing an investment memo.

STARTUP DATA:
{startup_data}

CONTEXT FROM DOCUMENTS:
{retrieved_context}

Write a compelling Executive Summary section for this investment memo.
Structure:
- 2-paragraph overview of the company and opportunity
- Key investment highlights (3-5 bullet points)
- Why now (market timing)

Requirements:
- Professional VC memo tone
- Specific numbers and metrics where available
- 300-400 words
- Format as clean markdown

If data is missing or unclear, state it honestly. Do NOT fabricate metrics.
"""

PROBLEM_SOLUTION_PROMPT = """
You are a senior VC analyst. Write the Problem & Solution section of an investment memo.

STARTUP DATA:
{startup_data}

RELEVANT CONTEXT:
{retrieved_context}

Structure:
## The Problem
- Describe the pain point with market context
- Who suffers from this problem and how severely
- Why existing solutions are inadequate

## The Solution
- What the company has built
- How it uniquely addresses the problem
- Core technical or business model innovation
- Product differentiation

Requirements: 400-500 words, professional VC memo tone, specific language.
"""

MARKET_ANALYSIS_PROMPT = """
You are a senior VC analyst. Write the Market Analysis section.

STARTUP DATA:
{startup_data}

MARKET RESEARCH:
{market_research}

RETRIEVED CONTEXT:
{retrieved_context}

Structure:
## Market Size
- TAM (Total Addressable Market): cite source inline [Source: URL]
- SAM (Serviceable Addressable Market)
- SOM (Serviceable Obtainable Market) — realistic 3-year target

## Market Dynamics
- Key tailwinds driving growth
- Market timing assessment
- Relevant trends

## Growth Drivers
- Why this market will grow
- Key catalysts

Requirements: 400-600 words. Include specific $ figures with sources. State uncertainty ranges.
Do NOT fabricate market size numbers — use research data or clearly estimate with methodology.
"""

COMPETITOR_ANALYSIS_PROMPT = """
You are a senior VC analyst. Write the Competitive Analysis section.

STARTUP DATA:
{startup_data}

COMPETITOR RESEARCH:
{competitor_research}

RETRIEVED CONTEXT:
{retrieved_context}

Structure:
## Competitive Landscape
Brief overview of the competitive dynamics.

## Key Competitors
For each competitor: name, funding raised, positioning, key weakness.

## Competitive Advantages
What makes this startup defensible?
- Proprietary data / technology moat
- Network effects
- Switching costs
- Brand / go-to-market advantages

## Competitive Matrix
Create a comparison table in markdown format comparing on 4-5 key dimensions.

Requirements: 400-500 words, honest assessment.
"""

FOUNDER_ANALYSIS_PROMPT = """
You are a senior VC analyst. Write the Founder & Team Analysis section.

STARTUP DATA:
{startup_data}

FOUNDER RESEARCH:
{founder_research}

RETRIEVED CONTEXT:
{retrieved_context}

Structure:
## Team Overview
## Founder Profiles
For each founder: background, relevant experience, why they are uniquely qualified.
## Founder-Market Fit Assessment
## Team Gaps & Risks
Honest assessment of what's missing.

Requirements: 350-450 words. Investor-grade analysis of founder quality.
"""

FINANCIAL_ANALYSIS_PROMPT = """
You are a senior VC analyst. Write the Financial & Traction section.

STARTUP DATA:
{startup_data}

RETRIEVED CONTEXT:
{retrieved_context}

Structure:
## Current Traction
Key metrics: ARR/MRR, growth rate, users, customers, retention

## Unit Economics
CAC, LTV, LTV/CAC ratio, payback period (if available)

## Financial Ask
- How much they're raising
- Valuation / cap if disclosed
- Use of funds breakdown

## Path to Profitability
- Key milestones
- Burn rate and runway

Requirements: 350-450 words. If metrics are missing, state so explicitly.
Flag unrealistic projections or concerning unit economics.
"""

RISK_ANALYSIS_PROMPT = """
You are a senior VC analyst. Write a balanced Risk Analysis section.

STARTUP DATA:
{startup_data}

COMPETITOR RESEARCH:
{competitor_research}

RETRIEVED CONTEXT:
{retrieved_context}

Structure:
## Key Risks

For each risk, format as:
**[Risk Name]** (Severity: High/Medium/Low)
Description of the risk and its potential impact.
*Mitigant:* How the company plans to address this or how you'd evaluate it.

Include risks across:
- Market risk
- Technical / product risk
- Competition risk
- Team / execution risk
- Regulatory / legal risk
- Financial risk

Requirements: 350-500 words. Be honest — good memos flag real risks.
"""

RECOMMENDATION_PROMPT = """
You are a senior VC analyst writing the final Investment Recommendation.

STARTUP DATA:
{startup_data}

MEMO CONTEXT (all prior sections summarized):
{memo_summary}

Write the Investment Recommendation section:

## Recommendation: [STRONG INVEST / INVEST / WATCH / PASS]

## Investment Thesis
3-4 sentences on why this is (or isn't) a compelling investment.

## Key Value Drivers
What must go right for this to be a great investment.

## Key Risks to Watch
Top 2-3 risks the investor should monitor.

## Suggested Terms (if recommending invest)
- Suggested check size range
- Preferred structure notes
- Key diligence items before close

## Summary
One paragraph closing statement.

Requirements: 300-400 words. Be decisive — good investment memos have clear recommendations.

Also return a JSON block at the very end in this format:
```json
{{"recommendation": "strong_invest|invest|watch|pass", "confidence_score": 0.0-1.0}}
```
"""
