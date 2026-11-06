# AI Portfolio: Manos Papadogiannakis

**Practical AI use cases that automate real work across commercial and business operations.**

Much of the work in sales, revenue and business operations is repetitive: qualifying leads, researching accounts, pulling numbers, writing the same reports and follow-ups. This portfolio is a set of working builds, each one taking a specific task and automating it with AI tools. Each one answers two questions: *does it save real time, and can it be trusted?*

Every project follows the same rules:

- **Deterministic where possible, AI where it adds judgement.** Rules handle what rules can handle. Models handle research, language and ambiguity.
- **Show the evidence.** Answers come with the SQL, the source or the reasoning behind them.
- **Test against known answers.** Each project is checked against cases where the right outcome is already known, and the README documents what failed.
- **Keep a human in the loop** for anything that leaves the building.

---

## Projects

| # | Project | What it does | Stack |
|---|---|---|---|
| 1 | **[Commercial Ops Copilot](project-1-copilot/)** | Ask questions about CRM sales data in plain English and get a summary, a chart, and the exact SQL that produced it. Includes a test suite that compares results to hand-written SQL. | Python, SQLite, Streamlit, Claude API |
| 2 | **[Lead Desk](project-2-lead-desk/)** | n8n workflow that triages, researches, scores and routes inbound leads, then drafts personalised outreach for human approval. | n8n, Claude, Google Sheets, Gmail |
| 3 | **[Competitive Intelligence Agent](competitive-intel-agent/)** | Scheduled agent that watches five competitors' public pages, detects what is new, asks Claude whether it matters to a revenue team, and emails a weekly digest with a source link for every claim. Fetching and change detection use no AI and are covered by automated tests. | Python, GitHub Actions, Claude API, pytest |
| – | **[RAG starter](RAG-Project/)** | A first retrieval-augmented Q&A tool over a folder of documents. It answers only from retrieved sources, cites them, and says when it doesn't know. | Python, ChromaDB, sentence-transformers, Claude API |

### Highlights

- **Copilot:** the test suite caught a silent join bug, where a product name was spelled differently across two tables. The query ran without error but under-reported one product series by about 3.5M. It was invisible without ground-truth tests. [Read how it was found and fixed →](project-1-copilot/#what-the-tests-caught)
- **Lead Desk:** AI is used for exactly three jobs: website research, lead scoring and drafting. Everything around them (triage, routing, logging, approval) is deterministic, so every decision can be traced in the log. [See the workflow →](project-2-lead-desk/)
- **Competitive Intelligence Agent:** the first real weekly digest reported four press releases as this week's news, when all four were months old. They had only just appeared in a tracked source. The cause was found and fixed in code, with a test that reproduces it. [Read what it taught me →](competitive-intel-agent/#what-building-it-taught-me)

---


## About me

Strategy & Operations leader based in Athens, Greece. Previously Strategy & Operations Manager at Skroutz and Strategy Manager at Spitogatos. MSc Management, University of Mannheim.

**Tools:** SQL, Python, Power BI, n8n / Make / Zapier, Salesforce, HubSpot

📫 [LinkedIn](https://www.linkedin.com/in/manos-papadogiannakis/)· manospapadog@gmail.com
