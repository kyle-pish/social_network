from flask import Flask, render_template
import random

class Profile:
    def __init__(self, username) -> None:
        self.username = username
        followers = []
        posts = []

        def add_friend():
            pass

        def add_post():
            pass



profiles = []

app = Flask(__name__)



if __name__ == "__main__":
    app.run( # Starts the site
        host='0.0.0.0',  # Establishes the host
        port= random.randint(2000, 9000)  # Randomly select the port the machine hosts on.
    )