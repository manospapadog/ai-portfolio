import os
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from anthropic import Anthropic
from schema_context import get_schema
from matplotlib.ticker import FuncFormatter

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
SCHEMA = get_schema()

FORBIDDEN = ["drop", "delete", "update", "insert", "alter", "create", "attach", "pragma"]


def get_text(response):
    for block in response.content:
        if block.type == "text":
            return block.text
    return None


def clean_sql(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("sql"):
            text = text[3:]
    return text.strip()


def generate_sql(question):
    prompt = f"""You are a SQL expert. Given this SQLite database schema:

{SCHEMA}

Business definitions:
- Win rate = deals with deal_stage 'Won' divided by deals with deal_stage 'Won' or 'Lost'.
- Revenue or deal value means close_value on deals with deal_stage 'Won'.

Write a single read-only SQLite query that answers this question: {question}

If the question asks to change or delete data, or cannot be answered from this schema, return exactly the word CANNOT_ANSWER instead of a query.

Return ONLY the SQL query (or CANNOT_ANSWER), no explanation, no markdown formatting, no backticks."""

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = get_text(response)
    return clean_sql(text) if text else None


def is_safe(sql):
    lowered = sql.strip().rstrip(";").lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return False
    if ";" in lowered:
        return False
    words = lowered.replace("(", " ").replace(")", " ").replace(",", " ").split()
    return not any(word in FORBIDDEN for word in words)


def run_sql(sql):
    try:
        conn = sqlite3.connect("file:crm.db?mode=ro", uri=True)
        result = pd.read_sql_query(sql, conn)
        conn.close()
        return result, None
    except Exception as e:
        return None, str(e)


def summarize(question, sql, result):
    prompt = f"""A user asked: {question}

This SQL query was run:
{sql}

Results:
{result.head(50).to_string(index=False)}

Write a clear 2-3 sentence answer for a business reader. Use only the numbers shown in the results, and express rates as percentages. If the results are empty, say that no matching data was found."""

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return get_text(response)


def make_chart(result, path="chart.png"):
    if result is None or result.shape[1] != 2 or len(result) < 2 or len(result) > 30:
        return None
    label_col, value_col = result.columns
    if not pd.api.types.is_numeric_dtype(result[value_col]):
        return None

    values = result[value_col]
    name = value_col.lower()
    is_rate = values.between(0, 1).all() and any(k in name for k in ["rate", "pct", "percent", "share"])
    plot_values = values * 100 if is_rate else values

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(result[label_col].astype(str), plot_values)
    ax.set_title(f"{value_col.replace('_', ' ').title()} by {label_col.replace('_', ' ').title()}")
    ax.set_ylabel("%" if is_rate else value_col.replace("_", " ").title())
    if not is_rate:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.bar_label(bars, labels=[f"{v:.1f}%" if is_rate else f"{v:,.0f}" for v in plot_values], padding=3)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


if __name__ == "__main__":
    question = input("Ask a question about the sales data: ")
    sql = generate_sql(question)

    if not sql or sql.strip().upper() == "CANNOT_ANSWER":
        print("\nI can't answer that from this data, or it asks to modify data, which this tool never does.")
    else:
        print("\nGenerated SQL:\n", sql)
        if not is_safe(sql):
            print("\nBlocked: only read-only SELECT queries are allowed.")
        else:
            result, error = run_sql(sql)
            if error:
                print("\nThe query failed to run:", error)
            else:
                print("\nResults:\n", result)
                print("\nSummary:\n", summarize(question, sql, result))
                chart = make_chart(result)
                if chart:
                    print(f"\nChart saved to {chart}")