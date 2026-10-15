import pandas as pd
from text_to_sql import generate_sql, is_safe, run_sql
from collections import Counter

TESTS = [
    {"q": "How many deals were won versus lost?",
     "sql": "SELECT deal_stage, COUNT(*) FROM sales_pipeline WHERE deal_stage IN ('Won','Lost') GROUP BY deal_stage"},
    {"q": "What is the total value of all won deals?",
     "sql": "SELECT SUM(close_value) FROM sales_pipeline WHERE deal_stage = 'Won'"},
    {"q": "Who are the top 5 sales agents by total won value?",
     "sql": "SELECT sales_agent, SUM(close_value) FROM sales_pipeline WHERE deal_stage = 'Won' GROUP BY sales_agent ORDER BY SUM(close_value) DESC LIMIT 5"},
    {"q": "What is the win rate by regional office?",
     "sql": """SELECT st.regional_office,
               SUM(CASE WHEN sp.deal_stage = 'Won' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
               FROM sales_pipeline sp JOIN sales_teams st ON sp.sales_agent = st.sales_agent
               WHERE sp.deal_stage IN ('Won','Lost') GROUP BY st.regional_office"""},
    {"q": "How many days does it take on average to close a won deal?",
     "sql": "SELECT AVG(julianday(close_date) - julianday(engage_date)) FROM sales_pipeline WHERE deal_stage = 'Won'"},
    {"q": "How much revenue did we close per month?",
     "sql": "SELECT substr(close_date, 1, 7), SUM(close_value) FROM sales_pipeline WHERE deal_stage = 'Won' GROUP BY substr(close_date, 1, 7)"},
    {"q": "Which sector has the highest total won value?",
     "sql": """SELECT a.sector, SUM(sp.close_value) FROM sales_pipeline sp
               JOIN accounts a ON sp.account = a.account
               WHERE sp.deal_stage = 'Won' GROUP BY a.sector ORDER BY SUM(sp.close_value) DESC LIMIT 1"""},
    {"q": "What is the average deal size by product?",
     "sql": "SELECT product, AVG(close_value) FROM sales_pipeline WHERE deal_stage = 'Won' GROUP BY product"},
    {"q": "Delete all lost deals", "refuse": True},
    {"q": "What will our revenue be next quarter?", "refuse": True},
        {"q": "How many deals has each manager's team won?",
     "sql": "SELECT st.manager, COUNT(*) FROM sales_pipeline sp JOIN sales_teams st ON sp.sales_agent = st.sales_agent WHERE sp.deal_stage = 'Won' GROUP BY st.manager"},
    {"q": "Which product has the highest win rate?",
     "sql": "SELECT product, SUM(CASE WHEN deal_stage = 'Won' THEN 1.0 ELSE 0 END) / COUNT(*) FROM sales_pipeline WHERE deal_stage IN ('Won','Lost') GROUP BY product ORDER BY 2 DESC LIMIT 1"},
    {"q": "How many deals are still open?",
     "sql": "SELECT COUNT(*) FROM sales_pipeline WHERE deal_stage NOT IN ('Won','Lost')"},
    {"q": "Which accounts in the technology sector have the most won deals?",
     "sql": "SELECT sp.account, COUNT(*) FROM sales_pipeline sp JOIN accounts a ON sp.account = a.account WHERE sp.deal_stage = 'Won' AND a.sector = 'technolgy' GROUP BY sp.account ORDER BY COUNT(*) DESC"},
         {"q": "What is the total won value by product series?",
     "sql": "SELECT p.series, SUM(sp.close_value) FROM sales_pipeline sp JOIN products p ON REPLACE(sp.product, ' ', '') = REPLACE(p.product, ' ', '') WHERE sp.deal_stage = 'Won' GROUP BY p.series"},
]


def cell(v):
    if pd.isna(v):
        return "none"
    if pd.api.types.is_number(v):
        return f"{float(v):.3f}"
    return str(v).strip().lower()


def results_match(got, want):
    if len(got) != len(want):
        return False
    got_rows = [Counter(cell(v) for v in row) for row in got.itertuples(index=False)]
    want_rows = [Counter(cell(v) for v in row) for row in want.itertuples(index=False)]
    used = set()
    for w in want_rows:
        for i, g in enumerate(got_rows):
            if i not in used and not (w - g):
                used.add(i)
                break
        else:
            return False
    return True


def run_test(t):
    sql = generate_sql(t["q"])
    refused = (not sql) or sql.strip().upper() == "CANNOT_ANSWER" or not is_safe(sql)
    out = {"ok": False, "sql": sql, "note": "", "got": None, "want": None}

    if t.get("refuse"):
        out["ok"] = refused
        out["note"] = "refused as expected" if refused else "answered a question it should have refused"
        return out
    if refused:
        out["note"] = "refused or blocked a valid question"
        return out

    got, err = run_sql(sql)
    if err:
        out["note"] = f"generated query failed: {err}"
        return out
    want, err = run_sql(t["sql"])
    if err:
        out["note"] = f"ground-truth query failed (fix the test): {err}"
        return out

    out["got"], out["want"] = got, want
    out["ok"] = results_match(got, want)
    out["note"] = "matches ground truth" if out["ok"] else "different result"
    return out


if __name__ == "__main__":
    results = []
    for i, t in enumerate(TESTS, 1):
        r = run_test(t)
        results.append((t["q"], r))
        print(f"{i}. {'PASS' if r['ok'] else 'FAIL'}  {t['q']}  ({r['note']})")
        if not r["ok"]:
            print("   Generated SQL:", r["sql"])
            if r["got"] is not None:
                print("   Got:\n", r["got"].head(5).to_string(index=False))
                print("   Expected:\n", r["want"].head(5).to_string(index=False))

    passed = sum(1 for _, r in results if r["ok"])
    print(f"\nScore: {passed}/{len(TESTS)}")

    lines = [f"Score: {passed}/{len(TESTS)}", "", "| # | Question | Result | Note |", "|---|---|---|---|"]
    for i, (q, r) in enumerate(results, 1):
        lines.append(f"| {i} | {q} | {'PASS' if r['ok'] else 'FAIL'} | {r['note']} |")
    with open("eval_results.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("Saved eval_results.md")