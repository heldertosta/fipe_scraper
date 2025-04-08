import psycopg2
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import config
from utils import setup_logging

# Configuração do logging
setup_logging(__file__)

def get_referencias(cur):
    """Obtém todas as referências do banco"""
    try:
        cur.execute("SELECT id, mes_ano FROM referencias ORDER BY ano DESC, mes DESC")
        return [(row[0], row[1]) for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Erro ao obter referências: {e}")
        return []

def get_tipo_veiculo_id(cur, tipo_veiculo_nome):
    """Obtém o ID do tipo de veículo pelo nome"""
    try:
        cur.execute(
            "SELECT id FROM tipo_veiculo WHERE descricao = %s",
            (tipo_veiculo_nome,)
        )
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            raise Exception(f"Tipo de veículo não encontrado: {tipo_veiculo_nome}")
    except Exception as e:
        logging.error(f"Erro ao obter ID do tipo de veículo: {e}")
        raise

def get_marcas_existentes(cur, tipo_veiculo_id, referencia_id):
    """Obtém a lista de marcas já existentes no banco para um tipo de veículo e referência"""
    try:
        cur.execute(
            "SELECT nome FROM marca WHERE tipo_veiculo = %s AND referencia_id = %s",
            (tipo_veiculo_id, referencia_id)
        )
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Erro ao obter marcas existentes: {e}")
        return []

def selecionar_tipo_veiculo(driver, tipo_veiculo):
    """Seleciona o tipo de veículo na página"""
    try:
        botao = driver.find_element(By.CSS_SELECTOR, f'div.tab-veiculos ul li.ilustra a[data-slug="{tipo_veiculo}"]')
        driver.execute_script("arguments[0].click();", botao)
        logging.info(f"Tipo de veículo '{tipo_veiculo}' selecionado com sucesso!")
        time.sleep(2)  # Aumentado para garantir o carregamento
        return True
    except Exception as e:
        logging.error(f"Erro ao selecionar tipo de veículo '{tipo_veiculo}': {str(e)}")
        return False

def get_marcas_site(driver, referencia, wait, tipo_veiculo):
    """Obtém a lista de marcas do site para uma referência e tipo de veículo"""
    max_retries = 3
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
            
            # Aguarda o carregamento das marcas
            time.sleep(2)  # Aumentado para garantir o carregamento
            
            # Encontra e obtém a lista de marcas
            select_marcas = wait.until(
                EC.presence_of_element_located((By.ID, f"selectMarca{tipo_veiculo}"))
            )
            driver.execute_script("arguments[0].style.display = 'block';", select_marcas)
            select = Select(select_marcas)
            
            # Obtém todas as opções do select
            options = select.options
            marcas = []
            
            # Itera sobre as opções para obter o texto e o value (fipeid)
            for option in options:
                if option.text and option.text.strip():
                    marca = {
                        'nome': option.text.strip().upper(),
                        'fipeid': int(option.get_attribute('value'))
                    }
                    marcas.append(marca)
            
            logging.info(f"Encontradas {len(marcas)} marcas para a referência {referencia} do tipo {tipo_veiculo}")
            return marcas
            
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"Erro ao obter marcas do site para referência {referencia} e tipo {tipo_veiculo}: {e}")
                return []
            logging.warning(f"Tentativa {attempt + 1} falhou, tentando novamente...")
            time.sleep(2)  # Espera antes de tentar novamente

def processar_tipo_veiculo(driver, wait, cur, conn, referencias, tipo_veiculo_nome):
    """Processa as marcas para um tipo específico de veículo"""
    if not selecionar_tipo_veiculo(driver, tipo_veiculo_nome):
        return
    
    try:
        tipo_veiculo_id = get_tipo_veiculo_id(cur, tipo_veiculo_nome)
    except Exception as e:
        logging.error(f"Não foi possível processar o tipo de veículo {tipo_veiculo_nome}: {e}")
        return
    
    for referencia_id, referencia in referencias:
        logging.info(f"Processando referência: {referencia} para {tipo_veiculo_nome}")
        
        try:
            # Obtém marcas existentes para esta referência
            marcas_existentes = get_marcas_existentes(cur, tipo_veiculo_id, referencia_id)
            
            # Obtém marcas do site
            marcas = get_marcas_site(driver, referencia, wait, tipo_veiculo_nome)
            
            if not marcas:
                logging.warning(f"Nenhuma marca encontrada para a referência {referencia} do tipo {tipo_veiculo_nome}")
                continue
            
            # Filtra apenas as marcas que não existem no banco para esta referência
            novas_marcas = [marca for marca in marcas if marca['nome'] not in marcas_existentes]
            
            if not novas_marcas:
                logging.info(f"Não há novas marcas para adicionar para a referência {referencia} do tipo {tipo_veiculo_nome}")
                continue
            
            # Insere as novas marcas no banco
            for marca in novas_marcas:
                cur.execute(
                    "INSERT INTO marca (nome, fipeid, tipo_veiculo, referencia_id) VALUES (%s, %s, %s, %s)",
                    (marca['nome'], marca['fipeid'], tipo_veiculo_id, referencia_id)
                )
            
            conn.commit()
            logging.info(f"Adicionadas {len(novas_marcas)} novas marcas para a referência {referencia} do tipo {tipo_veiculo_nome}")
            
        except Exception as e:
            logging.error(f"Erro ao processar referência {referencia} do tipo {tipo_veiculo_nome}: {str(e)}")
            conn.rollback()
            continue

def main():
    try:
        # Conecta ao banco de dados
        logging.info("Conectando ao banco de dados...")
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Obtém as referências do banco
        referencias = get_referencias(cur)
        logging.info(f"Encontradas {len(referencias)} referências no banco")
        
        if not referencias:
            logging.info("Não há referências para processar")
            return
        
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
        time.sleep(3)  # Aumentado para garantir o carregamento inicial
        
        # Processa cada tipo de veículo
        tipos_veiculos = ['carro', 'caminhao', 'moto']
        for tipo_veiculo in tipos_veiculos:
            logging.info(f"Iniciando processamento para {tipo_veiculo}")
            processar_tipo_veiculo(driver, wait, cur, conn, referencias, tipo_veiculo)
        
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