from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database connection details
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "msithyd1"

# Connect to the PostgreSQL database
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# Function to ensure the 'users' table exists
def create_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_login (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL
            );
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def home():
    create_users_table()
    return render_template('home_page.html')

@app.route('/login', methods=['POST'])
def login():
    
    username = request.form['username']
    password = request.form['password']
    
    # Connect to the database and validate user
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM users_login WHERE username = %s AND password = %s",
            (username, password)
        )
        user = cursor.fetchone()
        if user:
            flash("Login successful!", "success")
            return render_template('success_page.html')
        else:
            flash("Invalid username or password", "danger")
            return render_template('unsuccessful_login_page.html')
    finally:
        cursor.close()
        conn.close()

@app.route('/registration_page')
def registration_page():
    return render_template('registration_page.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Check if username already exists
            cursor.execute("SELECT * FROM users_login WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user:
                # Redirect to unsuccessful page if user exists
                flash("Username already exists. Registration unsuccessful.", "danger")
                return render_template('unsuccessful_registration_page.html')

            # Insert new user into the database
            cursor.execute(
                "INSERT INTO users_login (username, password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
            flash("Registration successful! You can now log in.", "success")
            return render_template('successful_registration_page.html')
        finally:
            cursor.close()
            conn.close()

    return render_template('registration_page.html')

if __name__ == '__main__':
    app.run(debug=True)
