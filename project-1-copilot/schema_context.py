import sqlite3

def get_schema():
    conn = sqlite3.connect("crm.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema_text = ""
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        schema_text += f"Table: {table_name}\nColumns: {', '.join(col_names)}\n\n"

    conn.close()
    return schema_text

if __name__ == "__main__":
    print(get_schema())