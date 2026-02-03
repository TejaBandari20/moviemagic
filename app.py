from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import boto3
import uuid
import os
from botocore.exceptions import ClientError

app = Flask(__name__)

# Use a static secret key
app.secret_key = 'your_static_secret_key_here'

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

# SNS Topic ARN
SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-1:977099000730:MovieTicketNotifications'

# AWS services
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns = boto3.client('sns', region_name=AWS_REGION)

# DynamoDB tables
USERS_TABLE_NAME = os.environ.get('USERS_TABLE_NAME', 'MovieMagic_Users')
BOOKINGS_TABLE_NAME = os.environ.get('BOOKINGS_TABLE_NAME', 'MovieMagic_Bookings')

users_table = dynamodb.Table(USERS_TABLE_NAME)
bookings_table = dynamodb.Table(BOOKINGS_TABLE_NAME)


# ===================== SNS EMAIL =====================

def send_booking_confirmation(booking):
    if not SNS_TOPIC_ARN:
        print("SNS_TOPIC_ARN is not set.")
        return False

    try:
        email_subject = f"MovieMagic Booking Confirmation - {booking['booking_id']}"

        email_message = f"""
Hello {booking['user_name']},

Your movie ticket booking is confirmed!

Booking Details:
----------------
Booking ID: {booking['booking_id']}
Movie: {booking['movie_name']}
Date: {booking['date']}
Time: {booking['time']}
Theater: {booking['theater']}
Location: {booking['address']}
Seats: {booking['seats']}
Amount Paid: {booking['amount_paid']}

Please show this confirmation at the theater to collect your tickets.

Thank you for choosing MovieMagic!
"""

        user_email = booking['booked_by']

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=email_subject,
            Message=email_message,
            MessageAttributes={
                'email': {
                    'DataType': 'String',
                    'StringValue': user_email
                }
            }
        )

        return True

    except Exception as e:
        print(f"Error sending booking confirmation: {e}")
        return False


# ===================== AUTH =====================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        try:
            response = users_table.get_item(Key={'email': email})
            if 'Item' in response:
                flash('Email already registered!', 'danger')
                return redirect(url_for('signup'))

            users_table.put_item(
                Item={
                    'id': str(uuid.uuid4()),
                    'name': name,
                    'email': email,
                    'password': password,
                    'created_at': datetime.now().isoformat()
                }
            )

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except ClientError as e:
            print(e)
            flash('Registration error', 'danger')

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
                    session['user'] = {
                        'id': user['id'],
                        'name': user['name'],
                        'email': user['email']
                    }
                    return redirect(url_for('home1'))

            flash('Invalid email or password', 'danger')

        except ClientError as e:
            print(e)
            flash('Login error', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out!', 'info')
    return redirect(url_for('index'))


# ===================== PAGES =====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/home1')
def home1():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home1.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact_us')
def contact():
    return render_template('contact_us.html')


# ===================== BOOKING =====================

@app.route('/b1', methods=['GET'], endpoint='b1')
def booking_page():
    if 'user' not in session:
        return redirect(url_for('login'))

    return render_template(
        'b1.html',
        movie=request.args.get('movie'),
        theater=request.args.get('theater'),
        address=request.args.get('address'),
        price=request.args.get('price')
    )


@app.route('/tickets', methods=['POST'])
def tickets():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        movie_name = request.form.get('movie')
        booking_date = request.form.get('date')
        show_time = request.form.get('time')
        theater_name = request.form.get('theater')
        theater_address = request.form.get('address')
        selected_seats = request.form.get('seats')
        amount_paid = request.form.get('amount')

        booking_id = f"MM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        booking_item = {
            'booking_id': booking_id,
            'movie_name': movie_name,
            'date': booking_date,
            'time': show_time,
            'theater': theater_name,
            'address': theater_address,
            'booked_by': session['user']['email'],
            'user_name': session['user']['name'],
            'seats': selected_seats,
            'amount_paid': amount_paid,
            'created_at': datetime.now().isoformat()
        }

        bookings_table.put_item(Item=booking_item)
        send_booking_confirmation(booking_item)

        flash('Booking successful! Confirmation sent to your email.', 'success')
        return render_template('tickets.html', booking=booking_item)

    except ClientError as e:
        print(f"Error saving booking: {e}")
        flash('An error occurred while booking tickets.', 'danger')
        return redirect(url_for('home1'))

    except Exception as e:
        print(f"Error processing booking: {e}")
        flash('Error processing booking', 'danger')
        return redirect(url_for('home1'))


# ===================== RUN =====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
