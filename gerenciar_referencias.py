import psycopg2
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import config

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('referencias.log'),
        logging.StreamHandler()
    ]
)

def get_referencias_site(driver):
    """Obtém todas as referências disponíveis no site"""
    try:
        # Aguarda o carregamento da página
        wait = WebDriverWait(driver, 10)
        
        # Encontra e clica no botão de carros
        botao = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.tab-veiculos ul li.ilustra a[data-slug="carro"]'))
        )
        driver.execute_script("arguments[0].click();", botao)
        logging.info("Botão de carros clicado com sucesso!")
        
        # Aguarda um pouco para o carregamento
        time.sleep(3)
        
        # Encontra o select de referências
        select_ref = wait.until(
            EC.presence_of_element_located((By.ID, "selectTabelaReferenciacarro"))
        )
        # Usa JavaScript para tornar o elemento visível
        driver.execute_script("arguments[0].style.display = 'block';", select_ref)
        select = Select(select_ref)
        
        # Obtém todas as opções do select
        options = select.options
        referencias = []
        
        # Itera sobre as opções para obter o texto
        for option in options:
            if option.text and option.text.strip():
                mes_ano = option.text.strip()
                mes, ano = mes_ano.split('/')
                referencias.append((mes, int(ano), mes_ano))
        
        logging.info(f"Encontradas {len(referencias)} referências no site")
        return referencias
        
    except Exception as e:
        logging.error(f"Erro ao obter referências do site: {e}")
        return []

def get_referencias_banco(cur):
    """Obtém todas as referências já existentes no banco"""
    try:
        cur.execute("SELECT mes, ano, mes_ano FROM referencias")
        return [(row[0], row[1], row[2]) for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Erro ao obter referências do banco: {e}")
        return []

def inserir_referencias(cur, referencias):
    """Insere novas referências no banco"""
    try:
        for mes, ano, mes_ano in referencias:
            cur.execute(
                "INSERT INTO referencias (mes, ano, mes_ano) VALUES (%s, %s, %s) ON CONFLICT (mes_ano) DO NOTHING",
                (mes, ano, mes_ano)
            )
            logging.info(f"Referência {mes_ano} processada")
        
    except Exception as e:
        logging.error(f"Erro ao inserir referências: {e}")
        raise

def main():
    try:
        # Conecta ao banco de dados
        logging.info("Conectando ao banco de dados...")
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Configuração do Chrome
        chrome_options = Options()
        if config.SELENIUM_CONFIG['headless']:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-infobars')
        
        # Inicializa o driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Acessa a página
        url = "https://veiculos.fipe.org.br/"
        driver.get(url)
        logging.info(f"Acessando a página: {url}")
        
        # Obtém referências do site
        referencias_site = get_referencias_site(driver)
        
        # Obtém referências do banco
        referencias_banco = get_referencias_banco(cur)
        
        # Filtra apenas as novas referências
        referencias_banco_set = {(m, a, ma) for m, a, ma in referencias_banco}
        novas_referencias = [ref for ref in referencias_site if ref not in referencias_banco_set]
        
        if not novas_referencias:
            logging.info("Não há novas referências para adicionar")
        else:
            # Insere novas referências
            inserir_referencias(cur, novas_referencias)
            logging.info(f"Adicionadas {len(novas_referencias)} novas referências")
        
        conn.commit()
        logging.info("Processo concluído com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro durante a execução: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    main() 