
from datetime import date
from functools import wraps
import secrets

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# In-memory storage only. Data resets when the app restarts.
users = {}
bookings = []
seat_inventory = {}
next_booking_id = 1

flights = [
    {"id": 1, "airline": "Airway Express", "source": "Hyderabad", "destination": "Delhi",
     "departure": "06:30 AM", "arrival": "08:45 AM", "price": 4500, "seats": 20},
    {"id": 2, "airline": "SkyConnect", "source": "Hyderabad", "destination": "Delhi",
     "departure": "10:15 AM", "arrival": "12:30 PM", "price": 5200, "seats": 18},
    {"id": 3, "airline": "FlyHigh", "source": "Hyderabad", "destination": "Delhi",
     "departure": "04:00 PM", "arrival": "06:20 PM", "price": 3900, "seats": 15},
    {"id": 4, "airline": "Airway Express", "source": "Delhi", "destination": "Hyderabad",
     "departure": "09:00 AM", "arrival": "11:15 AM", "price": 4600, "seats": 20},
    {"id": 5, "airline": "SkyConnect", "source": "Hyderabad", "destination": "Mumbai",
     "departure": "08:00 AM", "arrival": "09:40 AM", "price": 3200, "seats": 20},
    {"id": 6, "airline": "FlyHigh", "source": "Mumbai", "destination": "Hyderabad",
     "departure": "02:00 PM", "arrival": "03:40 PM", "price": 3400, "seats": 20},
    {"id": 7, "airline": "Airway Express", "source": "Hyderabad", "destination": "Bengaluru",
     "departure": "11:00 AM", "arrival": "12:15 PM", "price": 2800, "seats": 16},
    {"id": 8, "airline": "SkyConnect", "source": "Bengaluru", "destination": "Hyderabad",
     "departure": "06:00 PM", "arrival": "07:15 PM", "price": 2900, "seats": 20},
    {"id": 9, "airline": "FlyHigh", "source": "Delhi", "destination": "Mumbai",
     "departure": "07:30 AM", "arrival": "09:40 AM", "price": 4100, "seats": 18},
    {"id": 10, "airline": "Airway Express", "source": "Mumbai", "destination": "Delhi",
     "departure": "05:30 PM", "arrival": "07:40 PM", "price": 4300, "seats": 20},
]

cities = ["Hyderabad", "Delhi", "Mumbai", "Bengaluru"]


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_email" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def get_available_seats(flight, travel_date):
    key = (flight["id"], travel_date)
    if key not in seat_inventory:
        seat_inventory[key] = flight["seats"]
    return seat_inventory[key]


@app.route("/")
def welcome():
    if "user_email" in session:
        return redirect(url_for("home"))
    return render_template("welcome.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_email" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please fill in all fields.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif email in users:
            flash("An account with this email already exists.", "error")
        else:
            users[email] = {
                "username": username,
                "password": generate_password_hash(password),
            }
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_email" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = users.get(email)

        if user and check_password_hash(user["password"], password):
            session["user_email"] = email
            session["username"] = user["username"]
            return redirect(url_for("home"))

        flash("Invalid email or password. Please try again.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("welcome"))


@app.route("/flights", methods=["GET"])
@login_required
def home():
    today = date.today().isoformat()

    source = request.args.get("source", "Hyderabad")
    destination = request.args.get("destination", "Delhi")
    travel_date = request.args.get("travel_date", today)
    searched = request.args.get("search") == "1"

    matching_flights = []

    if searched:
        try:
            selected_date = date.fromisoformat(travel_date)
            if selected_date < date.today():
                flash("Please select today or a future travel date.", "error")
                searched = False
            elif source == destination:
                flash("Departure and destination cities must be different.", "error")
                searched = False
            elif source not in cities or destination not in cities:
                flash("Please select valid cities.", "error")
                searched = False
            else:
                for flight in flights:
                    if flight["source"] == source and flight["destination"] == destination:
                        available = get_available_seats(flight, travel_date)
                        if available > 0:
                            matching_flights.append({
                                **flight,
                                "available_seats": available
                            })
        except ValueError:
            flash("Please select a valid travel date.", "error")
            searched = False

    return render_template(
        "index.html",
        cities=cities,
        flights=matching_flights,
        source=source,
        destination=destination,
        travel_date=travel_date,
        today=today,
        searched=searched,
    )


@app.route("/book/<int:flight_id>", methods=["POST"])
@login_required
def book_flight(flight_id):
    global next_booking_id

    flight = next((item for item in flights if item["id"] == flight_id), None)
    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("home"))

    travel_date = request.form.get("travel_date", "")
    passenger = request.form.get("passenger", "").strip()

    try:
        selected_date = date.fromisoformat(travel_date)
    except ValueError:
        flash("Please select a valid travel date.", "error")
        return redirect(url_for("home"))

    if selected_date < date.today():
        flash("You cannot book a flight for a past date.", "error")
        return redirect(url_for("home", source=flight["source"],
                                destination=flight["destination"],
                                travel_date=travel_date, search="1"))

    if not passenger:
        flash("Please enter the passenger name.", "error")
        return redirect(url_for("home", source=flight["source"],
                                destination=flight["destination"],
                                travel_date=travel_date, search="1"))

    available = get_available_seats(flight, travel_date)
    if available <= 0:
        flash("Sorry, this flight has no seats remaining for that date.", "error")
        return redirect(url_for("home", source=flight["source"],
                                destination=flight["destination"],
                                travel_date=travel_date, search="1"))

    seat_inventory[(flight_id, travel_date)] = available - 1

    bookings.append({
        "id": next_booking_id,
        "reference": secrets.token_hex(4).upper(),
        "email": session["user_email"],
        "passenger": passenger,
        "travel_date": travel_date,
        "flight": flight.copy(),
        "status": "Confirmed",
    })
    next_booking_id += 1

    flash("Your flight has been booked successfully!", "success")
    return redirect(url_for("my_bookings"))


@app.route("/my-bookings")
@login_required
def my_bookings():
    user_bookings = [
        booking for booking in bookings
        if booking["email"] == session["user_email"]
    ]
    return render_template("bookings.html", bookings=user_bookings)


@app.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    booking = next(
        (
            item for item in bookings
            if item["id"] == booking_id
            and item["email"] == session["user_email"]
        ),
        None,
    )

    if not booking:
        flash("Booking not found.", "error")
    elif booking["status"] == "Cancelled":
        flash("This booking is already cancelled.", "info")
    else:
        key = (booking["flight"]["id"], booking["travel_date"])
        seat_inventory[key] = get_available_seats(
            booking["flight"], booking["travel_date"]
        ) + 1
        booking["status"] = "Cancelled"
        flash("Your booking has been cancelled.", "success")

    return redirect(url_for("my_bookings"))


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
