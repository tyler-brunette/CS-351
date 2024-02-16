# Imports for the backend to function properly
from datetime import datetime as dt  # Rename datetime to dt
from gevent import monkey

# Needed for Flask's implementation for Socket.IO
monkey.patch_all()

from flask import Flask, render_template, request, redirect, make_response, jsonify
import database as DB
from flask_socketio import SocketIO, emit
import json

# Define the Flask instance
app = Flask(__name__)

# Set the secret key for the socketIO config
app.config["SECRET_KEY"] = "secret!"

# Connect the Flask instance to be used by SocketIO
socketIO = SocketIO(app)


# When the user first joins the server, they will be redirected to the login screen
@app.route("/")
def home():
    return redirect("/login")


# The login page for accessing the application
@app.route("/login", methods=["GET", "POST"])
def login():
    # If the user is trying to log in, their client will send a POST request with the credentials
    if request.method == "POST":
        # Credentials
        username = request.form.get("username")
        password = request.form.get("password")

        # Call database, which returns the type of the user
        userType = DB.checkEmployeeTitle(username, password)

        # If the user type is invalid, login was invalid
        if userType == None:
            errorMsg = "ERROR: Invalid login! Please try again."
            return render_template("login.html", error=errorMsg)
        else:
            # Response to be returned to the client (set up later)
            response = None

            # Switch to redirect based on the user type
            if userType == "Manager":
                response = make_response(redirect("/manager"))
            elif userType == "Staff":
                response = make_response(redirect("/scheduler"))

            if response == None:
                errorMsg = "ERROR: Invalid login! Please try again."
                return render_template("login.html", error=errorMsg)

            # Set the username cookie for the user for logging in and out
            response.set_cookie("Role", userType)

            # Send the response to the client
            return response

    else:
        # If the user is simply visiting the page (GET method), show them the login page
        return render_template("login.html")


# This route is for log out buttons. It will clock out the user and redirect to the log in page
@app.route("/logout", methods=["GET"])
def logout():
    # Get the username of the user
    response = None
    response = make_response(redirect("/login"))
    response.delete_cookie("Role")

    # Redirect to the login screen
    return response


# Dashboard for the manager to access their different pages
@app.route("/manager", methods=["GET"])
def managerDashboard():
    role = request.cookies.get("Role")

    if (role == "Manager"):
        # Show the manager dashboard
        return render_template("manager.html")
    else:
        return redirect("/logout")


# Page for viewing all employee details
@app.route("/employeeDashboard", methods=["GET", "POST"])
def employeeDashboard():
    # Get details of all employees from the database to be displayed
    allEmployees = DB.printEmployees()

    # There is no POST request for this endpoint
    # Display the employee details page and pass along employee details
    return render_template("employeeDetails.html", allEmployees=allEmployees)

@app.route("/addEmployee", methods=["GET", "POST"])
def addEmployee():
    if request.method == "POST":
        name = request.form.get('name')
        password = request.form.get('pass')
        role = request.form.get('role') 
        
        DB.createEmployee(name, password, role)
    return redirect("/employeeDashboard")

@app.route("/removeEmployee", methods=["GET", "POST"])
def removeEmployee():
    if request.method == "POST":
        name = request.form.get('name')
        
        DB.removeEmployee(name)
    return redirect("/employeeDashboard")


# Page for viewing employee schedules
@app.route("/scheduler", methods=["GET", "POST"])
def schedulerDashboard():
    # Get details of all employees from the database to be displayed
    allEmployees = DB.printEmployees()
    schedules = DB.printScheduler()
    for shift in schedules:
        start_time = dt.strptime(shift['startTime'], '%H:%M').strftime('%I:%M %p')
        end_time = dt.strptime(shift['endTime'], '%H:%M').strftime('%I:%M %p')
        shift['startTime'] = start_time
        shift['endTime'] = end_time

    # There is no POST request for this endpoint
    # Display the employee schedule page and pass along employee and schedule details
    return render_template(
        "scheduler.html", allEmployees=allEmployees, schedules=schedules
    )

@app.route("/updateShift", methods=["GET", "POST"])
def updateShift():
    if request.method == "POST":
        username = request.form.get('username')
        day = request.form.get('day')
        start_time = request.form.get('startTime')
        end_time = request.form.get('endTime') 
        
        DB.updateShift(username, day, start_time, end_time)
    
    return redirect("/scheduler")


@app.route("/deleteShift", methods=["GET", "POST"])
def deleteShift():
    if request.method == "POST":
        username = request.form.get('username')
        day = request.form.get('day')
        
        DB.deleteShift(username, day)
    
    return redirect("/scheduler")


# Start the Flask web server using sockets
if __name__ == "__main__":
    socketIO.run(app)
