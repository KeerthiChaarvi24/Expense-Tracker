from flask import Flask, render_template, request, redirect
from datetime import datetime
from dotenv import load_dotenv
import os   
import mysql.connector as mysql
load_dotenv()
#creates the Flask application instance or a website
app = Flask(__name__)

db = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT")),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)
cursor = db.cursor(buffered=True)

# ---------------- HOME PAGE ---------------- #

@app.route('/')
def home():
    # render_template loads html pages
    return render_template('index.html')

# ---------------- LOGIN ---------------- #

@app.route('/login', methods=['POST'])
def login():
    #request is used to collect user input from the form in the html page
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    # to check if the user already exists in the database, and if not, it inserts a new record for the user. It then redirects the user to their dashboard page with their customer ID as a parameter.
    cursor.execute(
        "select * from customers where email=%s or phone=%s limit 1",
        (email, phone))
    #fetches only one result from the above query if it exists 
    customer = cursor.fetchone()

    if customer:
        #storing the customer_id from customer tuple
        customer_id = customer[0]

    else:
        cursor.execute(
            "insert into customers(name,email,phone) values(%s,%s,%s)",
            (name, email, phone)
        )
        #commit ensures the data is saved permanently after the insert operation
        db.commit()
        #gets the newly created id
        customer_id = cursor.lastrowid
        #redirects to the customer dashboard page with the customer_id as a parameter
    return redirect(f"/customer/{customer_id}")

# ---------------- DASHBOARD ---------------- #

@app.route('/customer/<int:customer_id>')
def customer_dashboard(customer_id):

    # Customer Details
    cursor.execute(
        "select * from customers where id=%s",
        (customer_id,)
    )
    customer = cursor.fetchone()
    # ---------------- SEARCH / FILTER / SORT ---------------- #

    search = request.args.get("search", "").strip()
    filter_by = request.args.get("filter", "all")
    sort_by = request.args.get("sort", "newest")

        # Expense History
    query = """
    SELECT *
    FROM dailytracker
    WHERE customer_id=%s
    """

    params = [customer_id]

    # ---------- SEARCH ----------

    if search:
        query += """
        AND (
            category LIKE %s
            OR description LIKE %s
        )
        """
        keyword = f"%{search}%"
        params.extend([keyword, keyword])

    # ---------- FILTER ----------

    if filter_by == "today":
        query += " AND expense_date = CURDATE()"

    elif filter_by == "month":
        query += """
        AND MONTH(expense_date)=MONTH(CURDATE())
        AND YEAR(expense_date)=YEAR(CURDATE())
        """

    elif filter_by == "year":
        query += """
        AND YEAR(expense_date)=YEAR(CURDATE())
        """

    # ---------- SORT ----------

    if sort_by == "oldest":
        query += " ORDER BY expense_date ASC, expense_time ASC"

    elif sort_by == "highest":
        query += " ORDER BY amount DESC"

    elif sort_by == "lowest":
        query += " ORDER BY amount ASC"

    else:
        query += " ORDER BY expense_date DESC, expense_time DESC"

    cursor.execute(query, tuple(params))
    expenses = cursor.fetchall()

    # ---------------- TOTAL SPENDING ---------------- #

    cursor.execute(
        """
        select sum(amount)
        from dailytracker
        where customer_id=%s
        """,
        (customer_id,)
    )

    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    # ---------------- TODAY'S SPENDING ---------------- #

    cursor.execute(
        """
        select sum(amount)
        from dailytracker
        where customer_id=%s
        and expense_date = curdate()
        """,
        (customer_id,)
    )

    today_total = cursor.fetchone()[0]

    if today_total is None:
        today_total = 0

    # ---------------- MONTHLY SPENDING ---------------- #

    cursor.execute(
        """
        select sum(amount)
        from dailytracker
        where customer_id=%s
        and month(expense_date)=month(curdate())
        and year(expense_date)=year(curdate())
        """,
        (customer_id,)
    )

    monthly_total = cursor.fetchone()[0]

    if monthly_total is None:
        monthly_total = 0

    # ---------------- MONTHLY BUDGET ---------------- #

    cursor.execute(
        """
        SELECT monthly_budget
        FROM budget
        WHERE customer_id=%s
        """,

        (customer_id,)
    )

    row = cursor.fetchone()

    if row:

        budget = float(row[0])

    else:

        budget = 0

    remaining = budget - monthly_total

    if budget > 0:

        progress = min((monthly_total / budget) * 100, 100)

    else:

        progress = 0

    warning = monthly_total > budget and budget > 0
    # ---------------- TRANSACTION COUNT ---------------- #

    cursor.execute(
        """
        select COUNT(*)
        from dailytracker
        where customer_id=%s
        """,
        (customer_id,)
    )

    transaction_count = cursor.fetchone()[0]

    # ---------------- HIGHEST CATEGORY ---------------- #

    cursor.execute(
        """
        select category, sum(amount) AS total
        from dailytracker
        where customer_id=%s
        group by category
        order by total desc
        limit 1
        """,
        (customer_id,)
    )

    highest = cursor.fetchone()

    if highest:
        highest_category = highest[0]
        highest_amount = highest[1]
    else:
        highest_category = "None"
        highest_amount = 0
        # ---------------- PIE CHART DATA ---------------- #

    cursor.execute(
        """
        select category, sum(amount)
        from dailytracker
        where customer_id=%s
        group by category
        order by sum(amount) desc
        """,
        (customer_id,)
        #fetches the total amount spent in each category for the given customer, grouped by category and ordered by the total amount spent in descending order
    )
    # runs th query 
    category_data = cursor.fetchall()
    # category_data is a list of tuples where each tuple contains a category and its respective total amount sum

    pie_labels = [] # stores food,shopping,entertainment etc
    pie_values = [] # stores the corresponding amounts for each category
    # traverse thru category data and append to its resepctive lists
    for row in category_data:
        pie_labels.append(row[0])
        pie_values.append(float(row[1]))

        # ---------------- LINE CHART ---------------- #

    cursor.execute(
        """
        select expense_date,
            sum(amount)
        from dailytracker
        where customer_id=%s
        group by expense_date
        order by expense_date
        """,
        (customer_id,)
        # group by dates and sum the total amount
    )

    line_data = cursor.fetchall()

    line_labels = [] # stores the dates
    line_values = [] # stores the corresponding total amounts for each date

    for row in line_data:
        # strftime formats the date from dd/mm/yyyy to dd/mmm (e.g., 01 Jan)
        line_labels.append(row[0].strftime("%d %b"))
        # appends the total amount for each date to the line_values list
        line_values.append(float(row[1]))

    return render_template(
        # renders the customer.html template and passes various data to it for display on the dashboard
        "customer.html",

        customer=customer,

        expenses=expenses,

        total=total,

        today_total=today_total,

        monthly_total=monthly_total,

        transaction_count=transaction_count,

        highest_category=highest_category,

        highest_amount=highest_amount,

        pie_labels=pie_labels,

        pie_values=pie_values,

        line_labels=line_labels,

        line_values=line_values,

        search=search,

        filter_by=filter_by,

        sort_by=sort_by,

        budget=budget,

        remaining=remaining,

        progress=progress,

        warning=warning,
    )

# ---------------- ADD EXPENSE ---------------- #

@app.route('/add_expense/<int:customer_id>', methods=['POST'])
def add_expense(customer_id):

    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']

    now = datetime.now() # dd/mm/yyyy hh:mm:ss

    expense_date = now.date() # extracts only date
    expense_time = now.strftime("%H:%M:%S") # formats the time in hh:mm:ss format

    cursor.execute(

        """
        insert into dailytracker
        (customer_id,
        amount,
        category,
        description,
        expense_date,
        expense_time)

        values(%s,%s,%s,%s,%s,%s)
        """,

        (

            customer_id,
            amount,
            category,
            description,
            expense_date,
            expense_time

        )

    )

    db.commit()

    return redirect(f"/customer/{customer_id}")

# ---------------- RUN ---------------- #
# checks if python file is being run directly or being imported as a module. If it is being run directly, the Flask application will start running on the specified host and port.
@app.route('/set_budget/<int:customer_id>', methods=['POST'])
def set_budget(customer_id):

    budget = request.form['budget']

    cursor.execute(
        """
        INSERT INTO budget(customer_id, monthly_budget)

        VALUES(%s,%s)

        ON DUPLICATE KEY UPDATE

        monthly_budget=%s
        """,

        (customer_id, budget, budget)
    )

    db.commit()

    return redirect(f"/customer/{customer_id}")

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000) 