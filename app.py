# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import sqlite3

app = Flask(__name__)

API_KEY = 'your_alpha_vantage_api_key'
BASE_URL = 'https://www.alphavantage.co/query'

# Fetch real-time stock data
def get_stock_data(symbol):
    url = f"{BASE_URL}?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    # Check if the API returns valid data
    if 'Time Series (5min)' in data:
        time_series = data['Time Series (5min)']
        latest_time = next(iter(time_series))  # Get the most recent time entry
        latest_data = time_series[latest_time]
        return {
            'symbol': symbol,
            'latest_price': latest_data['1. open'],
            'latest_time': latest_time
        }
    else:
        return None

# SQLite database interaction functions
def get_portfolio():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute('SELECT * FROM portfolio')
    portfolio = c.fetchall()
    conn.close()
    return portfolio

def add_stock(symbol, shares):
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute('INSERT INTO portfolio (symbol, shares) VALUES (?, ?)', (symbol, shares))
    conn.commit()
    conn.close()

def remove_stock(symbol):
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute('DELETE FROM portfolio WHERE symbol = ?', (symbol,))
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    portfolio = get_portfolio()
    portfolio_data = []
    for stock in portfolio:
        symbol = stock[1]
        shares = stock[2]
        stock_data = get_stock_data(symbol)
        if stock_data:
            stock_data['shares'] = shares
            portfolio_data.append(stock_data)
    return render_template('index.html', portfolio=portfolio_data)

@app.route('/add', methods=['POST'])
def add():
    symbol = request.form['symbol']
    shares = int(request.form['shares'])
    add_stock(symbol, shares)
    return redirect(url_for('index'))

@app.route('/remove', methods=['POST'])
def remove():
    symbol = request.form['symbol']
    remove_stock(symbol)
    return redirect(url_for('index'))

@app.route('/track_performance', methods=['GET'])
def track_performance():
    portfolio = get_portfolio()
    portfolio_data = []
    total_value = 0
    for stock in portfolio:
        symbol = stock[1]
        shares = stock[2]
        stock_data = get_stock_data(symbol)
        if stock_data:
            stock_data['shares'] = shares
            stock_data['total_value'] = float(stock_data['latest_price']) * shares
            total_value += stock_data['total_value']
            portfolio_data.append(stock_data)
    return jsonify({
        'portfolio': portfolio_data,
        'total_value': total_value
    })

if __name__ == '__main__':
    app.run(debug=True)
