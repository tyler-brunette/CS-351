# Imports for the backend to function properly
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
            elif userType == "Barista":
                response = make_response(redirect("/barista"))
            elif userType == "Cashier":
                response = make_response(redirect("/cashier"))

            # Set the username cookie for the user for logging in and out
            response.set_cookie("Username", username)

            # Automatically clock-in the user as they log in
            DB.clockIn(username)

            # Send the response to the client
            return response

    else:
        # If the user is simply visiting the page (GET method), show them the login page
        return render_template("login.html")


# This route is for log out buttons. It will clock out the user and redirect to the log in page
@app.route("/logout", methods=["GET"])
def logout():
    # Get the username of the user
    username = request.cookies.get("Username")

    # Clock out the user
    DB.clockOut(username)

    # Redirect to the login screen
    return redirect("/login")


# Dashboard for the manager to access their different pages
@app.route("/manager", methods=["GET"])
def managerDashboard():
    # Show the manager dashboard
    return render_template("manager.html")


# The default page for the cashier is the menu for placing an order
@app.route("/cashier", methods=["GET", "POST"])
def cashierDashboard():
    # If the cashier is submitting an order, calculate the total price
    if request.method == "POST":
        # Tally the items
        coffee_count = request.form.get("coffee")
        deluxe_coffee_count = request.form.get("deluxe_coffee")
        donut_count = request.form.get("donuts")

        # Transaction number is simply (total number of transactions + 1)
        transactionNum = DB.transactionDatabaseLength()

        # The user will be redirected to the rewards step of the transaction after cookies are set
        response = make_response(redirect("/rewards"))

        # Cost of items for calculating total
        costs = {"coffeeCost": 1.00, "deluxeCoffeeCost": 2.00, "donutCost": 2.50}

        # The order object that will be placed into a cookie for better client-side processing
        order = {
            "orderNum": transactionNum,
            "coffeeCount": coffee_count,
            "deluxeCoffeeCount": deluxe_coffee_count,
            "donutCount": donut_count,
            "cost": (int(coffee_count) * costs.get("coffeeCost"))
            + (int(deluxe_coffee_count) * costs.get("deluxeCoffeeCost"))
            + (int(donut_count) * costs.get("donutCost")) * 1.06,
            "status": "incomplete",
        }

        # Place the order object into a client cookie
        response.set_cookie("Order", json.dumps(order))

        # Send the response to the client
        return response
    else:
        # If the user is visiting the cashier page

        # After cookies are set, the cashier menu page will be displayed
        response = make_response(render_template("cashier.html"))

        # Clear cookies from previous orders if present
        response.set_cookie("RewardDiscount", "", expires=0)
        response.set_cookie("Order", "", expires=0)

        # Send the response to the client
        return response


# The rewards step of the order submission process is asking for a phone number
@app.route("/rewards", methods=["GET", "POST"])
def rewardsDashboard():
    # If the user is submitting a phone number for validation
    if request.method == "POST":
        # Get the phone number from the POST request
        rewards_number = request.form.get("phone")

        # When the phone number is processed, the client will be redirected to the payment screen
        response = make_response(redirect("/payment"))

        # Get the number of transactions the customer has completed, based on the phone number
        customer_transactions = DB.checkCustomerCard(rewards_number)

        # Increment the number of transactions completed
        # Done in this step to limit the number of cookies stored by the user
        DB.incrementCustomerCard(rewards_number)

        # Set the cookie containing whether or not the customer has earned their rewards
        response.set_cookie(
            # Every fifth transaction is a free coffee (a dollar off total)
            "RewardDiscount",
            str(((customer_transactions + 1) % 5) == 0),
        )

        # Send the response to the client
        return response

    else:
        # If the user is visiting the page, show the rewards page
        return render_template("rewards.html")


# The payment step of the order submission process
# Allows cash or card. Both are simulated and care not stored
@app.route("/payment", methods=["GET", "POST"])
def paymentDashboard():
    # If the user is submitting an order
    if request.method == "POST":
        # Get the order as a JSON object from the client
        order = json.loads(request.cookies.get("Order"))

        # Put the order into the database
        DB.completeTransaction(order)

        # Order is submitted, send the user back to cashier main page to start a new transaction
        return redirect("/cashier")
    else:
        # Show the user the payment page
        return render_template("payment.html")


# Renders the inventory dashboard when a request is received
@app.route("/inventory", methods=["GET", "POST"])
def inventoryDashboard():
    inventory = DB.printInventory()
    if request.method == "POST":
        print("This is a post request from Inventory")
        return render_template("inventory.html")
    else:
        return render_template("inventory.html", inventory=inventory)


# The default page for the barista with a list of incomplete order
@app.route("/barista", methods=["GET"])
def baristaDashboard():
    # Get a list of incomplete orders to send to the client
    incompleteOrders = DB.printBarista()

    # There is no POST request for this endpoint (see next route for details)
    # Display the barista main page and pass along data about all transactions
    return render_template("barista.html", allTransactions=incompleteOrders)


# The POST endpoint for marking an order as complete using it's order number
@app.route("/barista/<orderNumber>", methods=["POST"])
def update_order(orderNumber):
    # Complete the order with the given order number
    DB.completeOrder(orderNumber)

    # Update the inventory to remove materials used in the given order
    DB.updateInventory(orderNumber)

    # Return a message to the client that the order was successfully updated
    return jsonify({"message": f"Order {orderNumber} updated successfully"})


# Page for viewing a history of past transactions
@app.route("/transactionHistory", methods=["GET"])
def transactionHistoryDashboard():
    # Get all the transactions from the database
    allTransactions = DB.printTransactions()

    # There is no POST request for this endpoint
    # Display the transaction history page and pass along data about all transactions
    return render_template("transactionHistory.html", allTransactions=allTransactions)


# Page for viewing all employee details
@app.route("/employeeDashboard", methods=["GET", "POST"])
def employeeDashboard():
    # Get details of all employees from the database to be displayed
    allEmployees = DB.printEmployees()

    # There is no POST request for this endpoint
    # Display the employee details page and pass along employee details
    return render_template("employeeDetails.html", allEmployees=allEmployees)


# Page for viewing employee schedules
@app.route("/scheduler", methods=["GET", "POST"])
def schedulerDashboard():
    # Get details of all employees from the database to be displayed
    allEmployees = DB.printEmployees()

    # Get details of all schedules from the database to be displayed
    schedules = DB.printScheduler()

    # There is no POST request for this endpoint
    # Display the employee schedule page and pass along employee and schedule details
    return render_template(
        "scheduler.html", allEmployees=allEmployees, schedules=schedules
    )


# Reflection point for the cashier sending a new order to be received by the barista
@socketIO.on("newOrder")
def authConnection(order):
    emit("newOrder", order, broadcast=True)


# Start the Flask web server using sockets
if __name__ == "__main__":
    socketIO.run(app)
