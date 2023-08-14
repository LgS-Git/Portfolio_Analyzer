import yfinance as yf
import quandl
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import requests


def get_stock_data(ticker_symbol, start_date, end_date):
    # API Call
    ticker_data = yf.Ticker(ticker_symbol)
    print('Yahoo API Call: ' + ticker_symbol)

    # Get currency
    currency = ticker_data.info['currency']

    # Get Infos
    current_price = str(ticker_data.info['currentPrice']) + "   " + currency
    market_cap = format_number(ticker_data.info['marketCap'])
    avg_volume = format_number(ticker_data.info['averageVolume'])
    pe_ratio = round(ticker_data.info['trailingPE'], 2) if 'trailingPE' in ticker_data.info else 'NaN'

    # Update stock chart
    df = ticker_data.history(start=start_date, end=end_date)

    # Define the buttons for different time ranges
    range_buttons = [
        dict(count=1, label="1m", step="month", stepmode="backward"),
        dict(count=6, label="6m", step="month", stepmode="backward"),
        dict(count=1, label="1y", step="year", stepmode="backward"),
        dict(count=5, label="5y", step="year", stepmode="backward"),
        dict(step="all", label="All")
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Closing Price"))
    fig.update_layout(
        xaxis=dict(rangeselector=dict(buttons=range_buttons)),
        title=f"{ticker_symbol} Closing Price",
        xaxis_title="Date",
        yaxis_title=f"Price in {currency}",
        legend_title="Legend",
        autosize=True
    )

    return current_price, market_cap, avg_volume, pe_ratio, fig


def format_number(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T', 'Q'][magnitude])


def get_risk_free_rate(riskFreeCountry):

    # Quandl API config
    quandl.ApiConfig.api_key = 'cxzP3gdEbWx7ewRfYrRH'
    country = riskFreeCountry

    # API Calls
    data = quandl.get(country)
    print('Quandl API Call:' + country)
    current_yield = data.iloc[0][0]

    return current_yield


def get_portfolio_data(portfolio, start_date, end_date, marketPortfolio, riskFree_rate, triggered_input, portfolio_store, marketPortfolio_store, exchangeRate_store):

    start_date_string = start_date.strftime('%Y-%m-%d')
    end_date_string = end_date.strftime('%Y-%m-%d')
    for ticker, shares in portfolio.items():
        # Check if API call for stock is needed or stock is already in store, otherwise call API, else retrieve from store
        if ticker not in portfolio_store or portfolio_store[ticker]['startDate'] != start_date_string or portfolio_store[ticker]['endDate'] != end_date_string:
            # API Call
            ticker_data = yf.Ticker(ticker)
            print('Yahoo API Call: ' + ticker)
            # Get close prices
            close_prices = ticker_data.history(start=start_date, end=end_date)['Close']
            # Transform the DateTimeIndex to date strings without timestamps
            close_prices.index = close_prices.index.date.astype(str)
            # Convert the series to a dict (In order to store with dcc.Store)
            close_prices_dates = close_prices.index.tolist()
            close_prices_values = close_prices.values.tolist()
            # Get currency of each stock
            currency = ticker_data.info['currency']
            # Write into dictionary
            portfolio[ticker] = {
                'dates': close_prices_dates,
                'prices': close_prices_values,
                'shares': 0,
                'startValue': 0,
                'currency': currency,
                'startDate': start_date_string,
                'endDate': end_date_string
            }
        else:
            portfolio[ticker] = portfolio_store[ticker]

        # Update shares and start values everytime
        portfolio[ticker]['shares'] = shares
        portfolio[ticker]['startValue'] = shares * portfolio[ticker]['prices'][0]

    # Store new Portfolio
    portfolio_store = portfolio

    # Check if marketPortfolio is already in store, otherwise call API, else retrieve from store
    if not marketPortfolio_store.get('ticker') or marketPortfolio != marketPortfolio_store['ticker'] or marketPortfolio_store['startDate'] != start_date_string or marketPortfolio_store['endDate'] != end_date_string:
        # API Call
        ticker_data_mP = yf.Ticker(marketPortfolio)
        print('Yahoo API Call: ' + marketPortfolio)
        # Get close prices
        marketPortfolio_close = ticker_data_mP.history(start=start_date, end=end_date)['Close']
        # Transform the DateTimeIndex to date strings without timestamps
        marketPortfolio_close.index = marketPortfolio_close.index.date.astype(str)
        # Convert the series to a dict (In order to store with dcc.Store)
        marketPortfolio_close_dates = marketPortfolio_close.index.tolist()
        marketPortfolio_close_values = marketPortfolio_close.values.tolist()
        # Get currency of marketPortfolio
        currency_mP = ticker_data_mP.info['currency']
        # Write into dictionary
        marketPortfolio = {
            'ticker': marketPortfolio,
            'dates': marketPortfolio_close_dates,
            'prices': marketPortfolio_close_values,
            'currency': currency_mP,
            'startDate': start_date_string,
            'endDate': end_date_string
        }
    else:
        marketPortfolio = marketPortfolio_store

    marketPortfolio_store = marketPortfolio  # Store new marketPortfolio

    # Convert stored dicts back into pandasSeries and put into pandasDataFrame | Also collect unique currencies
    portfolioDF = pd.DataFrame()
    unique_currencies_toUSD = {}
    portfolio_info = {}
    for ticker, data in portfolio.items():
        # Convert each stock to pandasSeries
        stockSeries = pd.Series(data['prices'], index=data['dates'], name=ticker)
        # Fill in info about startValue and currency in extra dict: 'ticker': currency, start_value
        portfolio_info[ticker] = (data['currency'], data['startValue'])
        # Add each currency to the dictionary with placeholder value None
        unique_currencies_toUSD[data['currency']] = None
        # Store stockSeries in DataFrame
        portfolioDF = pd.concat([portfolioDF, stockSeries], axis=1)

    # Convert marketPortfolio to pandasSeries | Add unique_currency if applicable
    marketPortfolioPS = pd.Series(marketPortfolio['prices'], index=marketPortfolio['dates'], name=marketPortfolio['ticker'])
    marketPortfolioPS.currency = marketPortfolio['currency']
    unique_currencies_toUSD[marketPortfolio['currency']] = None

    # Delete USD from unique_currencies_toUSD
    unique_currencies_toUSD.pop('USD', None)

    # Find necessary exchange rates and store them (from AlphaVantage)
    api_key = 'PE8445MYJQQ5DLLP'
    base_url = 'https://www.alphavantage.co/query?'
    exchangeRate_function = 'CURRENCY_EXCHANGE_RATE'
    to_currency = 'USD'
    for from_currency in unique_currencies_toUSD:
        # If exchange_rate not already in store make API Call, else retrieve from store
        if from_currency not in exchangeRate_store:
            url = f'{base_url}function={exchangeRate_function}&from_currency={from_currency}&to_currency={to_currency}&apikey={api_key}'
            exchange_rate_data = requests.get(url).json()
            print('AlphaVantage API Call: ' + from_currency + ' --> USD')
            exchange_rate = float(exchange_rate_data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
            unique_currencies_toUSD[from_currency] = exchange_rate

            # Fill new rates into exchangeRate_store (Unlike the other stores this one is permanent, until DashApp is restarted)
            exchangeRate_store[from_currency] = exchange_rate
        else:
            unique_currencies_toUSD[from_currency] = exchangeRate_store[from_currency]

    # Convert prices/start_value for each stock and MP to USD
    for ticker in portfolioDF.columns:
        currency, start_value = portfolio_info[ticker]
        exchange_rate = unique_currencies_toUSD.get(currency, 1.0)  # default to 1.0 if currency is not found
        portfolioDF[ticker] *= exchange_rate
        start_value *= exchange_rate
        portfolio_info[ticker] = [currency, start_value]

    marketPortfolioPS *= unique_currencies_toUSD.get(marketPortfolioPS.currency, 1.0)

    # Align (same size) the portfolioFrame and marketPortfolioSeries and drop NaN
    aligned_data = pd.concat([portfolioDF, marketPortfolioPS], axis=1)

    aligned_data = aligned_data.dropna(how='any')

    portfolioDF_aligned = aligned_data.iloc[:, :-1]
    marketPortfolioPS_aligned = aligned_data.iloc[:, -1]

    # Calc returns from aligned price data
    portfolioDF_returns_aligned = portfolioDF_aligned.pct_change().dropna(how='any')
    marketPortfolioPS_returns_aligned = marketPortfolioPS_aligned.pct_change().dropna()

    # Calc returns from price data
    portfolioDF_returns = portfolioDF.pct_change().dropna(how='any')
    marketPortfolioPS_returns = marketPortfolioPS.pct_change().dropna()

    # Calculations
    alpha = round(calculate_portfolio_alpha(portfolioDF_returns_aligned, marketPortfolioPS_returns_aligned, riskFree_rate, portfolio_info), 2)
    beta = round(calculate_portfolio_beta(portfolioDF_returns_aligned, marketPortfolioPS_returns_aligned, portfolio_info), 2)
    returns = str(round(calculate_cumulative_return(portfolioDF_returns, portfolio_info), 2)) + ' %'
    dollarReturn = str(format_number(calculate_dollar_return(portfolioDF_returns, portfolio_info))) + ' $'
    sharpeRatio = round(calculate_sharpe_ratio(portfolioDF_returns, riskFree_rate, portfolio_info), 2)
    sortinoRatio = round(calculate_sortino_ratio(portfolioDF_returns, riskFree_rate, portfolio_info), 2)
    fig = create_portfolio_figure(portfolioDF, portfolioDF_returns, portfolio_info)

    return alpha, beta, returns, dollarReturn, sharpeRatio, sortinoRatio, fig, portfolio_store, marketPortfolio_store, exchangeRate_store


def calculate_portfolio_beta(portfolioReturnsDF, marketReturnsPS, portfolio_info):

    # Getting total investment
    totalInvestment = sum([portfolio_info[ticker][1] for ticker in portfolioReturnsDF.columns])

    portfolioBeta = 0

    # Iterate over each stock
    for ticker in portfolioReturnsDF.columns:
        stockReturns = portfolioReturnsDF[ticker]
        startValue = portfolio_info[ticker][1]

        # Beta is Covariance(Returns of portfolio, Returns of market) / Variance(Returns of market)
        covariance = np.cov(stockReturns, marketReturnsPS)[0][1]
        marketVariance = np.var(marketReturnsPS)
        stockBeta = covariance / marketVariance

        # Weighted beta
        weightedBeta = stockBeta * (startValue/totalInvestment)

        portfolioBeta += weightedBeta

    return portfolioBeta


def calculate_cumulative_return(portfolioReturnsDF, portfolio_info):

    # Getting total investment
    totalInvestment = sum([portfolio_info[ticker][1] for ticker in portfolioReturnsDF.columns])

    totalReturn = 0

    for ticker in portfolioReturnsDF.columns:
        weighted_cumulative_returns = ((1 + portfolioReturnsDF[ticker]).prod() - 1) * (portfolio_info[ticker][1]/totalInvestment)
        totalReturn += weighted_cumulative_returns

    # In percent
    totalReturn = totalReturn*100

    return totalReturn


def calculate_sharpe_ratio(portfolioReturnsDF, riskFree_rate, portfolio_info):

    # Getting total investment
    totalInvestment = sum([portfolio_info[ticker][1] for ticker in portfolioReturnsDF.columns])

    # Apply the weight to the return of each stock
    for ticker in portfolioReturnsDF.columns:
        start_value = portfolio_info[ticker][1]
        portfolioReturnsDF[ticker] *= (start_value / totalInvestment)

    # Calculate the weighted return of the portfolio
    portfolioReturns = portfolioReturnsDF.sum(axis=1)

    # Calculate the mean return of the portfolio and the standard deviation
    meanReturns = portfolioReturns.mean()
    stdReturns = portfolioReturns.std()

    # Annualize
    meanReturns_ann = ((1 + meanReturns)**252) - 1
    stdReturns_ann = stdReturns * np.sqrt(252)

    # Calculate the Sharpe ratio
    sharpeRatio = (meanReturns_ann - riskFree_rate) / stdReturns_ann

    return sharpeRatio


def calculate_sortino_ratio(portfolioReturnsDF, riskFree_rate, portfolio_info):

    # Calculate total investment
    totalInvestment = sum([portfolio_info[ticker][1] for ticker in portfolioReturnsDF.columns])

    # Apply the weight to the return of each stock
    for ticker in portfolioReturnsDF.columns:
        initial_investment = portfolio_info[ticker][1]
        portfolioReturnsDF[ticker] *= (initial_investment / totalInvestment)

    # Sum weighted returns to get the total return of the portfolio
    portfolioWeightedReturns = portfolioReturnsDF.sum(axis=1)

    # Calculate the mean return of the portfolio
    meanReturns = portfolioWeightedReturns.mean()

    # Calculate downside deviation
    negativeReturns = portfolioWeightedReturns[portfolioWeightedReturns < 0]
    downsideDeviation = np.sqrt((negativeReturns**2).mean())

    # Annualize
    meanReturns_ann = ((1 + meanReturns)**252) - 1
    downsideDeviation_ann = downsideDeviation * np.sqrt(252)

    # Calculate the Sortino ratio
    sortinoRatio = (meanReturns_ann - riskFree_rate) / downsideDeviation_ann

    return sortinoRatio


def calculate_portfolio_alpha(portfolioReturnsDF, marketReturnsPS, riskFree_rate, portfolio_info):

    # Getting total investment
    totalInvestment = sum([portfolio_info[ticker][1] for ticker in portfolioReturnsDF.columns])

    # Get portfolio beta
    portfolioBeta = calculate_portfolio_beta(portfolioReturnsDF, marketReturnsPS, portfolio_info)

    # Apply the weight to the return of each stock
    for ticker in portfolioReturnsDF.columns:
        start_value = portfolio_info[ticker][1]
        portfolioReturnsDF[ticker] *= (start_value / totalInvestment)

    # Sum weighted returns to get the total return of the portfolio
    portfolioWeightedReturns = portfolioReturnsDF.sum(axis=1)

    # Calculate annualized returns of the portfolio and market
    Rp_annualized = ((1 + portfolioWeightedReturns.mean())**252) - 1
    Rm_annualized = ((1 + marketReturnsPS.mean())**252) - 1

    # Calculate alpha
    portfolioAlpha = Rp_annualized - (riskFree_rate + portfolioBeta * (Rm_annualized - riskFree_rate))

    return portfolioAlpha


def calculate_dollar_return(portfolioReturnsDF, portfolio_info):

    totalReturn = 0

    for ticker in portfolioReturnsDF.columns:
        initial_investment = portfolio_info[ticker][1]
        cumulative_return = (1 + portfolioReturnsDF[ticker]).prod() - 1
        return_in_dollars = initial_investment * cumulative_return

        totalReturn += return_in_dollars

    return totalReturn


def create_portfolio_figure(portfolioDF, portfolioReturnsDF, portfolio_info):

    # Getting total investment
    totalInvestment = sum([portfolio_info[ticker][1] for ticker in portfolioDF.columns])

    # Apply weight
    for ticker in portfolioDF.columns:
        weight = portfolio_info[ticker][1] / totalInvestment
        portfolioDF[ticker] = portfolioDF[ticker] * weight
        portfolioReturnsDF[ticker] = portfolioReturnsDF[ticker] * weight

    # Sum over weighted stocks
    portfolioDF['Total'] = portfolioDF.sum(axis=1)
    portfolioReturnsDF['Total'] = portfolioReturnsDF.sum(axis=1)

    # Apply log to portfolio prices
    portfolioDF_log = np.log(portfolioDF)

    # Create figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=portfolioDF.index, y=portfolioDF['Total'], mode='lines', name='Total'))
    fig.add_trace(go.Scatter(x=portfolioDF_log.index, y=portfolioDF_log['Total'], mode='lines', name='Log Total', visible=False))
    fig.add_trace(go.Scatter(x=portfolioReturnsDF.index, y=portfolioReturnsDF['Total'], mode='lines', name='Total Returns', visible=False))

    # Define what shows on what scale
    scale_dropdown = [
        dict(args=[{"visible": [True, False, False]}, {"yaxis.title": "Price in USD"}], label="Prices (Linear Scale)", method="update"),
        dict(args=[{"visible": [False, True, False]}, {"yaxis.title": "Log Price in USD"}], label="Prices (Log Scale)", method="update"),
        dict(args=[{"visible": [False, False, True]}, {"yaxis.title": "Returns (%)"}, {}], label="Returns (Linear Scale)", method="update"),
    ]

    # Define the buttons for different time ranges
    range_buttons = [
        dict(count=1, label="1m", step="month", stepmode="backward"),
        dict(count=6, label="6m", step="month", stepmode="backward"),
        dict(count=1, label="1y", step="year", stepmode="backward"),
        dict(count=5, label="5y", step="year", stepmode="backward"),
        dict(step="all", label="All")
    ]

    fig.update_layout(
        updatemenus=[
            dict(
                buttons=scale_dropdown,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=1,
                xanchor="right",
                y=1,
                yanchor="top"
            ),
        ],
        xaxis=dict(rangeselector=dict(buttons=range_buttons)),
        title="Portfolio Closing Price",
        xaxis_title="Date",
        autosize=True
    )

    return fig
