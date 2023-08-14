The Portfolio Analyzer allows to analyze single stocks, as well as Portfolios.
It uses build-in storage in order to minimize API Calls. Sources of the data are YahooFinance, AlphaVantage and Quandl.

The application can be run by downloading the Portfolio_Analyzer directory and manually starting the Dash App in Terminal.
Run with: 'python app.py'

To run install the following packages
'yfinance', 'dash', 'quandl', 'dash_bootstrap_components', 'dash_bootstrap_templates', 'dash.dependencies', 'datetime'

app.py : Contains the Dash App layout and serves as the main entry point.
callbacks.py : Contains all callbacks and serves the input to the Dash App.
data_processing.py : Contains all API-Calls, as well as the data processing functions to create the outputs.