from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import psycopg2
import logging
import time
import config

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('marcas.log'),
        logging.StreamHandler()
    ]
)

def get_referencias(cur):
    """Obtém a lista de referências do banco"""
    try:
        cur.execute("SELECT id, mes_ano FROM referencias ORDER BY ano, mes")
        return [(row[0], row[1]) for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Erro ao obter referências: {e}")
        return []

def get_marcas_existentes(cur, tipo_veiculo):
    """Obtém a lista de marcas já existentes no banco para um tipo de veículo"""
    try:
        cur.execute(
            "SELECT nome FROM marcas WHERE tipo_veiculo = %s",
            (tipo_veiculo,)
        )
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Erro ao obter marcas existentes: {e}")
        return []

def main():
    try:
        # Conecta ao banco de dados
        logging.info("Conectando ao banco de dados...")
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Obtém as referências do banco
        referencias = get_referencias(cur)
        logging.info(f"Encontradas {len(referencias)} referências no banco")
        
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
        
        # Aguarda o carregamento da página
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)
        
        # Tenta encontrar o elemento <a> com data-slug="carro" dentro da estrutura correta
        try:
            botao = driver.find_element(By.CSS_SELECTOR, 'div.tab-veiculos ul li.ilustra a[data-slug="carro"]')
            # Usa JavaScript para clicar no elemento
            driver.execute_script("arguments[0].click();", botao)
            logging.info("Elemento encontrado e clicado com sucesso!")
        except Exception as e:
            logging.error(f"Não foi possível encontrar o elemento: {str(e)}")
            return
            
        # Aguarda um pouco para o carregamento da página
        time.sleep(3)
        
        # Obtém marcas existentes para este tipo de veículo
        marcas_existentes = get_marcas_existentes(cur, 'carro')
        
        # Para cada referência
        for referencia_id, referencia in referencias:
            logging.info(f"Processando referência: {referencia}")
            
            try:
                # Encontra e seleciona a referência
                select_ref = wait.until(
                    EC.presence_of_element_located((By.ID, "selectTabelaReferenciacarro"))
                )
                # Usa JavaScript para tornar o elemento visível
                driver.execute_script("arguments[0].style.display = 'block';", select_ref)
                select = Select(select_ref)
                select.select_by_visible_text(referencia)
                logging.info(f"Referência {referencia} selecionada")
                
                # Aguarda o carregamento das marcas
                time.sleep(3)
                
                # Encontra e obtém a lista de marcas
                select_marcas = wait.until(
                    EC.presence_of_element_located((By.ID, "selectMarcacarro"))
                )
                # Usa JavaScript para tornar o elemento visível
                driver.execute_script("arguments[0].style.display = 'block';", select_marcas)
                select = Select(select_marcas)
                
                # Obtém todas as opções do select
                options = select.options
                marcas = []
                
                # Itera sobre as opções para obter o texto
                for option in options:
                    if option.text and option.text.strip():
                        marcas.append(option.text.strip())
                
                logging.info(f"Encontradas {len(marcas)} marcas para a referência {referencia}")
                
                # Filtra apenas as marcas que não existem no banco
                novas_marcas = [marca for marca in marcas if marca not in marcas_existentes]
                
                if not novas_marcas:
                    logging.info(f"Não há novas marcas para adicionar para a referência {referencia}")
                    continue
                
                # Insere as novas marcas no banco
                for marca in novas_marcas:
                    cur.execute(
                        "INSERT INTO marcas (nome, tipo_veiculo) VALUES (%s, %s)",
                        (marca, 'carro')
                    )
                
                conn.commit()
                logging.info(f"Adicionadas {len(novas_marcas)} novas marcas para a referência {referencia}")
                
                # Atualiza a lista de marcas existentes
                marcas_existentes.extend(novas_marcas)
                
            except Exception as e:
                logging.error(f"Erro ao processar referência {referencia}: {str(e)}")
                continue
        
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