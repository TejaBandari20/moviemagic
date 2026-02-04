from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import boto3
import uuid
import os
from botocore.exceptions import ClientError

app = Flask(__name__)

# Security & Config
app.secret_key = 'your_static_secret_key_here'
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')
SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-1:977099000730:MovieTicketNotifications'

# AWS Services
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns = boto3.client('sns', region_name=AWS_REGION)
users_table = dynamodb.Table('MovieMagic_Users')
bookings_table = dynamodb.Table('MovieMagic_Bookings')

# Movie Data
MOVIES_DATA = [
    {'title': 'MAD', 'genre': 'Comedy, Drama', 'image': 'mad.jpg', 'price': 200, 'theater': 'PVR Cinemas', 'address': 'Hi-Tech City'},
    {'title': 'Court', 'genre': 'Drama, Thriller', 'image': 'court.jpg', 'price': 250, 'theater': 'AMB Cinemas', 'address': 'Gachibowli'},
    {'title': 'RRR', 'genre': 'Action, History', 'image': 'rrr.jpg', 'price': 300, 'theater': 'Prasads IMAX', 'address': 'Necklace Road'}
]

# --- HELPER FUNCTIONS ---
def send_email(booking):
    if not SNS_TOPIC_ARN: return False
    try:
        msg = f"Hello {booking['user_name']},\n\nYour booking for {booking['movie_name']} is confirmed!\nBooking ID: {booking['booking_id']}\nSeats: {booking['seats']}\n\nEnjoy the show!"
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="MovieMagic Ticket Confirmed",
            Message=msg,
            MessageAttributes={'email': {'DataType': 'String', 'StringValue': booking['booked_by']}}
        )
        return True
    except Exception as e:
        print(f"SNS Error: {e}")
        return False

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        name = request.form['name']
        
        try:
            if 'Item' in users_table.get_item(Key={'email': email}):
                flash('Email already registered', 'danger')
                return redirect(url_for('signup'))
            
            users_table.put_item(Item={'id': str(uuid.uuid4()), 'name': name, 'email': email, 'password': password})
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except ClientError:
            flash('Error creating account', 'danger')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            response = users_table.get_item(Key={'email': email})
            if 'Item' in response:
                user = response['Item']
                if check_password_hash(user['password'], password):
                    session['user'] = {'name': user['name'], 'email': user['email']}
                    return redirect(url_for('dashboard')) # NEW ROUTE NAME
            
            flash('Invalid credentials', 'danger')
        except ClientError:
            flash('Login error', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# --- NEW RENAMED ROUTES ---

@app.route('/dashboard') # Was /home1
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html', movies=MOVIES_DATA) # Was home1.html

@app.route('/booking') # Was /b1
def booking():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('booking.html', # Was b1.html
                           movie=request.args.get('movie'),
                           theater=request.args.get('theater'),
                           address=request.args.get('address'),
                           price=request.args.get('price'))

@app.route('/confirm_booking', methods=['POST']) # Was /tickets
def confirm_booking():
    if 'user' not in session: return redirect(url_for('login'))
    
    try:
        data = request.form
        booking_id = f"MM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        booking_item = {
            'booking_id': booking_id,
            'movie_name': data.get('movie'),
            'theater': data.get('theater'),
            'date': data.get('date'),
            'time': data.get('time'),
            'seats': data.get('seats'),
            'amount_paid': data.get('amount'),
            'address': data.get('address'),
            'booked_by': session['user']['email'],
            'user_name': session['user']['name']
        }
        
        bookings_table.put_item(Item=booking_item)
        send_email(booking_item)
        
        return render_template('confirmation.html', booking=booking_item) # Was tickets.html

    except Exception as e:
        print(e)
        flash('Booking failed', 'danger')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)