import json

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
all_tickers = json.loads(open('src/ticker.json').read())
tickers_list = [k['s'] for k in all_tickers['data']]

st.set_page_config(
    page_title="MarketMind",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stButton>button {
        background-color: #262730;
        color: #ffffff;
        border: 1px solid #4b4b4b;
        border-radius: 5px;
    }
    .stButton>button:hover {
        border-color: #00adb5;
        color: #00adb5;
    }
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🧠 MarketMind")
st.sidebar.markdown("---")

ticker_symbol = st.sidebar.selectbox("Enter Ticker Symbol", tickers_list, index=1).upper()

# Date Range Selection
period_options = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "YTD": "ytd",
    "1 Year": "1y",
    "5 Years": "5y",
    "Max": "max"
}
selected_period = st.sidebar.selectbox("Select Time Period", list(period_options.keys()), index=4)
period = period_options[selected_period]

st.sidebar.markdown("---")
st.sidebar.info("Enter a stock or crypto ticker (e.g., AAPL, BTC-USD, TSLA) to view real-time data and analysis.")

# Main Content
if ticker_symbol:
    try:
        # Fetch Data
        ticker_data = yf.Ticker(ticker_symbol)
        hist_data = ticker_data.history(period=period)
        info = ticker_data.info

        if hist_data.empty:
            st.error(f"No data found for ticker symbol: {ticker_symbol}")
        else:
            # Header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.title(f"{info.get('longName', ticker_symbol)} ({ticker_symbol})")
            with col2:
                current_price = info.get('currentPrice', hist_data['Close'].iloc[-1])
                previous_close = info.get('previousClose', hist_data['Close'].iloc[-2])
                delta = current_price - previous_close
                delta_percent = (delta / previous_close) * 100
                st.metric(label="Current Price", value=f"${current_price:,.2f}", delta=f"{delta:,.2f} ({delta_percent:.2f}%)")

            # Tabs
            tab1, tab2, tab3 = st.tabs(["📈 Chart Analysis", "📊 Financials", "📰 News & Sentiment"])

            with tab1:
                # Candlestick Chart
                fig = go.Figure(data=[go.Candlestick(x=hist_data.index,
                                open=hist_data['Open'],
                                high=hist_data['High'],
                                low=hist_data['Low'],
                                close=hist_data['Close'],
                                name='Price')])

                # Add Moving Averages
                hist_data['SMA_50'] = hist_data['Close'].rolling(window=50).mean()
                hist_data['SMA_200'] = hist_data['Close'].rolling(window=200).mean()

                fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['SMA_50'], mode='lines', name='SMA 50', line=dict(color='cyan', width=1)))
                fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['SMA_200'], mode='lines', name='SMA 200', line=dict(color='magenta', width=1)))

                fig.update_layout(
                    title=f'{ticker_symbol} Price Chart',
                    yaxis_title='Price (USD)',
                    xaxis_rangeslider_visible=False,
                    template="plotly_dark",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

                # Volume Chart
                fig_vol = go.Figure(data=[go.Bar(x=hist_data.index, y=hist_data['Volume'], marker_color='#00adb5')])
                fig_vol.update_layout(title='Trading Volume', yaxis_title='Volume', template="plotly_dark", height=300)
                st.plotly_chart(fig_vol, use_container_width=True)

            with tab2:
                st.subheader("Key Statistics")
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                with stats_col1:
                    st.markdown(f"**Market Cap:** {info.get('marketCap', 'N/A'):,}")
                    st.markdown(f"**PE Ratio:** {info.get('trailingPE', 'N/A')}")
                with stats_col2:
                    st.markdown(f"**52 Week High:** {info.get('fiftyTwoWeekHigh', 'N/A')}")
                    st.markdown(f"**52 Week Low:** {info.get('fiftyTwoWeekLow', 'N/A')}")
                with stats_col3:
                    st.markdown(f"**Dividend Yield:** {info.get('dividendYield', 'N/A')}")
                    st.markdown(f"**Sector:** {info.get('sector', 'N/A')}")

                st.subheader("Company Summary")
                st.write(info.get('longBusinessSummary', 'No summary available.'))

            with tab3:
                st.subheader("Latest News & Sentiment Analysis")
                news = ticker_data.news
                
                if news:
                    for article in news[:5]: # Show top 5 news
                        title = article.get('title', 'No Title')
                        link = article.get('link', '#')
                        publisher = article.get('publisher', 'Unknown')
                        
                        # Sentiment Analysis
                        blob = TextBlob(title)
                        sentiment = blob.sentiment.polarity
                        
                        if sentiment > 0:
                            sentiment_label = "Positive 🟢"
                        elif sentiment < 0:
                            sentiment_label = "Negative 🔴"
                        else:
                            sentiment_label = "Neutral ⚪"

                        with st.expander(f"{title} - {publisher}"):
                            st.write(f"**Sentiment:** {sentiment_label} ({sentiment:.2f})")
                            st.markdown(f"[Read more]({link})")
                else:
                    st.info("No recent news found for this ticker.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please enter a ticker symbol to get started.")
