from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import sqlite3

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'console.log'

# Function to get the SQLite database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('users.db')
    return db

# Function to create the user table in the database
def create_user_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()


# Function to create the friends table in the database
def create_friends_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id1 INTEGER,
            user_id2 INTEGER,
            status TEXT,
            FOREIGN KEY (user_id1) REFERENCES users (id),
            FOREIGN KEY (user_id2) REFERENCES users (id)
        )
    ''')
    conn.commit()
    
# Function to close the database connection after each request
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Endpoint for user signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Insert the new user into the database
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# Endpoint for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Retrieve the user from the database
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if not user or not bcrypt.check_password_hash(user[2], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    return jsonify({'message': 'Login successful'}), 200


@app.route('/friendship', methods=['POST'])
def manage_friendship():
    data = request.get_json()
    username1 = data.get('username1')
    username2 = data.get('username2')
    action = data.get('action')

    if not username1 or not username2 or not action:
        return jsonify({'error': 'Missing usernames or action'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Retrieve user IDs based on usernames
    cursor.execute('SELECT id FROM users WHERE username = ?', (username1,))
    user_id1 = cursor.fetchone()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username2,))
    user_id2 = cursor.fetchone()

    if not user_id1 or not user_id2:
        return jsonify({'error': 'One or both usernames do not exist'}), 400

    if action == 'send_request':
        # Check if the friendship request already exists
        cursor.execute('SELECT * FROM friends WHERE user_id1 = ? AND user_id2 = ?', (user_id1[0], user_id2[0]))
        existing_request = cursor.fetchone()
        
        if existing_request:
            return jsonify({'error': 'Friendship request already sent'}), 400

        # Create a new friendship request
        cursor.execute('INSERT INTO friends (user_id1, user_id2, status) VALUES (?, ?, ?)', (user_id1[0], user_id2[0], 'Pending'))
        conn.commit()
        return jsonify({'message': 'Friendship request sent successfully'}), 201

    return jsonify({'error': 'Invalid action'}), 400


# Function to create the user table in the database
def create_user_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()

# Endpoint for accepting a friend request
@app.route('/accept_request', methods=['POST'])
def accept_friend_request():
    data = request.get_json()
    username1 = data.get('username1')
    username2 = data.get('username2')

    if not username1 or not username2:
        return jsonify({'error': 'Missing usernames'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Retrieve user IDs based on usernames
    cursor.execute('SELECT id FROM users WHERE username = ?', (username1,))
    user_id1 = cursor.fetchone()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username2,))
    user_id2 = cursor.fetchone()

    if not user_id1 or not user_id2:
        return jsonify({'error': 'One or both usernames do not exist'}), 400

    # Check if the friend request exists and is pending
    cursor.execute('SELECT * FROM friends WHERE user_id1 = ? AND user_id2 = ? AND status = ?', (user_id1[0], user_id2[0], 'Pending'))
    friend_request = cursor.fetchone()

    if not friend_request:
        return jsonify({'error': 'Friend request not found or already accepted/rejected'}), 400

    # Update the friend request status to 'Accepted'
    cursor.execute('UPDATE friends SET status = ? WHERE user_id1 = ? AND user_id2 = ?', ('Accepted', user_id1[0], user_id2[0]))
    conn.commit()

    return jsonify({'message': 'Friend request accepted successfully'}), 200

# Endpoint for rejecting a friend request
@app.route('/reject_request', methods=['POST'])
def reject_friend_request():
    data = request.get_json()
    username1 = data.get('username1')
    username2 = data.get('username2')

    if not username1 or not username2:
        return jsonify({'error': 'Missing usernames'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Retrieve user IDs based on usernames
    cursor.execute('SELECT id FROM users WHERE username = ?', (username1,))
    user_id1 = cursor.fetchone()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username2,))
    user_id2 = cursor.fetchone()

    if not user_id1 or not user_id2:
        return jsonify({'error': 'One or both usernames do not exist'}), 400

    # Check if the friend request exists and is pending
    cursor.execute('SELECT * FROM friends WHERE user_id1 = ? AND user_id2 = ? AND status = ?', (user_id1[0], user_id2[0], 'Pending'))
    friend_request = cursor.fetchone()

    if not friend_request:
        return jsonify({'error': 'Friend request not found or already accepted/rejected'}), 400

    # Update the friend request status to 'Rejected'
    cursor.execute('UPDATE friends SET status = ? WHERE user_id1 = ? AND user_id2 = ?', ('Rejected', user_id1[0], user_id2[0]))
    conn.commit()

    return jsonify({'message': 'Friend request rejected successfully'}), 200


# Endpoint for getting the friend list for a user
@app.route('/friend_list/<username>', methods=['GET'])
def get_friend_list(username):
    conn = get_db()
    cursor = conn.cursor()

    # Retrieve the user's ID based on the provided username
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user_id = cursor.fetchone()

    if not user_id:
        return jsonify({'error': 'User not found'}), 404

    # Retrieve the user's friend list
    cursor.execute('''
        SELECT u.username
        FROM users AS u
        JOIN friends AS f ON u.id = f.user_id2
        WHERE f.user_id1 = ? AND f.status = 'Accepted'
    ''', (user_id[0],))

    friend_list = [row[0] for row in cursor.fetchall()]

    return jsonify({'friend_list': friend_list}), 200


if __name__ == '__main__':
    app.run(debug=True)
    create_user_table()
    create_friends_table()