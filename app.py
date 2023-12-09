from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

# Define the path to the SQLite database file
DATABASE_PATH = os.path.join(os.getcwd(), 'users.db')
DATABASE_PATH_POSTS = os.path.join(os.getcwd(), 'posts.db')

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

# def create_posts_connection():
#     """Create a connection to the posts database"""
#     conn = None
#     try:
#         conn = sqlite3.connect(DATABASE_PATH_POSTS)
#     except sqlite3.Error as e:
#         print(e)
#     return conn

def create_post_table():
    """Create a table to store the posts of users"""
    conn = create_connection()
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
            print(user_data)
            # Get the count of followed users for the logged-in user
            """
            cursor.execute('''
                SELECT COUNT(u.username)
                FROM users u
                INNER JOIN following f ON u.id = f.following_id
                INNER JOIN users u2 ON f.follower_id = u2.id
                WHERE u2.username = ?
            ''', (session['username'],))
            following_count = cursor.fetchone()[0]

            conn.close()
            """
            if user_data:
                # Fetch posts from the posts database for the specified username
                cursor.execute('SELECT * FROM posts WHERE username = ? ORDER BY timestamp DESC', (username,))
                posts = cursor.fetchall()
                print(posts , "hey")

                conn.close()
                # Pass user data and following count to the profile template
                return render_template('profile.html', user=user_data,posts=posts)
            else:
                # Handle case where user data is not found
                return "User data not found."
        else:
            return "Username not provided."
    else:
        return redirect(url_for('login'))
    
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
    conn = create_connection()
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
