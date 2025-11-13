from imutils.video import VideoStream
import cv2
import time
import f_detector
import imutils
import numpy as np
from flask import Flask, render_template, request, jsonify, redirect, url_for, session,Response
from flask_mail import Mail, Message
import mysql.connector
from hashlib import sha256
import threading
from itsdangerous import URLSafeTimedSerializer
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'zambdbdb'

db_config = {
    'host': 'localhost',
    'user': 'root',           # Replace with your MySQL username
    'password': '',           # Replace with your MySQL password
    'database': 'care-connect' # Replace with your MySQL database name
}

# Configure mail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'zamiashafi30@gmail.com'  # Enter your email address
app.config['MAIL_PASSWORD'] = 'fvhd xmdr hxlx ncmh'      # Enter your email password

mail = Mail(app)

CORS(app)


# Secret key for generating the token
app.config['SECRET_KEY'] = 'zamzizai'

# Initialize the serializer with your app's secret key
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def get_db_connection():
    return mysql.connector.connect(**db_config)

def hash_password(password):
    return sha256(password.encode()).hexdigest()


@app.route("/")
def index():
   
    return render_template("index.html")

@app.route("/home")
def home():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("home.html")


@app.route('/get_blink_direction', methods=['GET'])
def get_blink_direction():
    global blink_direction
    print(blink_direction)
    return jsonify({'direction': blink_direction})

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check user credentials
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM care_taker WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        # If the user exists
        if user:
            # Check if the password is correct
            hashed_password = hash_password(password)
            if hashed_password == user['password']:
                session['user_id'] = user['ct_id']  # Store user ID in session
                
                session['username'] = user['uname']   # Store username in session
                session['uemail']=user['email']
               
                # Redirect to dashboard based on role
                
                    # Get total file count and last login details
                  
                return render_template('home.html', response="Successful Login")
            else:
                return render_template('login.html', error="Invalid email or password. Please try again.")
             

        else:
            return render_template('login.html', error="Invalid email or password. Please try again.")

    return render_template('login.html')



@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Create a new user
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT * FROM care_taker WHERE email = %s"
        cursor.execute(query, (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            connection.close()
            return render_template('register.html',response="Email address already exists. Please choose a different one.")
            

        # Encrypt password
        hashed_password = hash_password(password)
        query = "INSERT INTO care_taker (uname, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, email, hashed_password))
        connection.commit()
        
        connection.close()
        

        return render_template('login.html',response="registration Successfull")  # Redirect to login page after successful registration

    return render_template('register.html')


@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # Check if the email exists in the database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM care_taker WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user:
            
            # Generate a token for password reset
            token = serializer.dumps(email, salt='password-reset')

            # Send password reset link via email
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', sender='zamiashafi30@gmail.com', recipients=[email])
            msg.body = f"Please click the following link to reset your password: {reset_link}"
            mail.send(msg)

            return render_template('forgot_password.html', response="Password reset link has been sent to your email.")

        else:
            return render_template('forgot_password.html', error="Email address not found.")

    return render_template('forgot_password.html')


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)  # Token expires after 1 hour (3600 seconds)
    except:
        return render_template('reset_password.html', error="Invalid or expired token.")

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('reset_password.html', error="Passwords do not match.")

        # Hash the new password
        hashed_password = hash_password(password)

        # Update the user's password in the database
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "UPDATE care_taker SET password = %s WHERE email = %s"
        cursor.execute(query, (hashed_password, email))
        connection.commit()
        connection.close()

        return render_template('reset_password.html', response="Password has been reset successfully.")

    return render_template('reset_password.html', token=token)



@app.route("/add_keys", methods=['POST', 'GET'])
def add_keys():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor()
   
    query = "SELECT * FROM preset_keys WHERE ct_id = %s"
    cursor.execute(query, (user_id,))
    keys = cursor.fetchall() # Extract key names from the result
    connection.close()

    if request.method == 'POST':
        key_name = request.form['name']  # Get the key name from the form

        # Get user ID from session
        user_id = session['user_id']

        # Insert the key into the database
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO preset_keys (ct_id, k_name) VALUES (%s, %s)"
        cursor.execute(query, (user_id, key_name))
        connection.commit()
        query = "SELECT * FROM preset_keys WHERE ct_id = %s"
        cursor.execute(query, (user_id,))
        keys = cursor.fetchall() # Extract key names from the result
        connection.close()

        return render_template("add_keys.html", response="Key added successfully.", keys=keys)

    return render_template("add_keys.html",keys=keys)


@app.route('/delete_key', methods=['POST'])
def delete_key():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        k_id = request.form['k_id']  # Get the key name to be deleted from the form

        # Get user ID from session
        user_id = session['user_id']

        # Delete the key from the database
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "DELETE FROM preset_keys WHERE ct_id = %s AND k_id = %s"
        cursor.execute(query, (user_id, k_id))
        connection.commit()

        # Get the updated list of keys after deletion
        query = "SELECT * FROM preset_keys WHERE ct_id = %s"
        cursor.execute(query, (user_id,))
        keys = cursor.fetchall() # Extract key names from the result
        connection.close()

        return render_template("add_keys.html", response="Key deleted successfully.", keys=keys)

    return render_template("add_keys.html")






@app.route("/logout")
def logout():
    # Clear user-related data from session
    
    session.pop('user_id', None)
   
    return render_template('login.html',response='logout succesfull')


@app.route('/send-message',methods=["POST"])
def sendmessage():
    if request.method == 'POST':
        message = request.form['message']
        recipient=session['uemail']
    # Create message
        msg = Message('Care-AI', sender='zamiashafi30@gmail.com', recipients=[recipient])
        msg.body = message

    # Send message
        mail.send(msg)
    
        return render_template('preset_virtual_keyboard.html',response="Mail sent Successfully")
    




@app.route('/navigate', methods=['POST'])
def navigate():
    direction = request.json.get('direction')

    if direction == 'left':
        print("Navigation: Open virtual keyboard")
    elif direction == 'right':
        print("Navigation: Open preset virtual keyboard")

    return jsonify({'success': True})

@app.route('/virtual_keyboard')
def virtual_keyboard():
    return render_template('virtual_keyboard.html')

@app.route('/preset_virtual_keyboard')
def preset_virtual_keyboard():
    if 'user_id' not in session:
        return redirect('/login')

    # Get user ID from session
    user_id = session['user_id']

    # Fetch the keys associated with the user from the database
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT k_name FROM preset_keys WHERE ct_id = %s"
    cursor.execute(query, (user_id,))
    keys = [row[0] for row in cursor.fetchall()]  # Extract key names from the result
    connection.close()

    return render_template('preset_virtual_keyboard.html', keys=keys)


# Initialize global variables
COUNTER = 0
TOTAL = 0
blink_direction = ""

# Function to perform eye blink detection
def eye_blink_detection():
    global COUNTER, TOTAL, blink_direction
    detector = f_detector.eye_blink_detector()
    vs = VideoStream(src=3).start()

    while True:
        start_time = time.time()
        im = vs.read()
        im = cv2.flip(im, 1)
        im = imutils.resize(im, width=720)
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
   
        rectangles = detector.detector_faces(gray, 0)
        boxes_face = f_detector.convert_rectangles2array(rectangles, im)
        if len(boxes_face) != 0:
            areas = f_detector.get_areas(boxes_face)
            index = np.argmax(areas)
            rectangles = rectangles[index]
            boxes_face = np.expand_dims(boxes_face[index], axis=0)

            COUNTER, TOTAL, type = detector.eye_blink(gray, rectangles, COUNTER, TOTAL)
            blink_direction = type

            img_post = f_detector.bounding_box(im, boxes_face, ['type: {}'.format( type)])
        else:
            img_post = im 
    
        end_time = time.time() - start_time    
        FPS = 1 / end_time
        cv2.putText(img_post, f"FPS: {round(FPS,3)}", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
        
        # Encode image to JPEG format
        _, img_encoded = cv2.imencode('.jpg', img_post)
        # Convert image to bytes
        img_bytes = img_encoded.tobytes()
        # Yield image bytes as a response
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')



@app.route('/video_feed')
def video_feed():
    return Response(eye_blink_detection(), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route("/consent")
def consent():
    return render_template('consent.html')

def run_server():
    app.run(debug=True)




if __name__ == '__main__':
    

    # Start Flask app in the main thread
    run_server()
