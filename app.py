from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import os
from flask import Flask, redirect, url_for, request, session, jsonify
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.auth
import google.auth.exceptions
import pathlib

import requests
from flask import Flask, session, abort, redirect, request
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import google.auth.transport.requests

app = Flask(__name__)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "252364305641-alloc4m9ovpauvqdhed8jlbpiuhnj28s.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="https://6b4f-115-114-88-222.ngrok-free.app/callback"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper


@app.route("/google-login")
def login():
    authorization_url, state = flow.authorization_url(prompt='login')
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session['email'] = id_info.get('email').split('@')[0]
    username = session['email']
    return render_template('/success_page.html',username=username)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")




app.secret_key = os.urandom(24)

# Database connection details
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = ""

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
def login_verify():
    
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
            return render_template('success_page.html',username = username.split('@')[0])
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