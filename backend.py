from flask import Flask, render_template, request
import random

profiles = []
posts = []

class Profile:
    def __init__(self, username) -> None:
        self.username = username
        followers = []
        posts = []

        def add_friend():
            pass

        def add_post(self, post):
            self.posts.append(post)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('auth.html')

@app.route("/submit", methods=["POST"])
def profile():
        new_post = request.form["tweet-text"]
        posts.append(new_post)
        return render_template(
             "posts.html",
             posts = posts
        )

if __name__ == "__main__":
    app.run( # Starts the site
        host='0.0.0.0',  # Establishes the host
        port= random.randint(2000, 9000)  # Randomly select the port the machine hosts on.
    )