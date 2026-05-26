---
name: fsi-eval-runner
description: |
  Run evaluations and benchmarks for financial-services skills and agents. Use this skill whenever someone wants to test a financial skill, benchmark its quality, compare skill versions, detect regressions, or validate that a skill produces financially accurate outputs. Also use when someone says "run evals", "test this skill", "benchmark", "how does this skill perform", or "check the quality" in the context of financial-services plugins.
---

# FSI Eval Runner

You run the full evaluation lifecycle for financial-services skills — from generating domain-specific test cases to producing benchmark reports with financial accuracy checks.

This skill extends the `skill-creator` evaluation framework with assertions and grading criteria specific to financial industry outputs.

## Evaluation Workflow

### Step 1: Generate Test Cases

If `evals/evals.json` doesn't exist for the target skill, generate it:

```json
[
  {
    "prompt": "Realistic financial prompt that exercises the skill",
    "expected_behavior": "What a correct output looks like",
    "assertions": [
      "Objectively verifiable assertion #1",
      "Objectively verifiable assertion #2"
    ]
  }
]
```

**Financial-Specific Test Case Guidelines:**

For each skill, generate 2-3 test cases covering:

1. **Happy path** — Standard use case with well-known public data (use real tickers like AAPL, MSFT, JPM for comps; well-known deals for precedents)
2. **Edge case** — Missing data, unusual sector, or boundary conditions (pre-revenue company for DCF, cross-border deal for M&A)
3. **Accuracy check** — Prompt that requires specific financial calculations where correctness is verifiable

Use the prompt generator sub-agent for domain-appropriate test prompts:
```
Read agents/fsi-prompt-generator.md for guidance on generating realistic financial test prompts.
```

### Step 2: Run Evaluations

Execute with-skill and without-skill (baseline) runs. Follow the `skill-creator` methodology:

1. **With-skill run:** Spawn a subagent that has the target skill loaded, give it the eval prompt, capture transcript + outputs
2. **Baseline run:** Spawn a subagent WITHOUT the skill, give it the same prompt, capture transcript + outputs
3. Run both in parallel if subagents are available; sequentially otherwise

Save results to:
```
evals/
├── evals.json                    # Test case definitions
├── runs/
│   ├── run-001/
│   │   ├── with-skill/
│   │   │   ├── transcript.md
│   │   │   └── outputs/
│   │   └── baseline/
│   │       ├── transcript.md
│   │       └── outputs/
```

### Step 3: Grade Results

Use the FSI grader to evaluate each run:

```
Read agents/fsi-grader.md for the grading methodology.
```

The FSI grader extends the standard `skill-creator` grader with:

- **Financial accuracy checks** — Do numbers add up? Are formulas correct?
- **Data provenance** — Did the skill cite MCP sources correctly?
- **Regulatory completeness** — Are required disclosures/disclaimers present?
- **Output format compliance** — Does the output match the expected format conventions?

Save grading results to `evals/runs/run-NNN/grading.json`.

### Step 4: Aggregate Benchmarks

Run the aggregation to produce `benchmark.json`:

```bash
python3 scripts/aggregate_fsi_benchmark.py evals/
```

This produces:
- `benchmark.json` — Machine-readable metrics (pass_rate, timing, tokens, variance, financial accuracy scores)
- `benchmark.md` — Human-readable summary with tables

### Step 5: Generate Review Dashboard

```bash
python3 ../skill-creator/eval-viewer/generate_review.py evals/
```

Opens an interactive HTML dashboard for human review of outputs, side-by-side with-skill vs baseline comparison.

### Step 6: Regression Analysis (Optional)

For skills with prior benchmarks, run the benchmark analyst:

```
Read agents/fsi-benchmark-analyst.md for version comparison and regression detection.
```

Compare current `benchmark.json` against the prior version to detect:
- Pass rate changes (overall and per-assertion)
- Financial accuracy regressions (numbers drifting, formulas breaking)
- Performance changes (latency, token usage)

## Eval Data Strategy

### Mock Mode (Default)

Evals run against synthetic financial data for reproducibility:
- Sample tickers and financials (AAPL, MSFT, JPM with realistic but not real-time numbers)
- Template earnings transcripts and filings
- Standard comps tables and precedent deal lists

### Live Mode (Opt-in)

Set `EVAL_MODE=live` to test against real MCP providers:
- Requires provider API keys in environment
- Results will vary with market data — useful for integration testing
- Use sparingly (API costs, rate limits)

## Financial Assertions Library

When generating assertions, draw from these domain-specific patterns:

### Balance & Integrity
- "Balance sheet balances: total assets equal total liabilities plus total equity"
- "Income statement flows: revenue minus all expenses equals net income"
- "Cash flow ties: ending cash equals beginning cash plus net cash flows"

### Valuation Reasonableness
- "DCF discount rate (WACC) is between 5% and 20%"
- "Terminal growth rate is between 0% and 4%"
- "EV/EBITDA multiples for comps are between 3x and 50x"
- "P/E ratios for the peer set are between 5x and 100x"

### Completeness
- "Comps table includes at least 5 comparable companies"
- "Precedent transactions include at least 3 deals"
- "All required financial statements are present (income statement, balance sheet, cash flow)"
- "Output includes source citations for all market data"

### Regulatory
- "Output includes appropriate disclaimers for forward-looking statements"
- "No material nonpublic information referenced"
- "Analyst certification language present (for research outputs)"

### Format
- "Excel workbook uses correct color coding (blue inputs, black formulas, green links)"
- "Pitch deck includes confidential watermark"
- "All slides have page numbers and date"

## Quality Gates

For a skill to pass evaluation and be eligible for publishing:

| Metric | Threshold |
|--------|-----------|
| Overall pass rate | >= 80% |
| Financial accuracy assertions | >= 90% |
| No critical failures | 0 critical |
| Baseline improvement | With-skill >= baseline on pass rate |
