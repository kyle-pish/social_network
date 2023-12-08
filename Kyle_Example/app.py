from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os

app = Flask(__name__)

# Define the path to the SQLite database file
DATABASE_PATH = os.path.join(os.getcwd(), 'myapp.db')
#DATABASE_PATH_POSTS = os.path.join(os.getcwd(), 'posts.db')

app = Flask(__name__)
app.secret_key = os.urandom(24)


def create_connection():
    """Create a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
    except sqlite3.Error as e:
        print(e)
    return conn


def create_table():
    """Create a table to store user information."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        username TEXT UNIQUE,
        password TEXT,
        age INTEGER
    )
''')

    conn.commit()
    conn.close()

def create_posts_connection():
    """Create a connection to the posts database"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_post_table():
    """Create a table to store the posts of users"""
    conn = create_posts_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        post_content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

@app.route('/')
def login():
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']

        conn = create_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO users (name, username, password, age) VALUES (?, ?, ?, ?)',
                           (name, username, password, age))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.rollback()
            conn.close()
            return "Username already exists. Please choose a different one."

    return render_template('signup.html')


@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Successful login - set the session and redirect to home page
            session['username'] = username
            return redirect(url_for('home'))
        else:
            # Failed login - handle appropriately (redirect to login page, display error, etc.)
            return "Login failed. Invalid username or password."

    # Check if the user is logged in using the session
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/profile/<username>', methods=['GET'])
def profile(username):
    print("Username parameter:", username)
    if 'username' in session:
        if username:
            # Fetch user profile information from the database and pass it to the template
            conn = create_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()

            if user_data:
                # Fetch posts from the posts database for the specified username
                conn_posts = create_connection()
                cursor_posts = conn_posts.cursor()

                cursor_posts.execute('SELECT * FROM posts WHERE username = ? ORDER BY timestamp DESC', (username,))
                posts = cursor_posts.fetchall()
                print(posts, "hey")

                conn_posts.close()

                # Convert user data and posts to JSON format
                user_json = {
                    'id': user_data[0],
                    'name': user_data[1],
                    'username': user_data[2],
                    'age': user_data[4]
                }
                print(user_json)
                posts_json = []
                for post in posts:
                    post_json = {
                        'id': post[0],
                        'username': post[1],
                        'post_content': post[2],
                        'timestamp': post[3]
                    }
                    posts_json.append(post_json)
                print(posts_json, "hey")

                # Return JSON response
                return jsonify(user=user_json, posts=posts_json)
            else:
                # Handle case where user data is not found
                return jsonify(message="User data not found.")
        else:
            return jsonify(message="Username not provided.")
    else:
        return jsonify(message="User not logged in.")
    
@app.route('/search', methods=['GET'])
def search():
    if 'username' in session:
        search_username = request.args.get('search_username')

        conn = create_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (search_username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            return render_template('search.html', user_data=user_data)
        else:
            return render_template('search.html', user_not_found=True)

    return redirect(url_for('login'))

@app.route('/addfriend', methods=['POST'])
def add_friend():
    username = request.form.get('username')
    return "Friend added successfully"

@app.route('/makepost', methods=['GET'])
def make_post():
    return render_template('makepost.html')

@app.route('/post', methods=['POST'])
def create_post():
    post = request.form.get('post')
    username = request.form.get('username')
    conn = create_posts_connection()
    cursor = conn.cursor()

    # conn2 = create_connection()
    # cursor2 = conn2.cursor()

    # cursor2.execute('SELECT * FROM users WHERE username = ?', (username,))
    # user_data = cursor2.fetchone()

    # conn2.close()
    print("username:")
    print(username)
    print("post:")
    print(post)
    try:
        cursor.execute('INSERT INTO posts (username, post_content) VALUES (?, ?)', 
                        (username, post))

        conn.commit()
        conn.close()
        return render_template('home.html')
    except sqlite3.IntegrityError:
            conn.rollback()
            conn.close()
            return "Post could not be posted at this time"
    
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))



if __name__ == '__main__':
    create_table()  # Create the table when the app starts
    create_post_table() # Create the table for the posts
    app.run(debug=True)
