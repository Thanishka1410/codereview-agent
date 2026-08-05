import sqlite3

API_KEY = "sk-1234567890abcdef1234567890abcdef"
password = "SuperSecretPassword123!"

def get_user_data(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Vulnerable SQL query concatenation
    query = "SELECT * FROM users WHERE id = '" + str(user_id) + "'"
    cursor.execute(query)
    x = cursor.fetchall()
    
    return x

def execute_user_code(user_code):
    try:
        # Unsafe eval execution
        eval(user_code)
    except Exception:
        pass

if __name__ == "__main__":
    data = get_user_data("1 OR 1=1")
    print(data)
