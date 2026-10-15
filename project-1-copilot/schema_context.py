import sqlite3

MAX_VALUES = 15


def get_schema():
    conn = sqlite3.connect("file:crm.db?mode=ro", uri=True)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    schema_text = ""
    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}");')
        columns = cursor.fetchall()
        schema_text += f"Table: {table}\n"
        for col in columns:
            name, col_type = col[1], col[2]
            line = f"  - {name} ({col_type})"
            if col_type.upper() == "TEXT":
                cursor.execute(f'SELECT COUNT(DISTINCT "{name}") FROM "{table}"')
                if cursor.fetchone()[0] <= MAX_VALUES:
                    cursor.execute(
                        f'SELECT DISTINCT "{name}" FROM "{table}" WHERE "{name}" IS NOT NULL ORDER BY 1'
                    )
                    values = [str(r[0]) for r in cursor.fetchall()]
                    line += " values: " + ", ".join(values)
            schema_text += line + "\n"
        schema_text += "\n"

    conn.close()
    return schema_text


if __name__ == "__main__":
    print(get_schema())