import os
import uuid
import streamlit as st
from text_to_sql import generate_sql, is_safe, run_sql, summarize, make_chart

st.set_page_config(page_title="Commercial Ops Copilot", page_icon="📊")
st.title("Commercial Ops Copilot")
st.caption("Ask plain-English questions about the sales pipeline. Answers come from live SQL queries on the data, not from the model's memory.")

os.makedirs("charts", exist_ok=True)

if "messages" not in st.session_state:
    st.session_state.messages = []


def answer(question):
    sql = generate_sql(question)
    if not sql or sql.strip().upper() == "CANNOT_ANSWER":
        return {"role": "assistant", "text": "I can't answer that from this data, or it asks to modify data, which this tool never does."}
    if not is_safe(sql):
        return {"role": "assistant", "text": "Blocked: only read-only queries are allowed.", "sql": sql}
    result, error = run_sql(sql)
    if error:
        return {"role": "assistant", "text": f"The query failed to run: {error}", "sql": sql}
    summary = summarize(question, sql, result)
    chart = make_chart(result, path=f"charts/{uuid.uuid4().hex[:8]}.png")
    return {"role": "assistant", "text": summary, "sql": sql, "table": result, "chart": chart}


def render(msg):
    st.markdown(msg["text"].replace("$", "\\$"))
    if msg.get("chart"):
        st.image(msg["chart"])
    if msg.get("table") is not None:
        with st.expander("Data"):
            st.dataframe(msg["table"])
    if msg.get("sql"):
        with st.expander("SQL used"):
            st.code(msg["sql"], language="sql")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        render(msg)

question = st.chat_input("Ask a question about the sales data")
if question:
    st.session_state.messages.append({"role": "user", "text": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Querying the data..."):
            reply = answer(question)
        render(reply)
    st.session_state.messages.append(reply)