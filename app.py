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


def create_friend_table():
    """Create a table to store friend relationships"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS friendships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_id INTEGER,
        user2_id INTEGER,
        FOREIGN KEY(user1_id) REFERENCES users(id),
        FOREIGN KEY(user2_id) REFERENCES users(id)
    )
''')
    conn.commit()
    conn.close()
    
def get_friends_posts(username):
    conn = create_connection()
    cursor = conn.cursor()
    all_posts = []
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_id = cursor.fetchone()
    user_id = user_id[0]
    cursor.execute('SELECT user2_id FROM friendships WHERE user1_id')
    friend_ids = cursor.fetchall()
    for friend in friend_ids:
        print("FRIENDS IDS: ", friend[0])
        friend_id = friend[0]
        cursor.execute('SELECT username FROM users WHERE id = ?', (friend_id,))
        friend_username = cursor.fetchone()
        print("FRIEND USERNAME: ", friend_username[0])
        friend_username = friend_username[0]
        cursor.execute('SELECT * FROM posts WHERE username = ? ORDER BY timestamp DESC', (friend_username,))
        all_posts = cursor.fetchall()
        print("FRIENDS POSTS: ", all_posts)


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

        all_posts = []
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_id = cursor.fetchone()
        user_id = user_id[0]
        cursor.execute('SELECT user2_id FROM friendships WHERE user1_id')
        friend_ids = cursor.fetchall()
        for friend in friend_ids:
            print("FRIENDS IDS: ", friend[0])
            friend_id = friend[0]
            cursor.execute('SELECT username FROM users WHERE id = ?', (friend_id,))
            friend_username = cursor.fetchone()
            print("FRIEND USERNAME: ", friend_username[0])
            friend_username = friend_username[0]
            cursor.execute('SELECT * FROM posts WHERE username = ? ORDER BY timestamp DESC', (friend_username,))
            all_posts = cursor.fetchall()
            print("FRIENDS POSTS: ", all_posts)
        

        conn.close()

        if user:
            # Successful login - set the session and redirect to home page
            session['username'] = username
            return render_template('home.html', posts=all_posts)
        else:
            # Failed login - handle appropriately (redirect to login page, display error, etc.)
            return "Login failed. Invalid username or password."

    # Check if the user is logged in using the session
    if 'username' in session:
        conn = create_connection()
        cursor = conn.cursor()
        username=session['username']
        all_posts = []
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_id = cursor.fetchone()
        user_id = user_id[0]
        cursor.execute('SELECT user2_id FROM friendships WHERE user1_id')
        friend_ids = cursor.fetchall()
        for friend in friend_ids:
            print("FRIENDS IDS: ", friend[0])
            friend_id = friend[0]
            cursor.execute('SELECT username FROM users WHERE id = ?', (friend_id,))
            friend_username = cursor.fetchone()
            print("FRIEND USERNAME: ", friend_username[0])
            friend_username = friend_username[0]
            cursor.execute('SELECT * FROM posts WHERE username = ? ORDER BY timestamp DESC', (friend_username,))
            all_posts = cursor.fetchall()
            print("FRIENDS POSTS: ", all_posts)

        return render_template('home.html', posts=all_posts)
    else:
        return redirect(url_for('login'))

#@app.route('/profile/<username>', methods=['GET'])
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
            
            # Fetch user's friends
            cursor.execute('''
                SELECT u.*
                FROM users u
                INNER JOIN friendships f ON u.id = f.user2_id
                INNER JOIN users u2 ON f.user1_id = u2.id
                WHERE u2.username = ?
            ''', (username,))
            friends = cursor.fetchall()

            #conn.close()

            if user_data:
                # Fetch posts from the posts database for the specified username
                cursor.execute('SELECT * FROM posts WHERE username = ? ORDER BY timestamp DESC', (username,))
                posts = cursor.fetchall()
                print(posts , "hey")

                conn.close()
                # Pass user data and following count to the profile template
                return render_template('profile.html', user=user_data, posts=posts, friends=friends)
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


        conn = create_connection()
        cursor = conn.cursor()
        all_posts = []
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user_id = cursor.fetchone()
        print("USER ID: ", user_id)
        user_id = user_id[0]
        cursor.execute('SELECT user2_id FROM friendships WHERE user1_id')
        friend_ids = cursor.fetchall()
        for friend in friend_ids:
            print("FRIENDS IDS: ", friend[0])
            friend_id = friend[0]
            cursor.execute('SELECT username FROM users WHERE id = ?', (friend_id,))
            friend_username = cursor.fetchone()
            print("FRIEND USERNAME: ", friend_username[0])
            friend_username = friend_username[0]
            cursor.execute('SELECT * FROM posts WHERE username = ? ORDER BY timestamp DESC', (friend_username,))
            all_posts = cursor.fetchall()
            print("FRIENDS POSTS: ", all_posts)

        return render_template('home.html', posts=all_posts)
    except sqlite3.IntegrityError:
            conn.rollback()
            conn.close()
            return "Post could not be posted at this time"
    


@app.route('/addfriend', methods=['POST'])
def add_friend():
    if 'username' in session:
        friend_username = request.form.get('username')

        conn = create_connection()
        cursor = conn.cursor()

        # Get the IDs of the logged-in user and the user to be added as a friend
        cursor.execute('SELECT id FROM users WHERE username = ?', (session['username'],))
        user1_id = cursor.fetchone()[0]

        cursor.execute('SELECT id FROM users WHERE username = ?', (friend_username,))
        user2_id = cursor.fetchone()[0]

        # Check if the friendship already exists
        cursor.execute('SELECT * FROM friendships WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)',
                       (user1_id, user2_id, user2_id, user1_id))
        existing_friendship = cursor.fetchone()

        if existing_friendship:
            conn.close()
            return "Friend already added."

        # Add the friendship to the database
        cursor.execute('INSERT INTO friendships (user1_id, user2_id) VALUES (?, ?)', (user1_id, user2_id))
        conn.commit()
        conn.close()

        return "Friend added successfully."
    else:
        return redirect(url_for('login'))


    
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))



if __name__ == '__main__':
    create_table()  # Create the table when the app starts
    create_post_table() # Create the table for the posts
    create_friend_table()
    app.run(debug=True)
