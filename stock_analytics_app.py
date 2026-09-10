import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Real-time Stock Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .header-title {
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Database setup
def init_db():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stock_data (
                    id INTEGER PRIMARY KEY,
                    ticker TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    return conn

# Fetch real-time stock data
@st.cache_data
def fetch_stock_data(ticker, period='1y'):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        info = stock.info
        return hist, info
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None, None

# Calculate technical indicators
def calculate_indicators(df):
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['EMA_12'] = df['Close'].ewm(span=12).mean()
    df['EMA_26'] = df['Close'].ewm(span=26).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    df['RSI'] = calculate_rsi(df['Close'])
    df['ATR'] = calculate_atr(df)
    return df

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

# Main app
st.markdown('<div class="header-title">📊 Real-time Stock Market Analytics</div>', unsafe_allow_html=True)
st.write("Professional-grade stock analysis with real-time data streaming and technical indicators")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Dashboard Configuration")
    selected_tickers = st.multiselect(
        "Select Stock Tickers",
        options=['AAPL', 'GOOGL', 'MSFT', 'TESLA', 'META', 'AMZN', 'NFLX', 'NVDA'],
        default=['AAPL', 'GOOGL'],
        help="Select stocks to analyze"
    )
    
    period = st.selectbox(
        "Time Period",
        options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
        index=3
    )
    
    chart_type = st.radio(
        "Chart Type",
        options=['Candlestick', 'Line'],
        horizontal=True
    )

if not selected_tickers:
    st.warning("Please select at least one ticker from the sidebar")
else:
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Price Charts", "📊 Technical Analysis", "📉 Comparison", "💡 Insights"])
    
    with tab1:
        st.subheader("Stock Price Movement")
        
        for ticker in selected_tickers:
            hist, info = fetch_stock_data(ticker, period)
            
            if hist is not None:
                hist_ind = calculate_indicators(hist.copy())
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    current_price = hist_ind['Close'].iloc[-1]
                    st.metric("Current Price", f"${current_price:.2f}")
                
                with col2:
                    change = hist_ind['Close'].iloc[-1] - hist_ind['Close'].iloc[-5]
                    change_pct = (change / hist_ind['Close'].iloc[-5]) * 100
                    st.metric("5-Day Change", f"{change_pct:.2f}%", delta=f"${change:.2f}")
                
                with col3:
                    high_52w = hist_ind['High'].tail(252).max()
                    st.metric("52-Week High", f"${high_52w:.2f}")
                
                with col4:
                    low_52w = hist_ind['Low'].tail(252).min()
                    st.metric("52-Week Low", f"${low_52w:.2f}")
                
                # Create price chart
                fig = go.Figure()
                
                if chart_type == 'Candlestick':
                    fig.add_trace(go.Candlestick(
                        x=hist_ind.index,
                        open=hist_ind['Open'],
                        high=hist_ind['High'],
                        low=hist_ind['Low'],
                        close=hist_ind['Close'],
                        name=ticker
                    ))
                else:
                    fig.add_trace(go.Scatter(
                        x=hist_ind.index,
                        y=hist_ind['Close'],
                        mode='lines',
                        name=ticker,
                        line=dict(width=2)
                    ))
                
                # Add moving averages
                fig.add_trace(go.Scatter(
                    x=hist_ind.index,
                    y=hist_ind['SMA_20'],
                    mode='lines',
                    name='SMA 20',
                    line=dict(width=1, dash='dash')
                ))
                
                fig.add_trace(go.Scatter(
                    x=hist_ind.index,
                    y=hist_ind['SMA_50'],
                    mode='lines',
                    name='SMA 50',
                    line=dict(width=1, dash='dash')
                ))
                
                fig.update_layout(
                    title=f"{ticker} - Price Chart ({period})",
                    yaxis_title="Price (USD)",
                    xaxis_title="Date",
                    height=500,
                    hovermode='x unified',
                    template='plotly_white'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Technical Analysis")
        
        for ticker in selected_tickers:
            hist, _ = fetch_stock_data(ticker, period)
            
            if hist is not None:
                hist_ind = calculate_indicators(hist.copy())
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # RSI Chart
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(
                        x=hist_ind.index,
                        y=hist_ind['RSI'],
                        mode='lines',
                        name='RSI',
                        line=dict(color='orange', width=2)
                    ))
                    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                    fig_rsi.update_layout(
                        title=f"{ticker} - RSI (14)",
                        yaxis_title="RSI",
                        height=350,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig_rsi, use_container_width=True)
                
                with col2:
                    # MACD Chart
                    fig_macd = go.Figure()
                    fig_macd.add_trace(go.Scatter(
                        x=hist_ind.index,
                        y=hist_ind['MACD'],
                        mode='lines',
                        name='MACD',
                        line=dict(color='blue', width=2)
                    ))
                    fig_macd.add_trace(go.Scatter(
                        x=hist_ind.index,
                        y=hist_ind['Signal'],
                        mode='lines',
                        name='Signal',
                        line=dict(color='red', width=2)
                    ))
                    fig_macd.update_layout(
                        title=f"{ticker} - MACD",
                        yaxis_title="MACD Value",
                        height=350,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig_macd, use_container_width=True)
    
    with tab3:
        st.subheader("Multi-Stock Comparison")
        
        comparison_data = []
        for ticker in selected_tickers:
            hist, info = fetch_stock_data(ticker, period)
            if hist is not None:
                comparison_data.append({
                    'Ticker': ticker,
                    'Current Price': hist['Close'].iloc[-1],
                    '30-Day Return %': ((hist['Close'].iloc[-1] / hist['Close'].iloc[-30]) - 1) * 100,
                    'Volatility %': hist['Close'].pct_change().std() * np.sqrt(252) * 100,
                    'Volume': hist['Volume'].iloc[-1]
                })
        
        if comparison_data:
            df_compare = pd.DataFrame(comparison_data)
            
            # Display comparison table
            st.dataframe(df_compare, use_container_width=True)
            
            # Performance comparison chart
            fig_compare = px.bar(df_compare, x='Ticker', y='30-Day Return %',
                               color='30-Day Return %',
                               color_continuous_scale='RdYlGn',
                               title='30-Day Returns Comparison')
            st.plotly_chart(fig_compare, use_container_width=True)
    
    with tab4:
        st.subheader("📈 Market Insights & Recommendations")
        
        for ticker in selected_tickers:
            hist, info = fetch_stock_data(ticker, period)
            
            if hist is not None:
                hist_ind = calculate_indicators(hist.copy())
                
                st.write(f"### {ticker} - Analysis Summary")
                
                current_rsi = hist_ind['RSI'].iloc[-1]
                current_price = hist_ind['Close'].iloc[-1]
                sma20 = hist_ind['SMA_20'].iloc[-1]
                sma50 = hist_ind['SMA_50'].iloc[-1]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if current_rsi > 70:
                        st.warning("⚠️ **Overbought** - RSI > 70")
                    elif current_rsi < 30:
                        st.success("✅ **Oversold** - RSI < 30 (Potential Buy)")
                    else:
                        st.info("📊 **Neutral** - RSI in normal range")
                
                with col2:
                    if current_price > sma20 > sma50:
                        st.success("📈 **Uptrend** - Price above both SMAs")
                    elif current_price < sma20 < sma50:
                        st.error("📉 **Downtrend** - Price below both SMAs")
                    else:
                        st.info("🔄 **Transitional** - Mixed signals")
                
                with col3:
                    st.metric("Current RSI", f"{current_rsi:.2f}")
                
                st.divider()

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("📊 Data Source: Yahoo Finance (Real-time)")
with col2:
    st.caption(f"⏰ Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col3:
    st.caption("🔄 Refresh: Auto-updates every minute")
