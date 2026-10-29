
from datetime import date
from functools import wraps
import secrets

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Simple in-memory demo storage. Data resets when Flask restarts.
users = {}
bookings = []
occupied_seats = {}
next_booking_id = 1

cities = ["Hyderabad", "Delhi", "Mumbai", "Bengaluru"]
SEAT_COLUMNS = ["A", "B", "C", "D", "E", "F"]

route_options = [
    ("Hyderabad", "Delhi", 3900),
    ("Hyderabad", "Mumbai", 3000),
    ("Hyderabad", "Bengaluru", 2600),
    ("Delhi", "Mumbai", 3800),
    ("Delhi", "Bengaluru", 4200),
    ("Mumbai", "Bengaluru", 2800),
]

airlines = [
    "Airway Express", "SkyConnect", "FlyHigh",
    "Cloud Airlines", "Skyline Airways"
]

departure_times = [
    "06:00 AM", "09:00 AM", "12:30 PM",
    "04:00 PM", "08:00 PM"
]

arrival_times = [
    "08:15 AM", "11:15 AM", "02:45 PM",
    "06:15 PM", "10:15 PM"
]

# Generate 60 sample flights: 5 for each direction of 6 city pairs.
flights = []
flight_id = 1

for city_a, city_b, base_price in route_options:
    for source, destination in [
        (city_a, city_b),
        (city_b, city_a)
    ]:
        for i in range(5):
            flights.append({
                "id": flight_id,
                "airline": airlines[i],
                "source": source,
                "destination": destination,
                "departure": departure_times[i],
                "arrival": arrival_times[i],
                "price": base_price + i * 350,
                "seats": 36
            })
            flight_id += 1


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_email" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def find_flight(flight_id):
    return next(
        (flight for flight in flights if flight["id"] == flight_id),
        None
    )


def valid_travel_date(value):
    try:
        selected = date.fromisoformat(value)
        return selected if selected >= date.today() else None
    except (ValueError, TypeError):
        return None


def get_occupied_seats(flight_id, travel_date):
    key = (flight_id, travel_date)
    if key not in occupied_seats:
        occupied_seats[key] = set()
    return occupied_seats[key]


def get_available_seats(flight, travel_date):
    return flight["seats"] - len(
        get_occupied_seats(flight["id"], travel_date)
    )


def make_seat_map(flight, travel_date):
    occupied = get_occupied_seats(flight["id"], travel_date)

    seat_types = {
        "A": "Window",
        "B": "Middle",
        "C": "Aisle",
        "D": "Aisle",
        "E": "Middle",
        "F": "Window"
    }

    seat_map = []

    for number in range(1, flight["seats"] + 1):
        row = (number - 1) // 6 + 1
        column = SEAT_COLUMNS[(number - 1) % 6]
        seat_number = f"{row}{column}"

        seat_map.append({
            "number": seat_number,
            "occupied": seat_number in occupied,
            "type": seat_types[column]
        })

    return seat_map


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

        if not username or not email or not password or not confirm_password:
            flash("Please fill in every field.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif email in users:
            flash("An account with this email already exists.", "error")
        else:
            users[email] = {
                "username": username,
                "password": generate_password_hash(password)
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


@app.route("/flights")
@login_required
def home():
    today = date.today().isoformat()
    source = request.args.get("source", "Hyderabad")
    destination = request.args.get("destination", "Delhi")
    travel_date = request.args.get("travel_date", today)
    searched = request.args.get("search") == "1"
    sort_by = request.args.get("sort_by", "recommended")

    matching_flights = []

    if searched:
        if not valid_travel_date(travel_date):
            flash("Choose today or a future travel date.", "error")
            searched = False
        elif source == destination:
            flash("Departure and destination must be different.", "error")
            searched = False
        elif source not in cities or destination not in cities:
            flash("Please choose valid cities.", "error")
            searched = False
        else:
            for flight in flights:
                if (
                    flight["source"] == source
                    and flight["destination"] == destination
                ):
                    available = get_available_seats(flight, travel_date)
                    if available > 0:
                        matching_flights.append({
                            **flight,
                            "available_seats": available
                        })

            if sort_by == "price":
                matching_flights.sort(key=lambda f: f["price"])
            elif sort_by == "departure":
                matching_flights.sort(
                    key=lambda f: departure_times.index(f["departure"])
                )

            if not matching_flights:
                flash("No flights found for this route and date.", "info")

    return render_template(
        "index.html",
        cities=cities,
        flights=matching_flights,
        source=source,
        destination=destination,
        travel_date=travel_date,
        today=today,
        searched=searched,
        sort_by=sort_by
    )


@app.route("/book/<int:flight_id>", methods=["POST"])
@login_required
def book_flight(flight_id):
    flight = find_flight(flight_id)

    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("home"))

    travel_date = request.form.get("travel_date", "").strip()
    passenger = request.form.get("passenger", "").strip()

    if not valid_travel_date(travel_date):
        flash("Choose today or a future travel date.", "error")
        return redirect(url_for("home"))

    if (
        len(passenger) < 2
        or not all(
            char.isalpha() or char.isspace() or char in "-'."
            for char in passenger
        )
    ):
        flash("Enter a valid passenger name.", "error")
        return redirect(url_for(
            "home",
            source=flight["source"],
            destination=flight["destination"],
            travel_date=travel_date,
            search="1"
        ))

    if get_available_seats(flight, travel_date) <= 0:
        flash("This flight has no seats remaining for that date.", "error")
        return redirect(url_for("home"))

    return render_template(
        "seats.html",
        flight=flight,
        travel_date=travel_date,
        passenger=passenger,
        seat_map=make_seat_map(flight, travel_date),
        available_seats=get_available_seats(flight, travel_date)
    )


@app.route("/payment/<int:flight_id>", methods=["POST"])
@login_required
def payment(flight_id):
    flight = find_flight(flight_id)

    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("home"))

    travel_date = request.form.get("travel_date", "").strip()
    passenger = request.form.get("passenger", "").strip()
    seat_number = request.form.get("seat_number", "").strip().upper()

    valid_seats = {
        f"{(n - 1) // 6 + 1}{SEAT_COLUMNS[(n - 1) % 6]}"
        for n in range(1, flight["seats"] + 1)
    }

    if (
        not valid_travel_date(travel_date)
        or not passenger
        or seat_number not in valid_seats
    ):
        flash("Please check your travel details and select a valid seat.", "error")
        return redirect(url_for("home"))

    if seat_number in get_occupied_seats(flight_id, travel_date):
        flash("That seat has already been booked. Please choose another.", "error")
        return render_template(
            "seats.html",
            flight=flight,
            travel_date=travel_date,
            passenger=passenger,
            seat_map=make_seat_map(flight, travel_date),
            available_seats=get_available_seats(flight, travel_date)
        ), 409

    seat_types = {
        "A": "Window", "B": "Middle", "C": "Aisle",
        "D": "Aisle", "E": "Middle", "F": "Window"
    }

    base_fare = flight["price"]
    demo_tax = round(base_fare * 0.05)

    return render_template(
        "payment.html",
        flight=flight,
        travel_date=travel_date,
        passenger=passenger,
        seat_number=seat_number,
        seat_type=seat_types[seat_number[-1]],
        base_fare=base_fare,
        demo_tax=demo_tax,
        total=base_fare + demo_tax
    )


@app.route("/confirm-booking/<int:flight_id>", methods=["POST"])
@login_required
def confirm_booking(flight_id):
    global next_booking_id

    flight = find_flight(flight_id)

    if not flight:
        flash("Flight not found.", "error")
        return redirect(url_for("home"))

    travel_date = request.form.get("travel_date", "").strip()
    passenger = request.form.get("passenger", "").strip()
    seat_number = request.form.get("seat_number", "").strip().upper()

    valid_seats = {
        f"{(n - 1) // 6 + 1}{SEAT_COLUMNS[(n - 1) % 6]}"
        for n in range(1, flight["seats"] + 1)
    }

    if (
        not valid_travel_date(travel_date)
        or not passenger
        or seat_number not in valid_seats
    ):
        flash("Booking details are invalid. Please try again.", "error")
        return redirect(url_for("home"))

    occupied = get_occupied_seats(flight_id, travel_date)

    if seat_number in occupied:
        flash("That seat is no longer available. Please select another.", "error")
        return render_template(
            "seats.html",
            flight=flight,
            travel_date=travel_date,
            passenger=passenger,
            seat_map=make_seat_map(flight, travel_date),
            available_seats=get_available_seats(flight, travel_date)
        ), 409

    occupied.add(seat_number)

    seat_types = {
        "A": "Window", "B": "Middle", "C": "Aisle",
        "D": "Aisle", "E": "Middle", "F": "Window"
    }

    base_fare = flight["price"]
    demo_tax = round(base_fare * 0.05)

    booking = {
        "id": next_booking_id,
        "reference": secrets.token_hex(4).upper(),
        "email": session["user_email"],
        "passenger": passenger,
        "travel_date": travel_date,
        "flight": flight.copy(),
        "seat": seat_number,
        "seat_type": seat_types[seat_number[-1]],
        "base_fare": base_fare,
        "tax": demo_tax,
        "total": base_fare + demo_tax,
        "status": "Confirmed"
    }

    next_booking_id += 1
    bookings.append(booking)

    flash("Demo booking completed successfully!", "success")
    return redirect(url_for("confirmation", booking_id=booking["id"]))


@app.route("/confirmation/<int:booking_id>")
@login_required
def confirmation(booking_id):
    booking = next(
        (
            item for item in bookings
            if item["id"] == booking_id
            and item["email"] == session["user_email"]
        ),
        None
    )

    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for("my_bookings"))

    return render_template("confirmation.html", booking=booking)


@app.route("/my-bookings")
@login_required
def my_bookings():
    user_bookings = [
        item for item in bookings
        if item["email"] == session["user_email"]
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
        None
    )

    if not booking:
        flash("Booking not found.", "error")
    elif booking["status"] == "Cancelled":
        flash("This booking is already cancelled.", "info")
    else:
        get_occupied_seats(
            booking["flight"]["id"],
            booking["travel_date"]
        ).discard(booking["seat"])

        booking["status"] = "Cancelled"
        flash("Booking cancelled. The seat is available again.", "success")

    return redirect(url_for("my_bookings"))


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)
