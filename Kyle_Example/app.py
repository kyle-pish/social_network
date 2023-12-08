from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

# Define the path to the SQLite database file
DATABASE_PATH = os.path.join(os.getcwd(), 'users.db')

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
        age INTEGER,
        followers TEXT
        following_count INTEGER DEFAULT 0  -- New column for following count
    )
''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS friend_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        status TEXT CHECK( status IN ('pending','accepted','declined') ) NOT NULL DEFAULT 'pending',
        FOREIGN KEY (sender_id) REFERENCES users (id),
        FOREIGN KEY (receiver_id) REFERENCES users (id)
    )
''')

    conn.commit()
    conn.close()


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
    if 'username' in session:
        if username:
            # Fetch user profile information from the database and pass it to the template
            conn = create_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()

            # Get the count of followed users for the logged-in user
            cursor.execute('''
                SELECT COUNT(u.username)
                FROM users u
                INNER JOIN following f ON u.id = f.following_id
                INNER JOIN users u2 ON f.follower_id = u2.id
                WHERE u2.username = ?
            ''', (session['username'],))
            following_count = cursor.fetchone()[0]

            conn.close()

            if user_data:
                # Pass user data and following count to the profile template
                return render_template('profile.html', user=user_data, following_count=following_count)
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


 
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# -------------- Friends Functionality
@app.route('/friends')
def friends():
    if 'username' in session:
        conn = create_connection()
        cursor = conn.cursor()

        # Fetch the current user's ID
        cursor.execute('SELECT id FROM users WHERE username = ?', (session['username'],))
        user_id = cursor.fetchone()[0]

        # Fetch friends
        cursor.execute('''
            SELECT u.id, u.name, u.username, u.age 
            FROM users u
            JOIN friendships f ON u.id = f.user_id1 OR u.id = f.user_id2
            WHERE (f.user_id1 = ? OR f.user_id2 = ?) AND u.id != ?
        ''', (user_id, user_id, user_id))
        friends = cursor.fetchall()

        # Fetch friend requests
        cursor.execute('''
            SELECT fr.id, u.username 
            FROM friend_requests fr
            JOIN users u ON fr.sender_id = u.id
            WHERE fr.receiver_id = ? AND fr.status = 'pending'
        ''', (user_id,))
        friend_requests = cursor.fetchall()

        conn.close()
        return render_template('friends.html', friends=friends, friend_requests=friend_requests)
    
    return redirect(url_for('login'))



@app.route('/send_friend_request', methods=['GET', 'POST'])
def send_friend_request():
    if 'username' in session:
        if request.method == 'POST':
            receiver_username = request.form['receiver_username']

            conn = create_connection()
            cursor = conn.cursor()

            # Fetch the current user's ID
            cursor.execute('SELECT id FROM users WHERE username = ?', (session['username'],))
            sender_id = cursor.fetchone()[0]

            # Fetch the receiver's ID
            cursor.execute('SELECT id FROM users WHERE username = ?', (receiver_username,))
            receiver_data = cursor.fetchone()

            if receiver_data:
                receiver_id = receiver_data[0]
                # Insert the friend request
                cursor.execute('INSERT INTO friend_requests (sender_id, receiver_id) VALUES (?, ?)', 
                               (sender_id, receiver_id))
                conn.commit()
                message = "Friend request sent successfully!"
            else:
                message = "Receiver username does not exist."

            conn.close()
            return render_template('friend_request_sent.html', message=message)

        return render_template('send_friend_request.html')
    
    return redirect(url_for('login'))


@app.route('/respond_friend_request/<int:request_id>/<string:response>')
def respond_friend_request(request_id, response):
    if 'username' not in session:
        return redirect(url_for('login'))

    if response in ['accepted', 'declined']:
        conn = create_connection()
        cursor = conn.cursor()

        # Update the friend request status
        cursor.execute('UPDATE friend_requests SET status = ? WHERE id = ?', (response, request_id))
        
        if response == 'accepted':
            # Fetch the sender and receiver IDs from the friend_requests table
            cursor.execute('SELECT sender_id, receiver_id FROM friend_requests WHERE id = ?', (request_id,))
            sender_id, receiver_id = cursor.fetchone()
            
            # Insert the new friendship into the friendships table
            cursor.execute('INSERT INTO friendships (user_id1, user_id2) VALUES (?, ?)', (sender_id, receiver_id))
        
        conn.commit()
        conn.close()

    return redirect(url_for('friends'))





if __name__ == '__main__':
    create_table()  # Create the table when the app starts
    app.run(debug=True)
