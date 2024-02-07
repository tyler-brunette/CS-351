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
employee_collection = db["Employees"]
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
    }
    employee_collection.insert_one(post)


# Prints all employees in the database
def printEmployees():
    return list(employee_collection.find())


# Prints all employee schedules in the scheduler database
def printScheduler():
    return list(scheduler_collection.find())
