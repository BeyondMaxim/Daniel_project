from flask import Flask, jsonify, render_template, request
import mysql.connector
import re
from datetime import datetime


def convert_to_24hr(time_str):
    """
    Converts a 12-hour time string to a 24-hour time string.

    Args:
        time_str (str): The time in 12-hour format (e.g. "09:06 AM").

    Returns:
        str: The time in 24-hour format (e.g. "09:06").
    """
    time_obj = datetime.strptime(time_str, "%I:%M %p")
    return time_obj.strftime("%H:%M")


def convert_to_12hr(time_str):
    """
    Converts a 24-hour time string to a 12-hour time string.

    Args:
        time_str (str): The time in 24-hour format (e.g. "20:00").

    Returns:
        str: The time in 12-hour format (e.g. "8:00 PM").
    """
    time_obj = datetime.strptime(time_str, "%H:%M")
    if time_obj.hour > 12:
        return f"{time_obj.hour - 12:02d}:{time_obj.minute:02d} PM"
    elif time_obj.hour == 12:
        return f"{time_obj.hour:02d}:{time_obj.minute:02d} PM"
    else:
        return f"{time_obj.hour:02d}:{time_obj.minute:02d} AM"


app = Flask(__name__)

# MySQL connection settings
username = "root"
# password = "y7ZXqfiALL"
host = "localhost"
database = "sql12713040"

# Establish the connection
cnx = mysql.connector.connect(user=username, host=host, database=database)

# Create a cursor object
cursor = cnx.cursor()


@app.route("/api/countries", methods=["GET"])
def get_countries():
    # Fetch the country column list from the GolfClubs table
    query = "SELECT DISTINCT country FROM GolfClubs"
    cursor.execute(query)
    countries = cursor.fetchall()

    # Convert the result to a list of dictionaries
    country_list = []
    for country in countries:
        country_list.append({"id": country[0], "name": country[0]})

    # Return the list of countries as JSON
    return jsonify(country_list)


@app.route("/api/filter", methods=["GET"])
def get_filter_data():
    filter_kind = request.args.get("filterKind")
    filter_text = request.args.get("filterText")

    if filter_kind == "country":
        query = "SELECT DISTINCT country FROM GolfClubs WHERE country LIKE %s"
        cursor.execute(query, (f"%{filter_text}%",))
    elif filter_kind == "state":
        query = "SELECT DISTINCT state FROM GolfClubs WHERE state LIKE %s"
        cursor.execute(query, (f"%{filter_text}%",))
    elif filter_kind == "suburb":
        query = "SELECT DISTINCT suburb FROM GolfClubs WHERE suburb LIKE %s"
        cursor.execute(query, (f"%{filter_text}%",))
    elif filter_kind == "postal_code":
        query = "SELECT DISTINCT postcode FROM GolfClubs WHERE postcode LIKE %s"
        cursor.execute(query, (f"%{filter_text}%",))
    else:
        return jsonify([])

    data = cursor.fetchall()

    return jsonify([{"id": row[0], "name": row[0]} for row in data])


@app.route("/filter_main", methods=["POST"])
def get_filter_clubs():
    if request.method == "POST":
        date = request.form.get("date")
        main_filter = request.form.get("main_filter")
        main_filter_input = request.form.get("main_filter_input")

        # Get the hole_id that have the same date as the input date
        cursor.execute("SELECT DISTINCT hole_id FROM Bookings WHERE date = %s", (date,))
        hole_ids = [row[0] for row in cursor.fetchall()]
        golf_clubs_data = []
        if not hole_ids:

            return jsonify(golf_clubs_data)
        # Get the club_id based on the hole_ids
        cursor.execute(
            "SELECT DISTINCT golf_club_id FROM Holes WHERE id IN ({})".format(
                ",".join(["%s"] * len(hole_ids))
            ),
            tuple(hole_ids),
        )
        club_ids = [row[0] for row in cursor.fetchall()]
        if main_filter == "postal_code":
            cursor.execute(
                "SELECT * FROM GolfClubs WHERE id IN ({}) AND postcode = %s".format(
                    ",".join(["%s"] * len(club_ids))
                ),
                tuple(club_ids) + (main_filter_input,),
            )
            golf_clubs = cursor.fetchall()

        elif main_filter == "state":
            cursor.execute(
                "SELECT * FROM GolfClubs WHERE id IN ({}) AND state = %s".format(
                    ",".join(["%s"] * len(club_ids))
                ),
                tuple(club_ids) + (main_filter_input,),
            )
            golf_clubs = cursor.fetchall()

        elif main_filter == "suburb":
            cursor.execute(
                "SELECT * FROM GolfClubs WHERE id IN ({}) AND suburb = %s".format(
                    ",".join(["%s"] * len(club_ids))
                ),
                tuple(club_ids) + (main_filter_input,),
            )
            golf_clubs = cursor.fetchall()

        elif main_filter == "course_name":
            # Get the golf club information based on the club_ids
            cursor.execute(
                "SELECT * FROM GolfClubs WHERE id IN ({}) AND club_name = %s".format(
                    ",".join(["%s"] * len(club_ids))
                ),
                tuple(club_ids) + (main_filter_input,),
            )
            golf_clubs = cursor.fetchall()

        # Convert the golf club data to a list of dictionaries

        for row in golf_clubs:
            golf_club = {
                "club_id": row[0],
                "club_name": row[1],
                "course_name": row[2],
                "address": row[3],
                "country": row[4],
                "state": row[5],
                "suburb": row[6],
                "postcode": row[7],
                "latitude": row[8],
                "longitude": row[9],
                "phone": row[10],
                "email": row[11],
                "golf_cart": row[12],
                "club_hire": row[13],
                "platform": row[14],
                "booking_link": row[15],
                "9_holes": row[16],
                "18_holes": row[17],
            }
            golf_clubs_data.append(golf_club)
        # Return the golf club data as a JSON response
        return jsonify(golf_clubs_data)
        # Process the data here
        # For example, you can use the data to filter a database query
        # or perform some other operation based on the input data
        print(
            f"date: {date}, main_filter: {main_filter}, main_filter_input: {main_filter_input}"
        )
        return "Data received successfully"


# Define a route for the /golf-clubs endpoint
@app.route("/api/golf-clubs", methods=["GET"])
def get_golf_clubs():

    query = "SELECT * FROM GolfClubs"
    cursor.execute(query)
    golf_clubs = cursor.fetchall()

    # Convert the data to a JSON response
    golf_clubs_json = []
    for golf_club in golf_clubs:
        golf_clubs_json.append(
            {
                "club_id": golf_club[0],
                "club_name": golf_club[1],
                "course_name": golf_club[2],
                "address": golf_club[3],
                "country": golf_club[4],
                "state": golf_club[5],
                "suburb": golf_club[6],
                "postcode": golf_club[7],
                "latitude": golf_club[8],
                "longitude": golf_club[9],
                "phone": golf_club[10],
                "email": golf_club[11],
                "golf_cart": golf_club[12],
                "club_hire": golf_club[13],
                "platform": golf_club[14],
                "booking_link": golf_club[15],
                "9_holes": golf_club[16],
                "18_holes": golf_club[17],
            }
        )

    return jsonify(golf_clubs_json)


@app.route("/api/initial_input_set", methods=["GET"])
def initial_set():

    date = request.args.get("date")
    trIds = request.args.get("trIds")
    trId_list = [int(x.split("-")[1]) for x in trIds.split(",") if x.startswith("row-")]
    # Filter the golf_clubs table based on the trId_list

    cursor.execute(
        "SELECT * FROM Holes WHERE golf_club_id IN ({})".format(
            ",".join(["%s"] * len(trId_list))
        ),
        tuple(trId_list),
    )

    hole_ids = [row[0] for row in cursor.fetchall()]
    # Query to get the minimum and maximum values in the price and time columns

    cursor.execute(
        "SELECT MIN(price) AS min_price,  MAX(price) AS max_price FROM Bookings WHERE  hole_id IN ({}) AND date = %s".format(
            ",".join(["%s"] * len(hole_ids))
        ),
        tuple(hole_ids) + (date,),
    )

    # Fetch the results
    results = cursor.fetchall()

    # Print the results
    for row in results:
        min_price = row[0]
        max_price = row[1]

    cursor.execute(
        "SELECT time AS max_price FROM Bookings WHERE  hole_id IN ({}) AND date = %s".format(
            ",".join(["%s"] * len(hole_ids))
        ),
        tuple(hole_ids) + (date,),
    )
    results = cursor.fetchall()
    index = 0
    row_time = []
    for row in results:
        index += 1
        time = row[0]
        new_time = re.sub(
            r"(\d{1,2}):(\d{1,2})(\s*am|\s*pm|\s*Am|\s*Pm|\s*AM|\s*PM)",
            lambda x: f"{x.group(1).zfill(2)}:{x.group(2).zfill(2)} {x.group(3).capitalize()}",
            time,
        )
        new_time = convert_to_24hr(new_time)
        row_time.append(new_time)
    min_time = min(row_time)
    max_time = max(row_time)
    # min_time = convert_to_12hr(min_time)
    # max_time = convert_to_12hr(max_time)
    data = {
        "min_time": min_time,
        "max_time": max_time,
        "min_price": min_price,
        "max_price": max_price,
    }
    return jsonify(data)


# Define a route for the /golf-clubs endpoint
@app.route("/filter_more", methods=["GET"])
def get_golf_more():
    date = request.args.get("date")
    filterHoleType = request.args.get("filterHoleType")
    filterGolfers = request.args.get("filterGolfers")
    startPrice = request.args.get("startPrice")
    endPrice = request.args.get("endPrice")
    startTimeValue = request.args.get("startTimeValue")
    endTimeValue = request.args.get("endTimeValue")
    trIds = request.args.get("trIds")
    filterKind = request.args.get("filterKind")
    filterText = request.args.get("filterText")

    # Get the hole_id that have the same date as the input date
    cursor.execute("SELECT DISTINCT hole_id FROM Bookings WHERE date = %s", (date,))
    hole_ids = [row[0] for row in cursor.fetchall()]

    golf_clubs_data = []
    if not hole_ids:
        return jsonify(golf_clubs_data)
    # Get the club_id based on the hole_ids
    cursor.execute(
        "SELECT DISTINCT golf_club_id FROM Holes WHERE id IN ({})".format(
            ",".join(["%s"] * len(hole_ids))
        ),
        tuple(hole_ids),
    )
    club_ids = [row[0] for row in cursor.fetchall()]
    print(f"filterKind: {filterKind}, filterText:{filterText}")
    if filterKind == "postal_code":
        cursor.execute(
            "SELECT * FROM GolfClubs WHERE id IN ({}) AND postcode = %s".format(
                ",".join(["%s"] * len(club_ids))
            ),
            tuple(club_ids) + (filterText,),
        )
        golf_clubs = cursor.fetchall()
    elif filterKind == "state":
        print("+++++++++++++++++++++++")
        cursor.execute(
            "SELECT * FROM GolfClubs WHERE id IN ({}) AND state = %s".format(
                ",".join(["%s"] * len(club_ids))
            ),
            tuple(club_ids) + (filterText,),
        )
        golf_clubs = cursor.fetchall()
    elif filterKind == "suburb":
        cursor.execute(
            "SELECT * FROM GolfClubs WHERE id IN ({}) AND suburb = %s".format(
                ",".join(["%s"] * len(club_ids))
            ),
            tuple(club_ids) + (filterText,),
        )
        golf_clubs = cursor.fetchall()
    elif filterKind == "course_name":
        # Get the golf club information based on the club_ids
        cursor.execute(
            "SELECT * FROM GolfClubs WHERE id IN ({}) AND club_name = %s".format(
                ",".join(["%s"] * len(club_ids))
            ),
            tuple(club_ids) + (filterText,),
        )
        golf_clubs = cursor.fetchall()

    club_ids = [row[0] for row in golf_clubs]
    print("==========================")
    print(club_ids)
    trId_list = [int(x.split("-")[1]) for x in trIds.split(",") if x.startswith("row-")]
    # Filter the golf_clubs table based on the trId_list
    if filterHoleType:
        cursor.execute(
            "SELECT * FROM Holes WHERE golf_club_id IN ({}) AND hole_type = %s".format(
                ",".join(["%s"] * len(club_ids))
            ),
            tuple(club_ids) + (filterHoleType,),
        )
    else:
        cursor.execute(
            "SELECT * FROM Holes WHERE golf_club_id IN ({})".format(
                ",".join(["%s"] * len(club_ids))
            ),
            tuple(club_ids),
        )

    hole_ids = [row[0] for row in cursor.fetchall()]
    print(hole_ids)
    # Query to get the minimum and maximum values in the price and time columns
    if filterGolfers:
        # Query to get the minimum and maximum values in the price and time columns
        cursor.execute(
            "SELECT * FROM Bookings WHERE  hole_id IN ({}) AND date = %s AND golfers >= %s AND (price >= %s AND price <= %s)".format(
                ",".join(["%s"] * len(hole_ids))
            ),
            tuple(hole_ids) + (date, filterGolfers, startPrice, endPrice),
        )
    else:
        cursor.execute(
            "SELECT * FROM Bookings WHERE  hole_id IN ({}) AND date = %s  AND (price >= %s AND price <= %s) ".format(
                ",".join(["%s"] * len(hole_ids))
            ),
            tuple(hole_ids) + (date, startPrice, endPrice),
        )

    # Fetch the results
    results = cursor.fetchall()
    print(results)
    print(len(results))
    result = []
    for row in results:
        if row[1] in result:
            continue
        time = row[3]
        new_time = re.sub(
            r"(\d{1,2}):(\d{1,2})(\s*am|\s*pm|\s*Am|\s*Pm|\s*AM|\s*PM)",
            lambda x: f"{x.group(1).zfill(2)}:{x.group(2).zfill(2)} {x.group(3).capitalize()}",
            time,
        )
        new_time = convert_to_24hr(new_time)
        if new_time >= startTimeValue and new_time <= endTimeValue:
            result.append(row[1])

    hole_ids = [row for row in result]
    golf_clubs_data = []
    if not hole_ids:

        return jsonify(golf_clubs_data)
    # Get the club_id based on the hole_ids
    cursor.execute(
        "SELECT DISTINCT golf_club_id FROM Holes WHERE id IN ({})".format(
            ",".join(["%s"] * len(hole_ids))
        ),
        tuple(hole_ids),
    )
    club_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute(
        "SELECT * FROM GolfClubs WHERE id IN ({})".format(
            ",".join(["%s"] * len(club_ids))
        ),
        tuple(club_ids),
    )
    golf_clubs = cursor.fetchall()

    # Convert the golf club data to a list of dictionaries
    for row in golf_clubs:
        golf_club = {
            "club_id": row[0],
            "club_name": row[1],
            "course_name": row[2],
            "address": row[3],
            "country": row[4],
            "state": row[5],
            "suburb": row[6],
            "postcode": row[7],
            "latitude": row[8],
            "longitude": row[9],
            "phone": row[10],
            "email": row[11],
            "golf_cart": row[12],
            "club_hire": row[13],
            "platform": row[14],
            "booking_link": row[15],
            "9_holes": row[16],
            "18_holes": row[17],
        }
        golf_clubs_data.append(golf_club)
    # Return the golf club data as a JSON response
    return jsonify(golf_clubs_data)


@app.route("/api/filter_hole", methods=["GET"])
def get_holes():
    date = request.args.get("date")
    filterHoleType = request.args.get("filterHoleType")
    filterGolfers = request.args.get("filterGolfers")
    startPrice = request.args.get("startPrice")
    endPrice = request.args.get("endPrice")
    startTimeValue = request.args.get("startTimeValue")
    endTimeValue = request.args.get("endTimeValue")
    rowId = request.args.get("rowId")

    cursor.execute("SELECT club_name FROM GolfClubs WHERE id  = %s", (rowId,))
    club_name = cursor.fetchone()

    if filterHoleType:
        cursor.execute(
            "SELECT * FROM Holes WHERE golf_club_id  = %s AND hole_type = %s",
            (rowId, filterHoleType),
        )
    else:
        cursor.execute(
            "SELECT * FROM Holes WHERE golf_club_id  = %s ",
            (rowId,),
        )

    hole_ids = [row[0] for row in cursor.fetchall()]

    if filterGolfers:
        # Query to get the minimum and maximum values in the price and time columns
        cursor.execute(
            "SELECT * FROM Bookings WHERE  hole_id IN ({}) AND date = %s AND golfers >= %s AND (price >= %s AND price <= %s)".format(
                ",".join(["%s"] * len(hole_ids))
            ),
            tuple(hole_ids) + (date, filterGolfers, startPrice, endPrice),
        )
    else:
        cursor.execute(
            "SELECT * FROM Bookings WHERE  hole_id IN ({}) AND date = %s  AND (price >= %s AND price <= %s) ".format(
                ",".join(["%s"] * len(hole_ids))
            ),
            tuple(hole_ids) + (date, startPrice, endPrice),
        )

    # Fetch the results
    results = cursor.fetchall()

    result = []
    for row in results:
        time = row[3]
        new_time = re.sub(
            r"(\d{1,2}):(\d{1,2})(\s*am|\s*pm|\s*Am|\s*Pm|\s*AM|\s*PM)",
            lambda x: f"{x.group(1).zfill(2)}:{x.group(2).zfill(2)} {x.group(3).capitalize()}",
            time,
        )
        new_time = convert_to_24hr(new_time)
        if new_time >= startTimeValue and new_time <= endTimeValue:
            cursor.execute("SELECT hole_name FROM Holes WHERE id  = %s", (row[1],))
            hole_name = cursor.fetchone()
            result.append((convert_to_12hr(new_time), hole_name, row[4], row[5]))

    hols_json = []
    for golf_club in result:
        hols_json.append(
            {
                "time": golf_club[0],
                "hole_name": golf_club[1],
                "available_golfers": golf_club[2],
                "price": golf_club[3],
            }
        )

    data = {}
    data["club_name"] = club_name
    data["result"] = hols_json
    return jsonify(data)


@app.route("/")
def first_page():
    """
    Renders the index.html template.

    Returns:
        The rendered HTML template.
    """
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
