import dash
from dash.dependencies import Input, Output, State

import plotly.graph_objs as go

from datetime import datetime

import data_processing


def register_callbacks_stock(app):
    @app.callback(
        [
            Output('currentPrice-display', 'children'),
            Output('marketCap-display', 'children'),
            Output('avgVolume-display', 'children'),
            Output('peRatio-display', 'children'),
            Output('stock-chart', 'figure'),
            Output('stock-error-alert', 'children'),
            Output('stock-error-alert', 'is_open')
        ],

        [
            Input('ticker-input', 'value'),
            Input('date-range-stock', 'start_date'),
            Input('date-range-stock', 'end_date'),
        ]
    )
    def update_stock_data(ticker_symbol, start_date, end_date):
        # For empty ticker
        if not ticker_symbol:
            return '-', '-', '-', '-', empty_figure(), dash.no_update, False

        # Remove timestamp from Date inputs and convert to datetime
        start_date = datetime.strptime(start_date.split("T")[0], '%Y-%m-%d')
        end_date = datetime.strptime(end_date.split("T")[0], '%Y-%m-%d')
        # Shift timepoint for end_date to the end of the day and start_date to beginning
        start_date = start_date.replace(hour=00, minute=00, second=00)
        end_date = end_date.replace(hour=23, minute=59, second=59)

        try:
            # Call get_stock_data
            current_price, market_cap, avg_volume, pe_ratio, fig = data_processing.get_stock_data(ticker_symbol, start_date, end_date)

            return current_price, market_cap, avg_volume, pe_ratio, fig, dash.no_update, False

        except Exception as e:
            print(f'Error getting stock data: {e}')
            # If there's an error, return default values for all outputs and the error message
            return '-', '-', '-', '-', empty_figure(), 'Ticker symbol not available', True


def register_callbacks_riskFreeRate(app):
    @app.callback(
        [
            Output('riskFreeRate-display', 'children'),
            Output('riskFreeRate-input', 'value')
        ],

        [
            Input('riskFreeButton', 'n_clicks')
        ],

        [
            State('riskFreeCountry', 'value')
        ]
    )
    def update_risk_free_rate(n_clicks, riskFreeCountry):
        if n_clicks == 0:
            return '- %', dash.no_update
        riskFreeRate = data_processing.get_risk_free_rate(riskFreeCountry)
        riskFreeRate_StringPerc = str(riskFreeRate) + ' %'

        return riskFreeRate_StringPerc, riskFreeRate


def register_callbacks_add_to_portfolio(app):
    @app.callback(
        [
            Output('portfolio-input', 'value')
        ],
        [
            Input('addPortfolio-button', 'n_clicks')
        ],
        [
            State('ticker-input', 'value'),
            State('share-input', 'value'),
            State('portfolio-input', 'value')
        ]
    )
    def update_portolio_composition(n_clicks, ticker_symbol, shares, current_portfolio):

        if n_clicks is None or ticker_symbol == '' or shares is None:
            return dash.no_update

        # Check if shares is a number and is not 0
        try:
            shares = int(shares)
            if shares == 0:
                shares = 1
        except (ValueError, TypeError):
            shares = 1

        # Create the new portfolio string
        new_portfolio_string = f"{ticker_symbol}, {shares}"

        # If the current portfolio is not empty, append a newline character and the new portfolio string
        if current_portfolio:
            current_portfolio += "\n" + new_portfolio_string
        else:  # If the current portfolio is empty, just use the new portfolio string
            current_portfolio = new_portfolio_string

        return [current_portfolio]


def register_callbacks_portfolio(app):
    @app.callback(
        [
            Output('alpha-display', 'children'),
            Output('beta-display', 'children'),
            Output('return-display', 'children'),
            Output('dollarReturn-display', 'children'),
            Output('sharpeRatio-display', 'children'),
            Output('sortinoRatio-display', 'children'),
            Output('portfolio-chart', 'figure'),
            Output('portfolio-store', 'data'),
            Output('marketPortfolio-store', 'data'),
            Output('exchangeRate-store', 'data'),
            Output('portfolio-error-alert', 'children'),
            Output('portfolio-error-alert', 'is_open')
        ],
        [
            Input('submit-button', 'n_clicks'),
            Input('date-range-portfolio', 'start_date'),
            Input('date-range-portfolio', 'end_date'),
            Input('marketPortfolio', 'value'),
            Input('riskFreeRate-input', 'value')
        ],
        [
            State('portfolio-input', 'value'),
            State('portfolio-store', 'data'),
            State('marketPortfolio-store', 'data'),
            State('exchangeRate-store', 'data')
        ]
    )
    def update_portfolio(n_clicks, start_date, end_date, marketPortfolio, riskFree_rate, portfolio_input, portfolio_store, marketPortfolio_store, exchangeRate_store):

        # For empty portfolio
        if not portfolio_input:
            return '-', '-', '-', '-', '-', '-', empty_figure(), dash.no_update, dash.no_update, dash.no_update, dash.no_update, False

        # Get which input triggered the callback
        ctx = dash.callback_context
        triggered_input = None
        if ctx.triggered:  # Check if the list is not empty
            prop_id = ctx.triggered[0]['prop_id']
            triggered_input = prop_id.split('.')[0]
        print('Triggered_input: ' + triggered_input)

        # Initialize stores if they are None
        if portfolio_store is None:
            portfolio_store = {}
        if marketPortfolio_store is None:
            marketPortfolio_store = {}
        if exchangeRate_store is None:
            exchangeRate_store = {}

        # Remove timestamp from Date inputs and convert to datetime
        start_date = datetime.strptime(start_date.split("T")[0], '%Y-%m-%d')
        end_date = datetime.strptime(end_date.split("T")[0], '%Y-%m-%d')
        # Shift timepoint for end_date to the end of the day and start_date to beginning
        start_date = start_date.replace(hour=00, minute=00, second=00)
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Convert riskFree_rate to float and decimal
        riskFree_rate = float(riskFree_rate)/100

        try:
            # Create dict with stocks and stock #
            portfolio = {}
            lines = portfolio_input.split('\n')
            for line in lines:
                ticker, shares = line.split(',')
                portfolio[ticker.strip()] = int(shares.strip())

            # Call get_portfolio_data
            alpha, beta, returns, dollarReturn, sharpeRatio, sortinoRatio, fig, portfolio_store, marketPortfolio_store, exchangeRate_store = data_processing.get_portfolio_data(
                portfolio, start_date, end_date, marketPortfolio, riskFree_rate, triggered_input, portfolio_store, marketPortfolio_store, exchangeRate_store)

            return alpha, beta, returns, dollarReturn, sharpeRatio, sortinoRatio, fig, portfolio_store, marketPortfolio_store, exchangeRate_store, dash.no_update, False

        except Exception as e:
            print(f'Error getting portfolio data: {e}')
            # If there's an error, return default values for all outputs and the error message
            return '-', '-', '-', '-', '-', '-', empty_figure(), dash.no_update, dash.no_update, dash.no_update, 'Invalid Input', True


def empty_figure():
    # Define data
    dates = ['YYYY']
    prices = ['100']

    # Define a transparent trace
    trace = go.Scatter(x=dates, y=prices, line=dict(color='rgba(0, 0, 0, 0)'))

    fig = go.Figure(data=trace,
                    layout=go.Layout(
                        title="Please enter a stock ticker to view its data",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        autosize=True,
                    )
                    )
    return fig
