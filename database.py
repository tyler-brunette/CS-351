##### Functionality Needed from this file #####
# Customer Rewards will need: Customer Card, Free Drink Tracker
# Employee Clock-In will need: Username, Password, Start Time, End Time, Total Time Worked
# Inventory will need: Amount of cups, milk, sugar, coffee grounds, etc
# Manager will need: To be able to view all employee database information, Work Scheduler?
# Barista Order Handler will need: To inset when a customer orders, and delete when the order is completed
###############################################

# Imports for the database to function properly
import datetime
from datetime import datetime
from pymongo import MongoClient

# Permissions for where my account database is stored (anyone can access it)
cluster = MongoClient(
    "mongodb+srv://admin:admin@cs351.nynjvwf.mongodb.net/"
    
)

# Initializing the database in MongoDB
db = cluster["schedule_system"]
customer_collection = db["Customers"]
employee_collection = db["Employees"]
inventory_collection = db["Inventory"]
transaction_collection = db["Transactions"]
scheduler_collection = db["Scheduler"]


# Gets the employee title of a user
def checkEmployeeTitle(name, password):
    for x in employee_collection.find({"username": name, "pass": password}):
        return x.get("title")


# Creates a new employee in the database ############################################################################
def createEmployee(name, password, title):
    # Example use of a customer password reset feature
    post = {
        "username": name,
        "pass": password,
        "title": title,
        "clock_in": "",
        "clock_out": "",
    }
    employee_collection.insert_one(post)


# Runs when the employee logs in to work
def clockIn(name):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    employee_collection.update_one(
        {"username": name}, {"$set": {"clock_in": str(current_time)}}
    )
    employee_collection.update_one({"username": name}, {"$set": {"clock_out": ""}})


# Runs when the employee logs out
def clockOut(name):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    employee_collection.update_one(
        {"username": name}, {"$set": {"clock_out": str(current_time)}}
    )


# Checks transactions on a customer card of a given phone number
def checkCustomerCard(phoneNum):
    for x in customer_collection.find({"phone": phoneNum}):
        return x.get("transactions")
    return 0


# Makes a customer card if one was not found
def createCustomerCard(phoneNum):
    post = {"phone": phoneNum, "transactions": 0}
    customer_collection.insert_one(post)


# Increments the number
def incrementCustomerCard(phoneNum):
    numTransactions = 0
    for x in customer_collection.find({"phone": phoneNum}):
        numTransactions = x.get("transactions")
        customer_collection.update_one(
            {"transactions": numTransactions},
            {"$set": {"transactions": numTransactions + 1}},
        )
    return 0


# Prints all employees in the database
def printEmployees():
    return list(employee_collection.find())


# Prints all transactions in the database
def printTransactions():
    return list(transaction_collection.find())


# Gets the number of transactions in the database
def transactionDatabaseLength():
    return len(list(transaction_collection.find()))


# Purpose: Prints all inventory items in the database
def printInventory():
    return list(inventory_collection.find())


# Prints all incomplete orders in the transaction database
def printBarista():
    return list(transaction_collection.find({"status": "incomplete"}))


# Prints all employee schedules in the scheduler database
def printScheduler():
    return list(scheduler_collection.find())


# Update an order from incomplete to complete
def completeOrder(orderNum):
    orderNumber = {"orderNum": int(orderNum)}
    newStatus = {"$set": {"status": "complete"}}
    transaction_collection.update_one(orderNumber, newStatus)


# Add an order in the transaction database
def completeTransaction(order):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    post = {
        "orderNum": order.get("orderNum"),
        "regular": order.get("coffeeCount"),
        "deluxe": order.get("deluxeCoffeeCount"),
        "donut": order.get("donutCount"),
        "cost": order.get("cost"),
        "time": str(current_time),
        "status": order.get("status"),
    }
    transaction_collection.insert_one(post)


# Update the shop inventory
def updateInventory(orderNum):
    # Get the order from the customer
    orderList = list(transaction_collection.find({"orderNum": int(orderNum)}))
    order = orderList[0]

    regOrder = int(order["regular"])
    delOrder = int(order["deluxe"])
    donutOrder = int(order["donut"])

    # Calculating the amount of ingredients used on the order
    cupsUsed = regOrder + delOrder
    groundsUsed = (regOrder * 2) + (delOrder * 2)
    milkUsed = delOrder * (0.05)

    # Get the shop inventory database
    inventoryList = list(inventory_collection.find())
    inventory = inventoryList[0]

    currentCups = inventory["cups"]
    currentGrounds = inventory["coffee_grounds"]
    currentMilk = inventory["milk"]
    currentDonuts = inventory["donuts"]

    # Calculate the new inventory amounts
    totalCups = currentCups - cupsUsed
    totalGrounds = currentGrounds - groundsUsed
    totalMilk = currentMilk - milkUsed
    totalDonuts = currentDonuts - donutOrder

    # Update the inventory database
    inventory_collection.update_one(
        {"cups": currentCups}, {"$set": {"cups": totalCups}}
    )
    inventory_collection.update_one(
        {"coffee_grounds": currentGrounds}, {"$set": {"coffee_grounds": totalGrounds}}
    )
    inventory_collection.update_one(
        {"milk": currentMilk}, {"$set": {"milk": totalMilk}}
    )
    inventory_collection.update_one(
        {"donuts": currentDonuts}, {"$set": {"donuts": totalDonuts}}
    )
