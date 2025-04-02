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
        logging.FileHandler('reprocessar_marcas.log'),
        logging.StreamHandler()
    ]
)

def carregar_referencias_falhas():
    """Carrega as referências com falhas do arquivo"""
    referencias = []
    try:
        with open('referencias_sem_marcas.txt', 'r') as arquivo:
            for linha in arquivo:
                ref_id, referencia, tipo_veiculo = linha.strip().split(',')
                referencias.append((int(ref_id), referencia, tipo_veiculo))
        return referencias
    except Exception as e:
        logging.error(f"Erro ao carregar referências: {e}")
        return []

def selecionar_tipo_veiculo(driver, tipo_veiculo):
    """Seleciona o tipo de veículo na página"""
    try:
        botao = driver.find_element(By.CSS_SELECTOR, f'div.tab-veiculos ul li.ilustra a[data-slug="{tipo_veiculo}"]')
        driver.execute_script("arguments[0].click();", botao)
        logging.info(f"Tipo de veículo '{tipo_veiculo}' selecionado com sucesso!")
        time.sleep(2)
        return True
    except Exception as e:
        logging.error(f"Erro ao selecionar tipo de veículo '{tipo_veiculo}': {str(e)}")
        return False

def get_marcas_site(driver, referencia, wait, tipo_veiculo):
    """Obtém a lista de marcas do site para uma referência e tipo de veículo"""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Encontra e seleciona a referência
            select_ref = wait.until(
                EC.presence_of_element_located((By.ID, f"selectTabelaReferencia{tipo_veiculo}"))
            )
            driver.execute_script("arguments[0].style.display = 'block';", select_ref)
            select = Select(select_ref)
            select.select_by_visible_text(referencia)
            logging.info(f"Referência {referencia} selecionada para {tipo_veiculo}")
            
            # Aumentado tempo de espera para 5 segundos
            time.sleep(5)
            
            # Encontra e obtém a lista de marcas
            select_marcas = wait.until(
                EC.presence_of_element_located((By.ID, f"selectMarca{tipo_veiculo}"))
            )
            driver.execute_script("arguments[0].style.display = 'block';", select_marcas)
            select = Select(select_marcas)
            
            # Obtém todas as opções do select
            options = select.options
            marcas = []
            
            # Itera sobre as opções para obter o texto
            for option in options:
                if option.text and option.text.strip():
                    marcas.append(option.text.strip())
            
            logging.info(f"Encontradas {len(marcas)} marcas para a referência {referencia} do tipo {tipo_veiculo}")
            return marcas
            
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Erro ao obter marcas do site para referência {referencia} e tipo {tipo_veiculo}: {e}")
                return []
            logging.warning(f"Tentativa {attempt + 1} falhou, tentando novamente...")
            time.sleep(5)

def processar_referencia(driver, wait, cur, conn, referencia_id, referencia, tipo_veiculo):
    """Processa uma referência específica para um tipo de veículo"""
    logging.info(f"Processando referência: {referencia} para {tipo_veiculo}")
    
    try:
        # Obtém marcas do site
        marcas = get_marcas_site(driver, referencia, wait, tipo_veiculo)
        
        if not marcas:
            logging.warning(f"Nenhuma marca encontrada para a referência {referencia} do tipo {tipo_veiculo}")
            return
        
        # Verifica se já existem marcas para esta referência
        cur.execute("""
            SELECT COUNT(*) FROM marcas 
            WHERE referencia_id = %s AND tipo_veiculo = %s
        """, (referencia_id, tipo_veiculo))
        
        count = cur.fetchone()[0]
        if count > 0:
            logging.info(f"Já existem {count} marcas para a referência {referencia} do tipo {tipo_veiculo}")
            return
        
        # Insere as marcas no banco
        for marca in marcas:
            try:
                cur.execute(
                    "INSERT INTO marcas (nome, tipo_veiculo, referencia_id) VALUES (%s, %s, %s)",
                    (marca, tipo_veiculo, referencia_id)
                )
            except psycopg2.IntegrityError:
                # Ignora erros de chave duplicada
                continue
        
        conn.commit()
        logging.info(f"Adicionadas {len(marcas)} marcas para a referência {referencia} do tipo {tipo_veiculo}")
        
    except Exception as e:
        logging.error(f"Erro ao processar referência {referencia} do tipo {tipo_veiculo}: {str(e)}")
        conn.rollback()

def main():
    try:
        # Carrega as referências com falhas
        referencias = carregar_referencias_falhas()
        logging.info(f"Encontradas {len(referencias)} referências para reprocessar")
        
        if not referencias:
            logging.info("Não há referências para reprocessar")
            return
        
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
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Inicializa o driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Acessa a página
        url = "https://veiculos.fipe.org.br/"
        driver.get(url)
        logging.info(f"Acessando a página: {url}")
        
        # Aguarda o carregamento da página
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)
        
        # Processa cada referência
        tipo_veiculo_atual = None
        for ref_id, referencia, tipo_veiculo in referencias:
            try:
                # Se mudou o tipo de veículo, seleciona o novo tipo
                if tipo_veiculo != tipo_veiculo_atual:
                    if not selecionar_tipo_veiculo(driver, tipo_veiculo):
                        continue
                    tipo_veiculo_atual = tipo_veiculo
                    time.sleep(5)
                
                processar_referencia(driver, wait, cur, conn, ref_id, referencia, tipo_veiculo)
                time.sleep(3)
                
            except Exception as e:
                logging.error(f"Erro ao processar referência {referencia} do tipo {tipo_veiculo}: {str(e)}")
                continue
        
        logging.info("Processo de reprocessamento concluído com sucesso!")
        
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