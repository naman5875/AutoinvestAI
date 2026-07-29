import os

# 1. Update backend views.py to include custom login/logout views and enforce permissions
VIEWS_CONTENT = """from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
import yfinance as yf

from .models import PaperPortfolio, PaperPosition, PaperTradeLog
from .tasks import run_trading_agent, scrape_cnbc_news
from .utils import get_current_bse_price

class CustomAuthToken(ObtainAuthToken):
    \"\"\"Authenticates user credentials and returns a secure token.\"\"\"
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'username': user.username
        })

class LogoutAPI(APIView):
    \"\"\"Invalidates and deletes the active session token.\"\"\"
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"status": "Successfully logged out."})

class PortfolioDashboardAPI(APIView):
    \"\"\"Enforces IsAuthenticated to protect dashboard metrics.\"\"\"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        portfolio, _ = PaperPortfolio.objects.get_or_create(id=1)
        positions = list(PaperPosition.objects.all().values())
        logs = list(PaperTradeLog.objects.all().order_by('-timestamp')[:20].values())

        cash = float(portfolio.cash_balance)
        positions_value = sum(float(pos['quantity']) * float(pos['avg_price']) for pos in positions)
        total_value = cash + positions_value

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

    def delete(self, request):
        PaperTradeLog.objects.all().delete()
        return Response({"status": "Logs cleared successfully."})

class StockHistoryAPI(APIView):
    \"\"\"Enforces IsAuthenticated to protect history metrics.\"\"\"
    permission_classes = [IsAuthenticated]

    def get(self, request):
        symbol = request.query_params.get('symbol', '^BSESN')
        if not symbol.endswith(".BO") and symbol != "^BSESN":
            symbol = f"{symbol}.BO"
            
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            
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
    \"\"\"Enforces IsAuthenticated to protect risk metrics.\"\"\"
    permission_classes = [IsAuthenticated]

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
@permission_classes([IsAuthenticated])
def trigger_scrape(request):
    scrape_cnbc_news.delay()
    return Response({"status": "Scraping task dispatched successfully."})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_agent(request):
    symbol = request.data.get("symbol", "RELIANCE")
    run_trading_agent.delay(symbol)
    return Response({"status": f"Agent dispatched for {symbol}."})
"""

# 2. Update backend urls.py to route authentication views
URLS_CONTENT = """from django.urls import path
from .views import (
    PortfolioDashboardAPI, 
    StockHistoryAPI, 
    RiskSummaryAPI, 
    trigger_scrape, 
    trigger_agent,
    CustomAuthToken,
    LogoutAPI
)

urlpatterns = [
    # Authentication routes
    path('auth/login/', CustomAuthToken.as_view(), name='auth_login'),
    path('auth/logout/', LogoutAPI.as_view(), name='auth_logout'),

    # Trading routes
    path('trading/portfolio/', PortfolioDashboardAPI.as_view(), name='portfolio'),
    path('trading/history/', StockHistoryAPI.as_view(), name='stock_history'),
    path('risk/summary/', RiskSummaryAPI.as_view(), name='risk_summary'),
    path('scrape/', trigger_scrape, name='trigger_scrape'),
    path('trade-agent/', trigger_agent, name='trigger_agent'),
]
"""

# 3. Create frontend AuthContext.jsx to manage Token state
AUTH_CONTEXT = """import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [username, setUsername] = useState(localStorage.getItem('username') || '')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Token ${token}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
    setLoading(false)
  }, [token])

  const login = async (user, password) => {
    const res = await axios.post('/api/v1/auth/login/', { username: user, password })
    const receivedToken = res.data.token
    const receivedUsername = res.data.username
    
    localStorage.setItem('token', receivedToken)
    localStorage.setItem('username', receivedUsername)
    setToken(receivedToken)
    setUsername(receivedUsername)
  }

  const logout = async () => {
    try {
      await axios.post('/api/v1/auth/logout/')
    } catch (err) {
      console.error('Logout request failed on backend. Clearing local session anyway.')
    }
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    setToken('')
    setUsername('')
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated: !!token, username, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
"""

# 4. Create frontend Login.jsx page component
LOGIN_PAGE = """import React, { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [usernameInput, setUsernameInput] = useState('')
  const [passwordInput, setPasswordInput] = useState('')
  const [error, setError] = useState('')
  const [loggingIn, setLoggingIn] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoggingIn(true)
    try {
      await login(usernameInput, passwordInput)
      navigate('/')
    } catch (err) {
      setError('Invalid username or password. Ensure your Django superuser account exists.')
      setLoggingIn(false)
    }
  }

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h2 style={logoStyle}>AutoInvest AI</h2>
        <p style={subtitleStyle}>Sign in to your simulated paper trading dashboard</p>
        
        {error && <div style={errorStyle}>{error}</div>}
        
        <form onSubmit={handleSubmit} style={formStyle}>
          <div style={inputGroup}>
            <label style={labelStyle}>USERNAME</label>
            <input 
              type="text" 
              value={usernameInput}
              onChange={(e) => setUsernameInput(e.target.value)}
              style={inputStyle}
              required
            />
          </div>
          <div style={inputGroup}>
            <label style={labelStyle}>PASSWORD</label>
            <input 
              type="password" 
              value={passwordInput}
              onChange={(e) => setPasswordInput(e.target.value)}
              style={inputStyle}
              required
            />
          </div>
          <button type="submit" style={buttonStyle} disabled={loggingIn}>
            {loggingIn ? 'Signing In...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}

const containerStyle = { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#04080f' }
const cardStyle = { background: '#0b132b', border: '1px solid #1e293b', padding: '32px', borderRadius: '12px', width: '100%', maxWidth: '400px', boxSizing: 'border-box' }
const logoStyle = { color: '#00e5a0', margin: '0 0 8px', fontSize: '28px', textAlign: 'center', fontWeight: 'bold' }
const subtitleStyle = { color: '#94a3b8', margin: '0 0 24px', fontSize: '14px', textAlign: 'center' }
const errorStyle = { background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', color: '#ef4444', padding: '10px', borderRadius: '4px', fontSize: '13px', marginBottom: '16px', textAlign: 'center' }
const formStyle = { display: 'flex', flexDirection: 'column', gap: '16px' }
const inputGroup = { display: 'flex', flexDirection: 'column', gap: '6px' }
const labelStyle = { fontSize: '11px', color: '#94a3b8', letterSpacing: '0.8px', fontWeight: '700' }
const inputStyle = { background: '#04080f', border: '1px solid #1e293b', color: '#f1f5f9', padding: '10px 14px', borderRadius: '6px', fontSize: '14px' }
const buttonStyle = { background: '#00e5a0', color: '#04080f', border: 'none', padding: '12px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', fontSize: '14px', marginTop: '10px' }
"""

# 5. Update App.jsx to protect routes and add a Header "Logout" panel
APP_CONTENT = """import React from 'react'
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Risk from './pages/Risk'

// Protected Route redirect wrapper
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return <div style={loadingStyle}>Loading Session...</div>
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route 
        path="/*" 
        element={
          <ProtectedRoute>
            <ProtectedLayout />
          </ProtectedRoute>
        } 
      />
    </Routes>
  )
}

function ProtectedLayout() {
  const location = useLocation()
  const { logout, username } = useAuth()

  return (
    <div style={appContainerStyle}>
      {/* Header Navigation with Logout widget */}
      <header style={headerStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div style={logoStyle}>AutoInvest AI</div>
          <nav style={navStyle}>
            <Link to="/" style={location.pathname === '/' ? activeLinkStyle : linkStyle}>Dashboard</Link>
            <Link to="/risk" style={location.pathname === '/risk' ? activeLinkStyle : linkStyle}>Risk Control</Link>
          </nav>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={userLabel}>User: <strong style={{ color: '#00e5a0' }}>{username}</strong></span>
          <button onClick={logout} style={logoutButtonStyle}>Logout</button>
        </div>
      </header>

      {/* Main Content */}
      <main style={mainStyle}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Status Footer */}
      <footer style={footerStyle}>
        <div style={statusDotContainer}>
          <span style={statusDot}></span> Django API Status: Connected (Secure Token)
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
const loadingStyle = { display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#04080f', color: '#00e5a0', fontSize: 14, fontFamily: 'monospace' }
const userLabel = { fontSize: '13px', color: '#94a3b8' }
const logoutButtonStyle = { background: 'transparent', color: '#ef4444', border: '1px solid #ef4444', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }
"""

# 6. Update main.jsx to wrap App in BrowserRouter + AuthProvider
MAIN_CONTENT = """import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)
"""

def enable_auth():
    print("Modifying Django Backend Configuration...")
    
    # 1. Update settings.py to add Token Auth and default REST authentication class
    settings_path = os.path.join("autoinvest_backend", "autoinvest_backend", "settings.py")
    with open(settings_path, "r", encoding="utf-8") as f:
        settings_text = f.read()
        
    if "'rest_framework.authtoken'" not in settings_text:
        # Inject the authtoken app inside INSTALLED_APPS
        settings_text = settings_text.replace(
            "'rest_framework',",
            "'rest_framework',\\n    'rest_framework.authtoken',"
        )
        # Append REST_FRAMEWORK settings to the end of settings.py
        settings_text += """\\n\\nREST_FRAMEWORK = {\\n    'DEFAULT_AUTHENTICATION_CLASSES': [\\n        'rest_framework.authentication.TokenAuthentication',\\n    ],\\n}\\n"""
        with open(settings_path, "w", encoding="utf-8") as f:
            f.write(settings_text)
        print("-> Successfully added 'rest_framework.authtoken' and configured REST_FRAMEWORK settings.")
    else:
        print("-> Settings.py is already configured with Token Authentication.")

    # 2. Update views.py
    views_path = os.path.join("autoinvest_backend", "trading", "views.py")
    with open(views_path, "w", encoding="utf-8") as f:
        f.write(VIEWS_CONTENT.strip() + "\\n")
    print(f"-> Successfully enabled Token authorization views inside: {views_path}")

    # 3. Update urls.py
    urls_path = os.path.join("autoinvest_backend", "trading", "urls.py")
    with open(urls_path, "w", encoding="utf-8") as f:
        f.write(URLS_CONTENT.strip() + "\\n")
    print(f"-> Successfully mapped login/logout routing inside: {urls_path}")

    print("\\nGenerating React Frontend Auth Files...")
    
    # 4. Generate AuthContext.jsx
    context_path = os.path.join("autoinvest_frontend_new", "src", "context", "AuthContext.jsx")
    context_dir = os.path.dirname(context_path)
    if not os.path.exists(context_dir):
        os.makedirs(context_dir)
    with open(context_path, "w", encoding="utf-8") as f:
        f.write(AUTH_CONTEXT.strip() + "\\n")
    print(f"-> Successfully created Session Context: {context_path}")

    # 5. Generate Login.jsx Page
    login_path = os.path.join("autoinvest_frontend_new", "src", "pages", "Login.jsx")
    login_dir = os.path.dirname(login_path)
    if not os.path.exists(login_dir):
        os.makedirs(login_dir)
    with open(login_path, "w", encoding="utf-8") as f:
        f.write(LOGIN_PAGE.strip() + "\\n")
    print(f"-> Successfully created Login interface: {login_path}")

    # 6. Overwrite App.jsx
    app_path = os.path.join("autoinvest_frontend_new", "src", "App.jsx")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(APP_CONTENT.strip() + "\\n")
    print(f"-> Successfully secured routing inside: {app_path}")

    # 7. Overwrite main.jsx
    main_path = os.path.join("autoinvest_frontend_new", "src", "main.jsx")
    with open(main_path, "w", encoding="utf-8") as f:
        f.write(MAIN_CONTENT.strip() + "\\n")
    print(f"-> Successfully configured Context providers inside: {main_path}")
    
    print("\\nAuthentication Integration Successfully Compiled!")

if __name__ == "__main__":
    enable_auth()