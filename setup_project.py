import os
import zipfile

# Define the project file structure and contents
PROJECT_FILES = {
    "requirements.txt": """django>=4.2,<5.0
djangorestframework
django-cors-headers
celery
redis
beautifulsoup4
requests
yfinance
langchain
langchain-community
langchain-openai
chromadb
""",

    "manage.py": """#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoinvest_backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
""",

    "autoinvest_backend/__init__.py": """from .celery import app as celery_app

__all__ = ('celery_app',)
""",

    "autoinvest_backend/celery.py": """import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoinvest_backend.settings')

app = Celery('autoinvest_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
""",

    "autoinvest_backend/settings.py": """import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'trading',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'autoinvest_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'autoinvest_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True 

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
""",

    "autoinvest_backend/urls.py": """from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/trading/', include('trading.urls')),
]
""",

    "autoinvest_backend/wsgi.py": """import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoinvest_backend.settings')
application = get_wsgi_application()
""",

    "trading/__init__.py": "",

    "trading/apps.py": """from django.apps import AppConfig

class TradingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trading'
""",

    "trading/models.py": """from django.db import models

class PaperPortfolio(models.Model):
    cash_balance = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)

    def __str__(self):
        return f"Portfolio Balance: ₹{self.cash_balance}"

class PaperPosition(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    quantity = models.PositiveIntegerField(default=0)
    avg_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.symbol} - {self.quantity} shares @ ₹{self.avg_price}"

class PaperTradeLog(models.Model):
    ACTIONS = [('BUY', 'Buy'), ('SELL', 'Sell'), ('HOLD', 'Hold')]
    timestamp = models.DateTimeField(auto_now_add=True)
    symbol = models.CharField(max_length=20)
    action = models.CharField(max_length=10, choices=ACTIONS)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()

    def __str__(self):
        return f"[{self.action}] {self.symbol} - {self.quantity} shares"
""",

    "trading/utils.py": """import yfinance as yf
from .models import PaperPortfolio, PaperPosition, PaperTradeLog

def get_current_bse_price(symbol):
    try:
        ticker_symbol = symbol if symbol.endswith(".BO") else f"{symbol}.BO"
        ticker = yf.Ticker(ticker_symbol)
        price = ticker.fast_info['lastPrice']
        return float(price)
    except Exception as e:
        print(f"Error fetching live price for {symbol}: {e}")
        return 1500.00

def execute_paper_trade(symbol, action, reason):
    portfolio, _ = PaperPortfolio.objects.get_or_create(id=1)
    price = get_current_bse_price(symbol)
    
    trade_value = 15000.00
    quantity = int(trade_value // price) if price > 0 else 0

    if quantity <= 0:
        return f"Trade price ₹{price} exceeds standard cash allocation."

    if action == "BUY":
        cost = float(price) * quantity
        if float(portfolio.cash_balance) >= cost:
            portfolio.cash_balance = float(portfolio.cash_balance) - cost
            portfolio.save()

            position, created = PaperPosition.objects.get_or_create(symbol=symbol)
            if created:
                position.quantity = quantity
                position.avg_price = price
            else:
                total_qty = position.quantity + quantity
                total_cost = (float(position.avg_price) * position.quantity) + cost
                position.avg_price = total_cost / total_qty
                position.quantity = total_qty
            position.save()

            PaperTradeLog.objects.create(
                symbol=symbol, action='BUY', quantity=quantity, price=price, reason=reason
            )
            return f"SIMULATED BUY: {quantity} shares of {symbol} at ₹{price}"
        return "SIMULATED BUY FAILED: Insufficient paper funds."

    elif action == "SELL":
        try:
            position = PaperPosition.objects.get(symbol=symbol)
            if position.quantity > 0:
                sell_qty = position.quantity
                revenue = float(price) * sell_qty
                
                portfolio.cash_balance = float(portfolio.cash_balance) + revenue
                portfolio.save()
                position.delete()

                PaperTradeLog.objects.create(
                    symbol=symbol, action='SELL', quantity=sell_qty, price=price, reason=reason
                )
                return f"SIMULATED SELL: Sold {sell_qty} shares of {symbol} at ₹{price}"
        except PaperPosition.DoesNotExist:
            return f"SIMULATED SELL FAILED: No position held in {symbol}."

    elif action == "HOLD":
        PaperTradeLog.objects.create(
            symbol=symbol, action='HOLD', quantity=0, price=price, reason=reason
        )
        return f"SIMULATED HOLD: Logged HOLD decision for {symbol}."

    return "No trade action taken."
""",

    "trading/tasks.py": """import json
import requests
from bs4 import BeautifulSoup
from celery import shared_task
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .utils import execute_paper_trade

embeddings = OpenAIEmbeddings()
db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

@shared_task
def scrape_cnbc_news():
    url = "https://www.cnbctv18.com/market/stocks/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('p') or soup.find_all('div', class_='text')
            
            texts = [art.get_text() for art in articles if len(art.get_text()) > 50]
            full_text = "\n".join(texts)

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs = text_splitter.create_documents([full_text])

            db.add_documents(docs)
            return f"Successfully added {len(docs)} documents to vector database."
    except Exception as e:
        return f"Scrape failed: {e}"
    return "Failed to fetch content."

@shared_task
def run_trading_agent(symbol):
    query = f"Latest news, analysis, and outlook for {symbol}"
    docs = db.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in docs])

    if not context:
        return f"Insufficient context in database to analyze {symbol}."

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"\\n    You are an AI paper trading assistant. \\n    Analyze the following market news context on {symbol} and decide to BUY, SELL, or HOLD.\\n    \\n    Context:\\n    {context}\\n    \\n    Respond STRICTLY in JSON format with keys \\"signal\\" and \\"reason\\":\\n    {{\\"signal\\": \\"BUY|SELL|HOLD\\", \\"reason\\": \\"reason here\\"}}\\n    "

    try:
        response = llm.predict(prompt)
        decision = json.loads(response)
        
        action = decision.get("signal", "HOLD").upper()
        reason = decision.get("reason", "No reason provided.")
        
        result = execute_paper_trade(symbol, action, reason)
        return result
    except Exception as e:
        return f"Error executing trading agent run: {e}"
""",

    "trading/views.py": """from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import PaperPortfolio, PaperPosition, PaperTradeLog
from .tasks import run_trading_agent, scrape_cnbc_news

class PortfolioDashboardAPI(APIView):
    def get(self, request):
        portfolio, _ = PaperPortfolio.objects.get_or_create(id=1)
        positions = PaperPosition.objects.all().values()
        logs = PaperTradeLog.objects.all().order_by('-timestamp')[:20].values()

        return Response({
            "cash_balance": portfolio.cash_balance,
            "positions": list(positions),
            "trade_history": list(logs)
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
""",

    "trading/urls.py": """from django.urls import path
from .views import PortfolioDashboardAPI, trigger_scrape, trigger_agent

urlpatterns = [
    path('dashboard/', PortfolioDashboardAPI.as_view(), name='dashboard'),
    path('scrape/', trigger_scrape, name='trigger_scrape'),
    path('trade-agent/', trigger_agent, name='trigger_agent'),
]
"""
}

def create_project_and_zip():
    project_dir = "autoinvest_backend"
    zip_filename = "backend_project.zip"
    
    print("Generating project files on disk...")
    # Create files on disk
    for file_path, content in PROJECT_FILES.items():
        full_path = os.path.join(project_dir, file_path)
        directory = os.path.dirname(full_path)
        
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
            
    print(f"Extract successful! Files written to './{project_dir}/'")
    
    print(f"Creating ZIP archive '{zip_filename}'...")
    # Pack everything into a zip file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Keep archive path relative to the root folder
                archive_path = os.path.relpath(file_path, project_dir)
                zipf.write(file_path, archive_path)
                
    print(f"Zip successful! Archive created at './{zip_filename}'")

if __name__ == "__main__":
    create_project_and_zip()