# main.py
from flask import Flask, request, jsonify, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
import sys

# Initialize the Flask application
app = Flask(__name__, template_folder='.')
app.secret_key = os.urandom(24)

# --- MongoDB Connection ---
# IMPORTANT: Replace <YOUR_USERNAME> and <YOUR_PASSWORD> with your actual MongoDB Atlas credentials.
# Make sure to also remove the angle brackets <>.
MONGO_URI = "mongodb+srv://roataract_db:rZodHPueBk2nuRcb@cluster0.pxdezgf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# --- Database Connection with Error Handling ---
try:
    client = MongoClient(MONGO_URI)
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
    print("MongoDB connection successful.")
    db = client.get_database('rotaract_club') 
    users_collection = db.users
except ConnectionFailure as e:
    print(f"MongoDB connection failed: {e}", file=sys.stderr)
    # You might want to exit the app if the DB connection fails
    sys.exit("Could not connect to MongoDB. Please check your connection string and network access settings in MongoDB Atlas.")
except Exception as e:
    print(f"An error occurred: {e}", file=sys.stderr)
    sys.exit("An unexpected error occurred during database initialization.")


# --- HTML Page Serving Routes ---

@app.route('/')
def index():
    """Serves the main landing page."""
    return render_template('index.html')

@app.route('/event')
def event():
    """Serves the event details page."""
    return render_template('event.html')

@app.route('/team')
def team():
    """Serves the team page."""
    return render_template('team.html')

# --- API Routes ---

@app.route('/api/register', methods=['POST'])
def register():
    """Handles user registration and stores them in MongoDB."""
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'member')

    if not name or not email or not password:
        return jsonify({"status": "error", "message": "Missing name, email, or password"}), 400

    # Check if a user with that email already exists in the database
    if users_collection.find_one({'email': email}):
        return jsonify({"status": "error", "message": "Email already registered"}), 409

    # Hash the password for security before storing it
    hashed_password = generate_password_hash(password)
    
    # Insert the new user document into the 'users' collection
    users_collection.insert_one({
        'name': name,
        'email': email,
        'password_hash': hashed_password,
        'role': role
    })

    return jsonify({"status": "success", "message": "Registration successful! Please login."}), 201


@app.route('/api/login', methods=['POST'])
def login():
    """Handles user login by checking credentials against MongoDB."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Missing email or password"}), 400

    # Find the user in the database by their email
    user = users_collection.find_one({'email': email})

    # Check if user exists and if the provided password is correct
    if user and check_password_hash(user['password_hash'], password):
        # Store user info in the session to keep them logged in
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        
        return jsonify({
            "status": "success",
            "message": f"Welcome {user['name']}!",
            "user": {"name": user['name'], "email": user['email'], "role": user['role']}
        }), 200
    else:
        return jsonify({"status": "error", "message": "Invalid email or password"}), 401
        
@app.route('/api/logout', methods=['POST'])
def logout():
    """Handles user logout."""
    session.clear() # Clear all session data
    return jsonify({"status": "success", "message": "Successfully logged out"}), 200


if __name__ == '__main__':
    # Runs the Flask app. 
    # debug=True will auto-reload the server when you make changes.
    app.run(debug=True, port=5000)
