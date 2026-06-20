from flask import Flask, render_template, request, redirect, session, make_response
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import csv
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================
# WELCOME PAGE
# ==========================
@app.route("/")
def welcome():

    if "user_id" in session:
        return redirect("/search")

    return render_template("welcome.html")


# ==========================
# HOME PAGE - SEARCH BUSES
# ==========================
@app.route("/search", methods=["GET", "POST"])
def search():

    if "user_id" not in session:
        return redirect("/login")

    buses = []
    travel_date = ""

    if request.method == "POST":

        from_city = request.form["from_city"].strip().upper()
        to_city = request.form["to_city"].strip().upper()
        travel_date = request.form["travel_date"]

        conn = get_db()

        all_buses = conn.execute(
            "SELECT * FROM buses"
        ).fetchall()

        for bus in all_buses:

            route = [bus["from_city"].strip().upper()]

            if bus["stops"]:
                route.extend(
                    [stop.strip().upper() for stop in bus["stops"].split(",")]
                )

            route.append(bus["to_city"].strip().upper())

            if from_city in route and to_city in route:

                if route.index(from_city) < route.index(to_city):

                    booked = conn.execute(
                        """
                        SELECT COUNT(*) AS count
                        FROM bookings
                        WHERE bus_id=? AND travel_date=?
                        """,
                        (bus["id"], travel_date)
                    ).fetchone()

                    available_seats = bus["seats"] - booked["count"]

                    bus_dict = dict(bus)
                    bus_dict["available_seats"] = available_seats

                    buses.append(bus_dict)

        conn.close()

    return render_template(
        "index.html",
        buses=buses,
        travel_date=travel_date
    )


# ==========================
# BOOK BUS
# ==========================
@app.route("/book/<int:bus_id>", methods=["GET", "POST"])
def book(bus_id):
    if "user_id" not in session:
        return redirect("/login")
    travel_date = request.args.get("date")

    if not travel_date:
        return redirect("/search")

    conn = get_db()

    bus = conn.execute(
        "SELECT * FROM buses WHERE id=?",
        (bus_id,)
    ).fetchone()

    booked_rows = conn.execute(
        """
        SELECT seat_no
        FROM bookings
        WHERE bus_id=? AND travel_date=?
        """,
        (bus_id, travel_date)
    ).fetchall()

    booked = [row["seat_no"] for row in booked_rows]

    if request.method == "POST":

        name = request.form["name"]
        seat_no = int(request.form["seat_no"])
        user_id = session.get("user_id")
        from_city = request.form["from_city"]
        to_city = request.form["to_city"]
        travel_date = request.form["travel_date"]
        
        # Prevent duplicate booking
        existing = conn.execute(
            """
            SELECT *
            FROM bookings
            WHERE bus_id=? AND seat_no=? AND travel_date=?
            """,
            (bus_id, seat_no, travel_date)
        ).fetchone()

        if existing:
            conn.close()
            return "Seat already booked!"

        conn.execute(
            """
            INSERT INTO bookings
            (
                name,
                bus_id,
                seat_no,
                from_city,
                to_city,
                travel_date,
                user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                bus_id,
                seat_no,
                from_city,
                to_city,
                travel_date,
                user_id
            )
        )

        conn.commit()

        bus_name = bus["bus_name"]

        conn.close()

        return render_template(
            "success.html",
            name=name,
            bus_name=bus_name,
            seat_no=seat_no,
            from_city=from_city,
            to_city=to_city,
            travel_date=travel_date
        )


    conn.close()

    return render_template(
        "booking.html",
        bus=bus,
        travel_date=travel_date,
        booked=booked
    )


# ==========================
# ADMIN LOGIN
# ==========================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        admin = conn.execute(
            """
            SELECT *
            FROM admins
            WHERE username=? AND password=?
            """,
            (username, password)
        ).fetchone()

        conn.close()

        if admin:
            session["admin"] = username
            return redirect("/admin")

        return "❌ Invalid Username or Password"

    return render_template("admin_login.html")

# ==========================
# USER SIGNUP
# ==========================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        existing = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing:
            conn.close()
            return "Email already registered!"

        conn.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")

# ==========================
# USER LOGIN
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email=? AND password=?
            """,
            (email, password)
        ).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/search")

        return "❌ Invalid Email or Password"

    return render_template("login.html")

# ==========================
# USER LOGOUT
# ==========================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ==========================
# ADMIN PANEL
# ==========================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    
    if "admin" not in session:
        return redirect("/admin-login")


    if request.method == "POST":

        bus_name = request.form["bus_name"]
        from_city = request.form["from_city"].strip().upper()
        to_city = request.form["to_city"].strip().upper()
        time = request.form["time"]
        seats = int(request.form["seats"])
        stops = request.form["stops"].strip().upper()

        conn = get_db()

        conn.execute(
            """
            INSERT INTO buses
            (
                bus_name,
                from_city,
                to_city,
                time,
                seats,
                stops
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                bus_name,
                from_city,
                to_city,
                time,
                seats,
                stops
            )
        )

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("admin.html")


# ==========================
# VIEW BOOKINGS
# ==========================
@app.route("/admin/bookings")
def view_bookings():
    
    if "admin" not in session:
        return redirect("/admin-login")
    conn = get_db()

    bookings = conn.execute(
        """
        SELECT
            bk.name,
            bk.seat_no,
            bk.travel_date,
            bk.from_city,
            bk.to_city,
            b.bus_name
        FROM bookings bk
        JOIN buses b
        ON bk.bus_id = b.id
        ORDER BY bk.travel_date DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "view_bookings.html",
        bookings=bookings
    )


# ==========================
# EXPORT BOOKINGS CSV
# ==========================
@app.route("/admin/export-bookings")
def export_bookings():

    if "admin" not in session:
        return redirect("/admin-login")

    conn = get_db()

    bookings = conn.execute(
        """
        SELECT
            bk.name,
            b.bus_name,
            bk.from_city,
            bk.to_city,
            bk.seat_no,
            bk.travel_date
        FROM bookings bk
        JOIN buses b
        ON bk.bus_id = b.id
        ORDER BY bk.travel_date DESC
        """
    ).fetchall()

    conn.close()

    csv_data = "Passenger Name,Bus Name,From,To,Seat No,Travel Date\n"

    for booking in bookings:
        csv_data += (
            f"{booking['name']},"
            f"{booking['bus_name']},"
            f"{booking['from_city']},"
            f"{booking['to_city']},"
            f"{booking['seat_no']},"
            f"{booking['travel_date']}\n"
        )

    response = make_response(csv_data)

    response.headers["Content-Disposition"] = "attachment; filename=bookings.csv"
    response.headers["Content-Type"] = "text/csv"

    return response

# ==========================
# CLEAR BOOKINGS
# ==========================
@app.route("/admin/clear_bookings")
def clear_bookings():

    if "admin" not in session:
        return redirect("/admin-login")
    conn = get_db()

    conn.execute("DELETE FROM bookings")

    conn.commit()
    conn.close()

    return redirect("/admin/bookings")


# ==========================
# MANAGE ROUTES
# ==========================
@app.route("/admin/routes")
def manage_routes():
    
    if "admin" not in session:
        return redirect("/admin-login")
    conn = get_db()

    buses = conn.execute(
        """
        SELECT *
        FROM buses
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "routes.html",
        buses=buses
    )


# ==========================
# DELETE BUS ROUTE
# ==========================
@app.route("/admin/delete_bus/<int:bus_id>")
def delete_bus(bus_id):

    if "admin" not in session:
        return redirect("/admin-login")

    conn = get_db()

    conn.execute(
        "DELETE FROM bookings WHERE bus_id=?",
        (bus_id,)
    )

    conn.execute(
        "DELETE FROM buses WHERE id=?",
        (bus_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/routes")

# ==========================
# ADMIN LOGOUT
# ==========================
@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect("/admin-login")



# ==========================
# MY BOOKINGS
# ==========================
@app.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    bookings = conn.execute(
        """
        SELECT
            bk.*,
            b.bus_name
        FROM bookings bk
        JOIN buses b
        ON bk.bus_id = b.id
        WHERE bk.user_id = ?
        ORDER BY bk.travel_date ASC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )

# ==========================
# CANCEL BOOKING
# ==========================
@app.route("/cancel-booking/<int:booking_id>")
def cancel_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    booking = conn.execute(
        """
        SELECT *
        FROM bookings
        WHERE id=? AND user_id=?
        """,
        (
            booking_id,
            session["user_id"]
        )
    ).fetchone()

    if booking:

        conn.execute(
            """
            DELETE FROM bookings
            WHERE id=?
            """,
            (booking_id,)
        )

        conn.commit()

    conn.close()

    return redirect("/my-bookings")

# ==========================
# DOWNLOAD TICKET PDF
# ==========================
@app.route("/ticket/<int:booking_id>")
def download_ticket(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    booking = conn.execute(
        """
        SELECT
            bk.*,
            b.bus_name
        FROM bookings bk
        JOIN buses b
        ON bk.bus_id = b.id
        WHERE bk.id=? AND bk.user_id=?
        """,
        (booking_id, session["user_id"])
    ).fetchone()

    conn.close()

    if not booking:
        return "Ticket not found!"

    filename = f"ticket_{booking_id}.pdf"

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("🚌 Bus Booking Ticket", styles["Title"])
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(f"Passenger Name: {booking['name']}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"Bus Name: {booking['bus_name']}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"Seat Number: {booking['seat_no']}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"From: {booking['from_city']}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"To: {booking['to_city']}", styles["Normal"])
    )

    elements.append(
        Paragraph(f"Travel Date: {booking['travel_date']}", styles["Normal"])
    )

    doc.build(elements)

    with open(filename, "rb") as pdf:
        response = make_response(pdf.read())

    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f"attachment; filename={filename}"
    )

    return response

# ==========================
# TEST DATABASE
# ==========================
@app.route("/test")
def test():

    conn = get_db()

    buses = conn.execute(
        "SELECT * FROM buses"
    ).fetchall()

    conn.close()

    result = ""

    for bus in buses:
        result += f"{dict(bus)}<br><br>"

    return result


# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    app.run(debug=True)