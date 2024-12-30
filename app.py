from flask import Flask, render_template, redirect, request, session, flash, request, jsonify, url_for
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from PIL import Image, ImageDraw
from datetime import datetime
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
app.secret_key = 'secretZaylixy88'
db = SQL("sqlite:///users.db")

db.execute('''CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT NOT NULL,
                   hash TEXT NOT NULL
               );''')


db.execute('''CREATE TABLE IF NOT EXISTS images (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   path TEXT NOT NULL,
                   FOREIGN KEY (user_id) REFERENCES users(id)
               );''')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/log_sign', methods=['GET', 'POST'])
def login_signup():
    return render_template('log_sign.html')


@app.route('/gridsize')
def gridsize():
    return render_template('gridsize.html')


@app.route('/grid')
def grid():
    grid_size = request.args.get('gridSize', default=5, type=int)
    return render_template('grid.html', grid_size=grid_size)


@app.route('/save_grid', methods=['POST'])
def save_grid():
    data = request.get_json()
    grid_size = data['grid_size']
    grid_data = data['grid_data']

    # Calculate the pixel size dynamically
    pixel_size = 600 // grid_size  # Adjust this value to fit the image dimensions

    # Create an image (blank canvas)
    img = Image.new('RGB', (grid_size * pixel_size, grid_size * pixel_size), 'white')
    draw = ImageDraw.Draw(img)

    # Draw the grid with the pixel colors and gray borders
    for i in range(grid_size):
        for j in range(grid_size):
            color = grid_data[i][j]
            x0, y0 = j * pixel_size, i * pixel_size  # Corrected
            x1, y1 = (j + 1) * pixel_size, (i + 1) * pixel_size  # Corrected
            draw.rectangle([x0, y0, x1, y1], fill=color)
            draw.rectangle([x0, y0, x1, y1], outline="#ccc", width=1)

    # Save the image
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'grid_{timestamp}.png'
    img_path = os.path.join('static', 'images', filename)  # Full path to save
    img.save(img_path)

    # Get user ID from session
    user_id = session.get("user_id")

    # Save the image path to the database
    db.execute("INSERT INTO images (user_id, path) VALUES (?, ?)", user_id, img_path)

    return jsonify({'message': 'Grid saved successfully!'})


@app.route('/gallery')
def gallery():
    user_id = session.get('user_id')
    # Retrieve image paths from the database
    image_rows = db.execute("SELECT path FROM images WHERE user_id = ?", user_id)
    image_paths = [row['path'] for row in image_rows]

    return render_template('gallery.html', image_paths=image_paths)


@app.route('/delete_image', methods=['POST'])
def delete_image():
    image_path = request.form.get('image_path')
    user_id = session.get("user_id")

    # Delete the image record from the database
    db.execute("DELETE FROM images WHERE user_id = ? AND path = ?", user_id, image_path)

    # Optionally, delete the image file from the filesystem
    if os.path.exists(image_path):
        os.remove(image_path)

    return redirect('/gallery')


@app.route('/login', methods=['POST'])
def login():
    temp_image_paths = session.get('image_paths', [])

    session.clear()

    username = request.form.get("username")
    password = request.form.get("password")

    if not username:
        flash("Must provide username", "error")
        return redirect("/log_sign")

    if not password:
        flash("Must provide password", "error")
        return redirect("/log_sign")

    rows = db.execute("SELECT * FROM users WHERE username = ?", username)

    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
        flash("Invalid username and/or password", "error")
        return redirect("/log_sign")

    session["user_id"] = rows[0]["id"]
    # Initialize image paths from the database when the user logs in
    image_rows = db.execute("SELECT path FROM images WHERE user_id = ?", session["user_id"])
    session['image_paths'] = [row['path'] for row in image_rows]

    return redirect("/gallery")


@app.route('/signup', methods=['POST'])
def signup():
    session.clear()

    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    if not username:
        flash("Must provide username", "error")
        return redirect("/log_sign")

    if not password:
        flash("Must provide password", "error")
        return redirect("/log_sign")

    if not confirmation:
        flash("Must provide confirmation", "error")
        return redirect("/log_sign")

    if password != confirmation:
        flash("Passwords must match", "error")
        return redirect("/log_sign")

    rows = db.execute("SELECT * FROM users WHERE username = ?", username)

    if len(rows) != 0:
        flash("Username already exists", "error")
        return redirect("/log_sign")

    hashed_password = generate_password_hash(password)
    db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)

    new_user_rows = db.execute("SELECT * FROM users WHERE username = ?", username)
    session["user_id"] = new_user_rows[0]["id"]

    return redirect("/gallery")

if __name__ == '__main__':
    app.run(debug=True)
