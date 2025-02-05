import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template, request, jsonify
from plotly.subplots import make_subplots
import plotly.graph_objects as go

class StockAnalyzer:
    def __init__(self, tickers, start_date, end_date):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.stock_data = {}
        self.fetch_data()

    def fetch_data(self):
        for ticker in self.tickers:
            try:
                self.stock_data[ticker] = yf.download(ticker, start=self.start_date, end=self.end_date)
            except Exception as e:
                self.stock_data[ticker] = None

    def calculate_metrics(self):
        for ticker, data in self.stock_data.items():
            if data is not None:
                data['SMA_50'] = data['Close'].rolling(window=50).mean()
                data['SMA_200'] = data['Close'].rolling(window=200).mean()
                data['Daily_Return'] = data['Close'].pct_change()
                data['Volatility'] = data['Daily_Return'].rolling(window=21).std()

    def calculate_total_return(self):
        returns = {}
        for ticker, data in self.stock_data.items():
            if data is not None and not data.empty:
                returns[ticker] = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            else:
                returns[ticker] = None
        return returns

    def generate_plot(self):
        fig = make_subplots(rows=1, cols=1)
        for ticker, data in self.stock_data.items():
            if data is not None:
                fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name=f'{ticker} Close'))
                if 'SMA_50' in data:
                    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_50'], mode='lines', name=f'{ticker} SMA 50', line=dict(dash='dash')))
                if 'SMA_200' in data:
                    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_200'], mode='lines', name=f'{ticker} SMA 200', line=dict(dash='dot')))

        fig.update_layout(title="Stock Analysis", xaxis_title="Date", yaxis_title="Price (USD)", template="plotly_dark")
        return fig.to_html(full_html=False)

    def analyze(self):
        self.calculate_metrics()
        total_returns = self.calculate_total_return()
        plot_html = self.generate_plot()
        return total_returns, plot_html

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        tickers = request.form['tickers'].split(',')
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        analyzer = StockAnalyzer(tickers, start_date, end_date)
        total_returns, plot_html = analyzer.analyze()

        return render_template('index.html', total_returns=total_returns, plot_html=plot_html)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

# templates/index.html

"""
<!DOCTYPE html>
<html>
<head>
    <title>Stock Analysis</title>
</head>
<body>
    <h1>Stock Analysis</h1>
    <form method="POST">
        <label for="tickers">Ticker Symbols (comma-separated):</label>
        <input type="text" id="tickers" name="tickers" placeholder="e.g., AAPL, MSFT"><br><br>
        <label for="start_date">Start Date:</label>
        <input type="date" id="start_date" name="start_date"><br><br>
        <label for="end_date">End Date:</label>
        <input type="date" id="end_date" name="end_date"><br><br>
        <input type="submit" value="Analyze">
    </form>

    {% if total_returns %}
        <h2>Analysis Results</h2>
        <ul>
            {% for ticker, return_ in total_returns.items() %}
                <li>{{ ticker }}: {{ return_ | round(2) if return_ is not none else "Data not available" }}%</li>
            {% endfor %}
        </ul>
        <div>{{ plot_html|safe }}</div>
    {% endif %}
</body>
</html>
"""
