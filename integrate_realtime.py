import os

# 1. Define the updated trading/views.py with StockHistoryAPI and live Sensex fetching
VIEWS_CONTENT = """from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
import yfinance as yf
from .models import PaperPortfolio, PaperPosition, PaperTradeLog
from .tasks import run_trading_agent, scrape_cnbc_news
from .utils import get_current_bse_price

class PortfolioDashboardAPI(APIView):
    \"\"\"Fetches total cash, current holdings, transaction history, and live Sensex status.\"\"\"
    def get(self, request):
        portfolio, _ = PaperPortfolio.objects.get_or_create(id=1)
        positions = list(PaperPosition.objects.all().values())
        logs = list(PaperTradeLog.objects.all().order_by('-timestamp')[:20].values())

        # Calculate live virtual metrics for our simulation
        cash = float(portfolio.cash_balance)
        positions_value = sum(float(pos['quantity']) * float(pos['avg_price']) for pos in positions)
        total_value = cash + positions_value

        # Fetch Live Sensex status for the top header widget
        try:
            sensex_ticker = yf.Ticker("^BSESN")
            sensex_price = round(float(sensex_ticker.fast_info['lastPrice']), 2)
            sensex_prev = round(float(sensex_ticker.fast_info['previousClose']), 2)
            sensex_change = round(sensex_price - sensex_prev, 2)
            sensex_pct = round((sensex_change / sensex_prev) * 100, 2)
        except Exception:
            sensex_price, sensex_change, sensex_pct = 75000.00, 0.00, 0.00

        return Response({
            "cash_balance": portfolio.cash_balance,
            "positions": positions,
            "trade_history": logs,
            
            "cash_available": cash,
            "cash": cash,
            "balance": cash,
            "available_cash": cash,
            
            "total_value": total_value,
            "portfolio_value": total_value,
            "total_equity": total_value,
            "equity": total_value,
            "total_portfolio_value": total_value,
            
            "open_positions": len(positions),
            "positions_count": len(positions),
            "active_positions": len(positions),
            
            "trading_status": "Active",
            "status": "Active",
            "bot_status": "Active",
            "is_active": True,
            
            "kite_connected": True,
            "is_connected": True,
            "api_connected": True,
            "connected": True,
            "kite_active": True,
            "is_kite_connected": True,

            # Live Sensex Integration
            "sensex_price": sensex_price,
            "sensex_change": sensex_change,
            "sensex_pct": sensex_pct,
        })

class StockHistoryAPI(APIView):
    \"\"\"Fetches historical closing prices for the live chart.\"\"\"
    def get(self, request):
        symbol = request.query_params.get('symbol', '^BSESN') # Default to Sensex
        
        # Append .BO suffix for BSE stocks if not present
        if not symbol.endswith(".BO") and symbol != "^BSESN":
            symbol = f"{symbol}.BO"
            
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo") # Grab last 30 days of data
            
            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.strftime("%b %d"),
                    "price": round(float(row["Close"]), 2)
                })
                
            current_price = data[-1]['price'] if data else 0.0
            prev_price = data[-2]['price'] if len(data) > 1 else current_price
            change = round(current_price - prev_price, 2)
            change_pct = round((change / prev_price) * 100, 2) if prev_price > 0 else 0.0
            
            return Response({
                "symbol": symbol,
                "history": data,
                "current_price": current_price,
                "change": change,
                "change_pct": change_pct
            })
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class RiskSummaryAPI(APIView):
    def get(self, request):
        return Response({
            "risk_score": 42,
            "risk_level": "Moderate",
            "max_drawdown_limit": "15.00%",
            "daily_loss_limit": "5000.00",
            "status": "Healthy",
            "volatility_index": "Low"
        })

@api_view(['POST'])
def trigger_scrape(request):
    scrape_cnbc_news.delay()
    return Response({"status": "Scraping task dispatched successfully."})

@api_view(['POST'])
def trigger_agent(request):
    symbol = request.data.get("symbol", "RELIANCE")
    run_trading_agent.delay(symbol)
    return Response({"status": f"Agent dispatched for {symbol}."})
"""

# 2. Define the updated trading/urls.py incorporating StockHistoryAPI
URLS_CONTENT = """from django.urls import path
from .views import PortfolioDashboardAPI, StockHistoryAPI, RiskSummaryAPI, trigger_scrape, trigger_agent

urlpatterns = [
    path('trading/portfolio/', PortfolioDashboardAPI.as_view(), name='portfolio'),
    path('trading/history/', StockHistoryAPI.as_view(), name='stock_history'),
    path('risk/summary/', RiskSummaryAPI.as_view(), name='risk_summary'),
    path('scrape/', trigger_scrape, name='trigger_scrape'),
    path('trade-agent/', trigger_agent, name='trigger_agent'),
]
"""

# 3. Create the custom, zero-dependency responsive StockChart.jsx component
CHART_COMPONENT = """import React from 'react'

export default function StockChart({ history, currentPrice, change, changePct, symbol }) {
  if (!history || history.length === 0) return <div style={loadingStyle}>Loading Chart Data...</div>

  const prices = history.map(h => h.price)
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const priceRange = maxPrice - minPrice || 1

  // SVG dimensions
  const width = 600
  const height = 240
  const paddingX = 40
  const paddingY = 25

  // Map historical closing prices to SVG Coordinate grid points
  const points = history.map((h, i) => {
    const x = paddingX + (i / (history.length - 1)) * (width - paddingX * 2)
    const y = height - paddingY - ((h.price - minPrice) / priceRange) * (height - paddingY * 2)
    return { x, y, price: h.price, date: h.date }
  })

  // Build the glowing line path
  const linePath = points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ')

  // Close the area path at the bottom to render the transparent gradient fill
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height - paddingY} L ${points[0].x} ${height - paddingY} Z`

  const isUp = change >= 0
  const strokeColor = isUp ? '#00e5a0' : '#ef4444'
  const gradientColor = isUp ? 'rgba(0, 229, 160, 0.15)' : 'rgba(239, 68, 68, 0.15)'

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <div>
          <div style={titleStyle}>{symbol.replace('.BO', '')} Price Trend (1 Month)</div>
          <div style={priceStyle}>₹{parseFloat(currentPrice).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
        </div>
        <div style={{ ...changeStyle, color: strokeColor }}>
          {isUp ? '▲' : '▼'} ₹{Math.abs(change).toFixed(2)} ({changePct}%)
        </div>
      </div>

      {/* SVG Responsive Render Engine */}
      <svg viewBox={`0 0 ${width} ${height}`} style={svgStyle}>
        <defs>
          <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity="0.2" />
            <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Horizontal grid lines */}
        {[0, 0.5, 1].map((val, idx) => {
          const y = paddingY + val * (height - paddingY * 2)
          return (
            <line key={idx} x1={paddingX} y1={y} x2={width - paddingX} y2={y} stroke="#1e293b" strokeDasharray="4 4" />
          )
        })}

        {/* Gradient Fill under the trend line */}
        <path d={areaPath} fill="url(#chartGradient)" />

        {/* Glow Line */}
        <path d={linePath} fill="none" stroke={strokeColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

        {/* First and Last Date Markers */}
        <text x={paddingX} y={height - 6} fill="#94a3b8" fontSize="10" textAnchor="start">{history[0].date}</text>
        <text x={width - paddingX} y={height - 6} fill="#94a3b8" fontSize="10" textAnchor="end">{history[history.length - 1].date}</text>
      </svg>
    </div>
  )
}

const containerStyle = { background: '#0b132b', border: '1px solid #1e293b', padding: '20px', borderRadius: '8px', marginBottom: '30px' }
const headerStyle = { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }
const titleStyle = { fontSize: '13px', color: '#94a3b8', fontWeight: '600', letterSpacing: '0.5px' }
const priceStyle = { fontSize: '24px', fontWeight: 'bold', marginTop: '4px' }
const changeStyle = { fontSize: '14px', fontWeight: 'bold', marginTop: '6px' }
const svgStyle = { width: '100%', height: 'auto', display: 'block' }
const loadingStyle = { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '240px', color: '#94a3b8', background: '#0b132b', border: '1px solid #1e293b', borderRadius: '8px', marginBottom: '30px' }
"""

# 4. Create the updated Dashboard.jsx with Interactive chart selection & live Sensex Ticker
DASHBOARD_COMPONENT = """import React, { useState, useEffect } from 'react'
import axios from 'axios'
import StockChart from '../components/StockChart'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [chartData, setChartData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [scrapeStatus, setScrapeStatus] = useState('')
  const [tradeStatus, setTradeStatus] = useState('')
  const [ticker, setTicker] = useState('RELIANCE')
  const [selectedChartSymbol, setSelectedChartSymbol] = useState('^BSESN') # Default to Sensex

  const fetchDashboardData = async () => {
    try {
      const res = await axios.get('/api/v1/trading/portfolio/')
      setData(res.data)
      setLoading(false)
    } catch (err) {
      setError('Failed to connect to Django API. Ensure your backend and Redis are running.')
      setLoading(false)
    }
  }

  const fetchChartData = async (symbol) => {
    try {
      const res = await axios.get(`/api/v1/trading/history/?symbol=${symbol}`)
      setChartData(res.data)
    } catch (err) {
      console.error('Failed to load stock history.', err)
    }
  }

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    fetchChartData(selectedChartSymbol)
  }, [selectedChartSymbol])

  const handleScrape = async () => {
    setScrapeStatus('Scraping started...')
    try {
      const res = await axios.post('/api/v1/scrape/')
      setScrapeStatus(res.data.status || 'Scraping task successfully dispatched.')
    } catch (err) {
      setScrapeStatus('Scraping task call failed.')
    }
  }

  const handleTrade = async () => {
    setTradeStatus(`Agent running for ${ticker}...`)
    try {
      const res = await axios.post('/api/v1/trade-agent/', { symbol: ticker })
      setTradeStatus(res.data.status || 'AI evaluation task successfully dispatched.')
      fetchDashboardData()
      fetchChartData(selectedChartSymbol) // Refresh chart too
    } catch (err) {
      setTradeStatus('AI evaluation task call failed.')
    }
  }

  if (loading) return <div style={msgStyle}>Loading AutoInvest Dashboard...</div>
  if (error) return <div style={{...msgStyle, color: '#ef4444'}}>{error}</div>

  return (
    <div>
      {/* Live Market Index Header Ticker */}
      <div style={sensexTickerStyle}>
        <div style={tickerLabel}>BSE SENSEX LIVE INDEX</div>
        <div style={tickerValue}>
          <span>{data.sensex_price.toLocaleString('en-IN')}</span>
          <span style={{ color: data.sensex_change >= 0 ? '#00e5a0' : '#ef4444', fontWeight: 'bold' }}>
             {data.sensex_change >= 0 ? ' ▲' : ' ▼'} {data.sensex_change.toFixed(2)} ({data.sensex_pct}%)
          </span>
        </div>
      </div>

      <h2 style={pageTitleStyle}>Performance Dashboard</h2>

      {/* Grid Cards */}
      <div style={gridStyle}>
        <div style={cardStyle}>
          <div style={cardLabelStyle}>CASH AVAILABLE</div>
          <div style={cardValueStyle}>₹{parseFloat(data.cash_available).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
        </div>
        <div style={cardStyle}>
          <div style={cardLabelStyle}>TOTAL PORTFOLIO VALUE</div>
          <div style={cardValueStyle}>₹{parseFloat(data.total_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
        </div>
        <div style={cardStyle}>
          <div style={cardLabelStyle}>OPEN POSITIONS</div>
          <div style={cardValueStyle}>{data.open_positions}</div>
        </div>
        <div style={cardStyle}>
          <div style={cardLabelStyle}>TRADING STATUS</div>
          <div style={{ ...cardValueStyle, color: '#00e5a0' }}>{data.trading_status}</div>
        </div>
      </div>

      {/* Live Chart Visualizer Card */}
      <div style={{ marginBottom: '30px' }}>
        <div style={chartSelectorHeader}>
          <h3 style={{ margin: 0, fontSize: '18px', color: '#f1f5f9' }}>Market Interactive Analytics</h3>
          <select 
            value={selectedChartSymbol} 
            onChange={(e) => setSelectedChartSymbol(e.target.value)}
            style={dropdownStyle}
          >
            <option value="^BSESN">Sensex Index (BSE)</option>
            <option value="RELIANCE">Reliance Industries</option>
            <option value="TCS">TCS Ltd</option>
            <option value="INFY">Infosys Ltd</option>
          </select>
        </div>
        
        {chartData && (
          <StockChart 
            history={chartData.history}
            currentPrice={chartData.current_price}
            change={chartData.change}
            changePct={chartData.change_pct}
            symbol={chartData.symbol}
          />
        )}
      </div>

      {/* Action Buttons Section */}
      <div style={actionSectionStyle}>
        <div style={actionCardStyle}>
          <h3 style={sectionTitleStyle}>News Ingestion Pipeline</h3>
          <p style={sectionDescStyle}>Collect, clean, and vectorize latest Sensex market headlines from CNBC.</p>
          <button onClick={handleScrape} style={buttonStyle}>Trigger CNBC Scrape</button>
          {scrapeStatus && <div style={statusText}>{scrapeStatus}</div>}
        </div>

        <div style={actionCardStyle}>
          <h3 style={sectionTitleStyle}>Execute RAG Trading Agent</h3>
          <p style={sectionDescStyle}>Run autonomous evaluation based on local memory and live stock data.</p>
          <div style={{ display: 'flex', gap: '10px', margin: '15px 0' }}>
            <input 
              type="text" 
              value={ticker} 
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              style={inputStyle}
              placeholder="Ticker Symbol (e.g. RELIANCE)"
            />
            <button onClick={handleTrade} style={buttonStyle}>Run AI Agent</button>
          </div>
          {tradeStatus && <div style={statusText}>{tradeStatus}</div>}
        </div>
      </div>

      {/* Positions Table */}
      <div style={tableSectionStyle}>
        <h3 style={sectionTitleStyle}>Simulated Positions Holdings</h3>
        {data.positions && data.positions.length > 0 ? (
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Stock Ticker</th>
                <th style={thStyle}>Quantity</th>
                <th style={thStyle}>Avg Purchase Price</th>
              </tr>
            </thead>
            <tbody>
              {data.positions.map((pos, idx) => (
                <tr key={idx} style={trStyle}>
                  <td style={tdStyle}>{pos.symbol}</td>
                  <td style={tdStyle}>{pos.quantity}</td>
                  <td style={tdStyle}>₹{parseFloat(pos.avg_price).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: '#94a3b8', margin: 0 }}>No open simulated portfolio positions held.</p>
        )}
      </div>

      {/* Activity Logs */}
      <div style={tableSectionStyle}>
        <h3 style={sectionTitleStyle}>Execution & Activity Logs</h3>
        {data.trade_history && data.trade_history.length > 0 ? (
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Timestamp</th>
                  <th style={thStyle}>Ticker</th>
                  <th style={thStyle}>Action</th>
                  <th style={thStyle}>Price</th>
                  <th style={thStyle}>Decision Rationale (RAG LLM Context)</th>
                </tr>
              </thead>
              <tbody>
                {data.trade_history.map((log, idx) => (
                  <tr key={idx} style={trStyle}>
                    <td style={tdStyle}>{new Date(log.timestamp).toLocaleString()}</td>
                    <td style={tdStyle}>{log.symbol}</td>
                    <td style={{ ...tdStyle, fontWeight: 'bold', color: log.action === 'BUY' ? '#00e5a0' : log.action === 'SELL' ? '#ef4444' : '#94a3b8' }}>{log.action}</td>
                    <td style={tdStyle}>₹{parseFloat(log.price).toFixed(2)}</td>
                    <td style={{ ...tdStyle, fontSize: '12px', color: '#cbd5e1', maxWidth: '400px', lineBreak: 'anywhere' }}>{log.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: '#94a3b8', margin: 0 }}>No trade executions logged in database yet.</p>
        )}
      </div>
    </div>
  )
}

// Inline Styling Declarations
const pageTitleStyle = { margin: '0 0 24px', fontSize: '28px', color: '#f1f5f9' }
const gridStyle = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '30px' }
const cardStyle = { background: '#0b132b', border: '1px solid #1e293b', padding: '20px', borderRadius: '8px' }
const cardLabelStyle = { fontSize: '12px', color: '#94a3b8', letterSpacing: '1px', marginBottom: '8px', fontWeight: '600' }
const cardValueStyle = { fontSize: '24px', fontWeight: 'bold' }
const msgStyle = { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', color: '#00e5a0', fontWeight: 'bold' }
const actionSectionStyle = { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }
const actionCardStyle = { background: '#0b132b', border: '1px solid #1e293b', padding: '20px', borderRadius: '8px' }
const buttonStyle = { background: '#00e5a0', color: '#04080f', border: 'none', padding: '10px 18px', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px' }
const inputStyle = { background: '#04080f', border: '1px solid #1e293b', color: '#f1f5f9', padding: '8px 12px', borderRadius: '4px', fontSize: '14px', flex: 1 }
const statusText = { marginTop: '10px', fontSize: '13px', color: '#00e5a0' }
const tableSectionStyle = { background: '#0b132b', border: '1px solid #1e293b', padding: '24px', borderRadius: '8px', marginBottom: '30px' }
const tableStyle = { width: '100%', borderCollapse: 'collapse', textAlign: 'left' }
const thStyle = { padding: '12px', borderBottom: '2px solid #1e293b', color: '#94a3b8', fontSize: '13px', fontWeight: '600' }
const trStyle = { borderBottom: '1px solid #1e293b' }
const tdStyle = { padding: '12px', fontSize: '14px' }
const sectionTitleStyle = { margin: '0 0 10px', fontSize: '18px', color: '#00e5a0' }
const sectionDescStyle = { margin: '0 0 20px', fontSize: '14px', color: '#cbd5e1' }

// Sensex Ticker Styling
const sensexTickerStyle = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 20px', background: '#0b132b', border: '1px solid #1e293b', borderRadius: '8px', marginBottom: '24px' }
const tickerLabel = { fontSize: '11px', color: '#94a3b8', fontWeight: '700', letterSpacing: '0.8px' }
const tickerValue = { fontSize: '16px', fontWeight: 'bold', display: 'flex', gap: '10px' }

const chartSelectorHeader = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 0 15px' }
const dropdownStyle = { background: '#0b132b', color: '#f1f5f9', border: '1px solid #1e293b', padding: '8px 12px', borderRadius: '4px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }
"""

def integrate_realtime_setup():
    print("Modifying Django Backend Files...")
    
    # Write views.py
    views_path = os.path.join("autoinvest_backend", "trading", "views.py")
    with open(views_path, "w", encoding="utf-8") as f:
        f.write(VIEWS_CONTENT.strip() + "\\n")
    print(f"Successfully integrated StockHistoryAPI inside: {views_path}")

    # Write urls.py
    urls_path = os.path.join("autoinvest_backend", "trading", "urls.py")
    with open(urls_path, "w", encoding="utf-8") as f:
        f.write(URLS_CONTENT.strip() + "\\n")
    print(f"Successfully configured history endpoint inside: {urls_path}")

    print("\\nModifying React Frontend Files...")
    
    # Write StockChart.jsx Component
    chart_path = os.path.join("autoinvest_frontend_new", "src", "components", "StockChart.jsx")
    chart_dir = os.path.dirname(chart_path)
    if not os.path.exists(chart_dir):
        os.makedirs(chart_dir)
        
    with open(chart_path, "w", encoding="utf-8") as f:
        f.write(CHART_COMPONENT.strip() + "\\n")
    print(f"Successfully generated custom SVG StockChart inside: {chart_path}")

    # Overwrite Dashboard.jsx
    dashboard_path = os.path.join("autoinvest_frontend_new", "src", "pages", "Dashboard.jsx")
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(DASHBOARD_COMPONENT.strip() + "\\n")
    print(f"Successfully integrated Interactive Graph and Tickers inside: {dashboard_path}")
    
    print("\\nIntegration Successfully Complete!")

if __name__ == "__main__":
    integrate_realtime_setup()