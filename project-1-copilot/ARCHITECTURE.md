# Project 1: Commercial Ops Copilot — Architecture

## What it does
Lets a user ask a plain-English question about the CRM sales pipeline
dataset and get back an accurate, grounded answer with supporting data

## Flow
1. User types a question (e.g. "what's our win rate by region this quarter?")
2. Claude receives the question, plus the database schema and data
   dictionary, and generates a SQL query
3. Python executes that SQL against crm.db
4. The raw results are sent back to Claude
5. Claude writes a plain-English summary of the results
6. Python renders a chart from the results (where relevant)
7. User sees: summary + chart + (optionally) the SQL query used

## Scope
Answers questions about historical sales pipeline data — deal outcomes,
agent/region/product performance, deal values, win rates.

Does NOT handle: forecasting/predictions, hypothetical scenarios,
or anything outside this dataset. Assumes questions can be answered
via SQL aggregation/filtering/joins, not open-ended analysis or opinion.

## Known risks
- Claude could generate incorrect SQL - need to validate against
  ground-truth queries already written
- Ambiguous questions may produce a technically-valid but
  wrong-in-spirit query
- Need a fallback for questions that don't map to the data at all
