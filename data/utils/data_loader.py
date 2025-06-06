import yfinance as yf

def load_prices(tickers, start='2020-01-01', end=None):
    data = yf.download(tickers, start=start, end=end, auto_adjust=False)  # <<<<< important
    return data['Adj Close']