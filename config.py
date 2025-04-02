import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do banco de dados
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'fipe_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Configurações do Selenium
SELENIUM_CONFIG = {
    'headless': os.getenv('SELENIUM_HEADLESS', 'true').lower() == 'true',
    'timeout': int(os.getenv('SELENIUM_TIMEOUT', '5'))
} 