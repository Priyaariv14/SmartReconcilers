from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
import matplotlib.pyplot as plt
from io import BytesIO
import plotly.graph_objects as go
import base64
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Initialize Flask app
app = Flask(__name__)

# Load GPT-2 model and tokenizer from Hugging Face
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

# Function to retrieve user data from the database
def get_user_data(username):
    conn = sqlite3.connect('banking_system.db')
    cursor = conn.cursor()

    cursor.execute('''SELECT * FROM users WHERE username = ?''', (username,))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
        cursor.execute('''SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC''', (user_id,))
        transactions = cursor.fetchall()

        cursor.execute('''SELECT balance FROM savings_account WHERE user_id = ?''', (user_id,))
        savings_balance = cursor.fetchone()[0]

        cursor.execute('''SELECT loan_balance, interest_rate FROM loan_account WHERE user_id = ?''', (user_id,))
        loan_data = cursor.fetchone()

        conn.close()
        return user, transactions, savings_balance, loan_data
    else:
        conn.close()
        return None, None, None, None

def check_savings_goal(savings_balance, savings_goal):
    if savings_balance >= savings_goal:
        return f"Congratulations! You have reached your savings goal of ${savings_goal}."
    return None

def check_transaction_limit(transactions, transaction_limit):
    total_spent = sum([t[4] for t in transactions])  # Sum of all transaction amounts
    if total_spent > transaction_limit:
        return f"Alert: You have exceeded your transaction limit of ${transaction_limit}."
    return None

def check_loan_repayment(loan_balance, repayment_threshold):
    if loan_balance <= repayment_threshold:
        return f"Your loan balance has fallen below ${repayment_threshold}. You can now consider repayment."
    return None

def generate_notifications(user_data, transactions, savings_balance, loan_data, savings_goal=10000, transaction_limit=5000, repayment_threshold=500):
    notifications = []

    # Check savings goal
    savings_notification = check_savings_goal(savings_balance, savings_goal)
    if savings_notification:
        notifications.append(savings_notification)

    # Check transaction limit
    transaction_notification = check_transaction_limit(transactions, transaction_limit)
    if transaction_notification:
        notifications.append(transaction_notification)

    # Check loan repayment
    loan_notification = check_loan_repayment(loan_data[0], repayment_threshold)
    if loan_notification:
        notifications.append(loan_notification)

    return notifications
 
import requests

# Simulate market changes (e.g., 5% fluctuation)
def simulate_market_conditions():
    market_fluctuation = random.uniform(-0.05, 0.05)  # -5% to +5%
    return market_fluctuation

# Adjust asset allocation based on market conditions
def adjust_portfolio_based_on_market(risk_tolerance, market_fluctuation):
    allocation = {}

    if risk_tolerance == 'high':
        allocation = {
            'stocks': 0.7 + market_fluctuation,
            'bonds': 0.2 - market_fluctuation / 2,
            'real_estate': 0.1
        }
    elif risk_tolerance == 'medium':
        allocation = {
            'stocks': 0.4 + market_fluctuation / 2,
            'bonds': 0.4 - market_fluctuation / 4,
            'real_estate': 0.2
        }
    elif risk_tolerance == 'low':
        allocation = {
            'stocks': 0.3,
            'bonds': 0.6 + market_fluctuation / 3,
            'real_estate': 0.1
        }

    return allocation
    
def generate_investment_strategy_with_market(user_data, savings_balance):
    market_fluctuation = simulate_market_conditions()
    portfolio_allocation = adjust_portfolio_based_on_market(user_data[7], market_fluctuation)
    
    # Generating dynamic strategy
    strategy = f"Dynamic asset allocation based on market conditions:\n"
    for asset_class, percentage in portfolio_allocation.items():
        strategy += f"{asset_class}: {percentage * 100:.2f}%\n"
    
    # Add extra considerations based on savings balance
    if savings_balance > 100000:
        strategy += "You have a large savings balance, consider including real estate and alternative investments."
    
    return strategy
    
def categorize_transactions(transactions):
    categories = {
        'groceries': ['grocery', 'supermarket', 'food'],
        'entertainment': ['movie', 'concert', 'game', 'event'],
        'utilities': ['electricity', 'water', 'internet'],
        'shopping': ['mall', 'clothes', 'shopping'],
        'others': ['miscellaneous']
    }

    categorized_transactions = {
        'groceries': [],
        'entertainment': [],
        'utilities': [],
        'shopping': [],
        'others': []
    }

    for transaction in transactions:
        description = transaction[2].lower()
        categorized = False
        for category, keywords in categories.items():
            if any(keyword in description for keyword in keywords):
                categorized_transactions[category].append(transaction)
                categorized = True
                break
        if not categorized:
            categorized_transactions['others'].append(transaction)

    return categorized_transactions
    
# Function to generate personalized recommendations using GPT-2
def generate_recommendations_gpt(user_data, transactions, savings_balance, loan_data):
    input_text = f"""
    User Profile:
    Income: {user_data[5]}
    Expenses: {user_data[6]}
    Savings Balance: {savings_balance}
    Loan Balance: {loan_data[0]}
    Risk Tolerance: {user_data[7]}
    Investment Goals: {user_data[8]}
    """

    inputs = tokenizer.encode(input_text, return_tensors="pt")
    outputs = model.generate(inputs, max_length=500, num_return_sequences=1, no_repeat_ngram_size=2, top_k=50, top_p=0.95, temperature=1.2)

    recommendation = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return recommendation

def recommend_products(income, savings_balance, credit_score, transaction_history):
    product_recommendations = []

    # Credit Card Recommendation based on spending patterns and credit score
    if credit_score > 700:
        product_recommendations.append("We recommend a premium credit card with cashback benefits.")
    elif credit_score > 650:
        product_recommendations.append("We recommend a standard credit card with rewards points.")

    # Loan Recommendation based on income and expenses
    if income > 5000 and savings_balance > 10000:
        product_recommendations.append("Consider a personal loan with a low interest rate for further investments.")
    elif income > 3000 and savings_balance > 5000:
        product_recommendations.append("A small loan could help you fund some of your immediate goals.")

    # Mortgage Recommendation
    if savings_balance > 50000 and income > 7000:
        product_recommendations.append("You are eligible for a mortgage loan with a low down payment.")

    # Transaction-based recommendations
    categories = [t[2] for t in transaction_history]
    if 'shopping' in categories:
        product_recommendations.append("Consider applying for a store-specific credit card for additional discounts.")

    return product_recommendations

# Generate Pie Chart using Plotly
def generate_pie_chart(transaction_categories):
    # Define the category labels and their corresponding values
    labels = list(transaction_categories.keys())
    values = [len(transactions) for transactions in transaction_categories.values()]

    # Create a pie chart using Plotly
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3, textinfo='percent+label', pull=[0.1, 0.1, 0.1, 0.1, 0])])

    # Adjust layout for better presentation
    fig.update_layout(
        title="Transaction Categories Distribution",
        showlegend=True,
        autosize=True,
        margin=dict(t=40, b=40, l=40, r=40),
        template="plotly_dark"
    )

    # Convert the Plotly figure to an image (PNG)
    img_bytes = BytesIO()
    fig.write_image(img_bytes, format='png')
    img_bytes.seek(0)

    # Convert image to base64 for embedding in HTML
    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    
    return img_base64
    
    
# Route to render login page
@app.route('/')
def login():
    return render_template('login.html')

# Route to handle login form submission
@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']

    # Retrieve user data for login validation
    conn = sqlite3.connect('banking_system.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM users WHERE username = ? AND password = ?''', (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['username'] = username  # Store username in session
        return redirect(url_for('dashboard'))
    else:
        return "Login Failed: Invalid username or password"


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_data, transactions, savings_balance, loan_data = get_user_data(username)

    if user_data:
        # Categorize transactions
        categorized_transactions = categorize_transactions(transactions)

        # Generate other personalized recommendations
        investment_strategy = generate_investment_strategy_with_market(user_data, savings_balance)
        product_recommendations = recommend_products(user_data[5], savings_balance, user_data[9], transactions)
        recommendations = generate_recommendations_gpt(user_data, transactions, savings_balance, loan_data)
        notifications = generate_notifications(user_data, transactions, savings_balance, loan_data)

        # Generate pie chart
        pie_chart_data = generate_pie_chart(categorized_transactions)

        return render_template('dashboard.html', user_data=user_data, transactions=transactions,
                               savings_balance=savings_balance, loan_data=loan_data, recommendations=recommendations,
                               investment_strategy=investment_strategy, product_recommendations=product_recommendations,
                               notifications=notifications, categorized_transactions=categorized_transactions,
                               pie_chart_data=pie_chart_data)  # Pass the pie chart data
    else:
        return "User data not found"
        
        
# Run the application
if __name__ == '__main__':
    app.run(debug=True)
