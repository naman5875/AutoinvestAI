import os
import zipfile

# Define the frontend files and directory structure
FRONTEND_FILES = {
    "package.json": """{
  "name": "autoinvest-frontend-new",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
""",

    "vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
""",

    "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AutoInvest AI Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
    <style>
      body {
        margin: 0;
        font-family: 'Space Grotesk', sans-serif;
        background-color: #04080f;
        color: #f1f5f9;
      }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",

    "src/index.css": """:root {
  --bg-dark: #04080f;
  --card-bg: #0b132b;
  --accent-green: #00e5a0;
  --accent-blue: #0077b6;
  --text-light: #f1f5f9;
  --text-muted: #94a3b8;
  --border: #1e293b;
}

body {
  margin: 0;
  background-color: var(--bg-dark);
  color: var(--text-light);
  font-family: 'Space Grotesk', sans-serif;
}

/* Custom Scrollbar for trade logs */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: #04080f;
}
::-webkit-scrollbar-thumb {
  background: #1e293b;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #00e5a0;
}
""",

    "src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
""",

    "src/App.jsx": """import React from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Risk from './pages/Risk'

export default function App() {
  const location = useLocation()

  return (
    <div style={appContainerStyle}>
      {/* Header Navigation */}
      <header style={headerStyle}>
        <div style={logoStyle}>AutoInvest AI</div>
        <nav style={navStyle}>
          <Link to="/" style={location.pathname === '/' ? activeLinkStyle : linkStyle}>Dashboard</Link>
          <Link to="/risk" style={location.pathname === '/risk' ? activeLinkStyle : linkStyle}>Risk Control</Link>
        </nav>
      </header>

      {/* Main Content */}
      <main style={mainStyle}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/risk" element={<Risk />} />
        </Routes>
      </main>

      {/* Status Footer */}
      <footer style={footerStyle}>
        <div style={statusDotContainer}>
          <span style={statusDot}></span> Django API Status: Connected
        </div>
        <div>v1.0.0 (Simulated Paper Trading Mode)</div>
      </footer>
    </div>
  )
}

const appContainerStyle = { display: 'flex', flexDirection: 'column', minHeight: '100vh', background: '#04080f' }
const headerStyle = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', background: '#0b132b', borderBottom: '1px solid #1e293b' }
const logoStyle = { fontSize: '20px', fontWeight: 'bold', color: '#00e5a0' }
const navStyle = { display: 'flex', gap: '20px' }
const linkStyle = { color: '#94a3b8', textDecoration: 'none', fontSize: '14px', fontWeight: '500' }
const activeLinkStyle = { color: '#00e5a0', textDecoration: 'none', fontSize: '14px', fontWeight: '700' }
const mainStyle = { flex: 1, padding: '24px', maxWidth: '1200px', margin: '0 auto', width: '100%' }
const footerStyle = { display: 'flex', justifyContent: 'space-between', padding: '12px 24px', background: '#0b132b', borderTop: '1px solid #1e293b', fontSize: '12px', color: '#94a3b8' }
const statusDotContainer = { display: 'flex', alignItems: 'center', gap: '6px' }
const statusDot = { width: '8px', height: '8px', background: '#00e5a0', borderRadius: '50%' }
""",

    "src/pages/Dashboard.jsx": """import React, { useState, useEffect } from 'react'
import axios from 'axios'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [scrapeStatus, setScrapeStatus] = useState('')
  const [tradeStatus, setTradeStatus] = useState('')
  const [ticker, setTicker] = useState('RELIANCE')

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

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 5000) // Poll every 5 seconds
    return () => clearInterval(interval)
  }, [])

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
    } catch (err) {
      setTradeStatus('AI evaluation task call failed.')
    }
  }

  if (loading) return <div style={msgStyle}>Loading AutoInvest Dashboard...</div>
  if (error) return <div style={{...msgStyle, color: '#ef4444'}}>{error}</div>

  return (
    <div>
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
""",

    "src/pages/Risk.jsx": """import React, { useState, useEffect } from 'react'
import axios from 'axios'

export default function Risk() {
  const [risk, setRisk] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchRisk = async () => {
      try {
        const res = await axios.get('/api/v1/risk/summary/')
        setRisk(res.data)
        setLoading(false)
      } catch (err) {
        setLoading(false)
      }
    }
    fetchRisk()
  }, [])

  if (loading) return <div style={msgStyle}>Loading Risk Parameters...</div>

  return (
    <div>
      <h2 style={{ margin: '0 0 24px', fontSize: '28px' }}>Risk Management Control</h2>
      
      <div style={containerStyle}>
        <div style={rowStyle}>
          <strong>Risk Evaluation Score:</strong>
          <span style={{ color: '#00e5a0', fontWeight: 'bold' }}>{risk?.risk_score} / 100</span>
        </div>
        <div style={rowStyle}>
          <strong>Assigned Profile:</strong>
          <span>{risk?.risk_level}</span>
        </div>
        <div style={rowStyle}>
          <strong>Max Drawdown Allowance:</strong>
          <span>{risk?.max_drawdown_limit}</span>
        </div>
        <div style={rowStyle}>
          <strong>Daily Loss Safety Stop:</strong>
          <span>₹{parseFloat(risk?.daily_loss_limit).toLocaleString('en-IN')}</span>
        </div>
        <div style={rowStyle}>
          <strong>Current Status:</strong>
          <span style={{ color: '#00e5a0', fontWeight: 'bold' }}>{risk?.status}</span>
        </div>
      </div>
    </div>
  )
}

const msgStyle = { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh', color: '#00e5a0' }
const containerStyle = { background: '#0b132b', border: '1px solid #1e293b', padding: '24px', borderRadius: '8px', maxWidth: '600px' }
const rowStyle = { display: 'flex', justifyContent: 'space-between', padding: '14px 0', borderBottom: '1px solid #1e293b' }
"""
}

def create_frontend_and_zip():
    project_dir = "autoinvest_frontend_new"
    zip_filename = "frontend_project.zip"
    
    print("Generating React Frontend files on disk...")
    # Create files on disk
    for file_path, content in FRONTEND_FILES.items():
        full_path = os.path.join(project_dir, file_path)
        directory = os.path.dirname(full_path)
        
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
            
    print(f"Extract successful! React files written to './{project_dir}/'")
    
    print(f"Creating ZIP archive '{zip_filename}'...")
    # Pack everything into a zip file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                archive_path = os.path.relpath(file_path, project_dir)
                zipf.write(file_path, archive_path)
                
    print(f"Zip successful! Archive created at './{zip_filename}'")

if __name__ == "__main__":
    create_frontend_and_zip()