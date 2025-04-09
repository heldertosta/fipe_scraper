import psycopg2
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
import time
import config
from utils import setup_logging
import argparse

# Configuração do logging
setup_logging(__file__)

def verificar_tabela_modelo(cur):
    """Verifica se a tabela modelo existe e cria se necessário"""
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS modelo (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                fipeid INTEGER NOT NULL,
                marca_id INTEGER NOT NULL,
                referencia_id INTEGER NOT NULL,
                FOREIGN KEY (marca_id) REFERENCES marca(id),
                FOREIGN KEY (referencia_id) REFERENCES referencias(id),
                UNIQUE (nome, marca_id, referencia_id)
            )
        """)
        logging.info("Tabela modelo verificada/criada com sucesso")
    except Exception as e:
        logging.error(f"Erro ao verificar/criar tabela modelo: {e}")
        raise

def get_referencias(cur, referencia_especifica=None):
    """Obtém as referências do banco"""
    try:
        if referencia_especifica:
            cur.execute("SELECT id, mes_ano FROM referencias WHERE mes_ano = %s", (referencia_especifica,))
        else:
            cur.execute("SELECT id, mes_ano FROM referencias ORDER BY ano DESC, mes DESC")
        return cur.fetchall()
    except Exception as e:
        logging.error(f"Erro ao obter referências: {e}")
        return []

def get_marcas_para_processar(cur, tipo_veiculo, referencia_id):
    """Obtém as marcas que precisam ter seus modelos processados"""
    try:
        cur.execute("""
            SELECT m.id, m.nome 
            FROM marca m
            LEFT JOIN modelo mo ON m.id = mo.marca_id AND mo.referencia_id = %s
            WHERE m.tipo_veiculo = %s 
            AND m.referencia_id = %s
            AND mo.id IS NULL
            ORDER BY m.id
        """, (referencia_id, tipo_veiculo, referencia_id))
        return cur.fetchall()
    except Exception as e:
        logging.error(f"Erro ao obter marcas para processar: {e}")
        return []

def get_modelos_existentes(cur, marca_id, referencia_id):
    """Obtém a lista de modelos já existentes no banco para uma marca e referência"""
    try:
        cur.execute(
            "SELECT nome FROM modelo WHERE marca_id = %s AND referencia_id = %s",
            (marca_id, referencia_id)
        )
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Erro ao obter modelos existentes: {e}")
        return []

def esperar_e_clicar(driver, wait, by, value, timeout=20):
    """Espera um elemento ficar visível e clicável, então clica nele"""
    try:
        elemento = wait.until(EC.element_to_be_clickable((by, value)))
        driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
        time.sleep(3)  # Aumentado para 3 segundos
        elemento.click()
        return True
    except Exception as e:
        logging.error(f"Erro ao clicar no elemento {value}: {e}")
        return False

def selecionar_tipo_veiculo(driver, tipo_veiculo):
    """Seleciona o tipo de veículo na página"""
    try:
        botao = driver.find_element(By.CSS_SELECTOR, f'div.tab-veiculos ul li.ilustra a[data-slug="{tipo_veiculo}"]')
        driver.execute_script("arguments[0].click();", botao)
        logging.info(f"Tipo de veículo '{tipo_veiculo}' selecionado com sucesso!")
        time.sleep(3)  # Aumentado para 3 segundos
        return True
    except Exception as e:
        logging.error(f"Erro ao selecionar tipo de veículo '{tipo_veiculo}': {str(e)}")
        return False

def selecionar_referencia(driver, wait, referencia, tipo_veiculo):
    """Seleciona a referência na página"""
    try:
        select_ref = wait.until(
            EC.presence_of_element_located((By.ID, f"selectTabelaReferencia{tipo_veiculo}"))
        )
        driver.execute_script("arguments[0].style.display = 'block';", select_ref)
        time.sleep(2)  # Aguarda o elemento ficar visível
        select = Select(select_ref)
        select.select_by_visible_text(referencia)
        logging.info(f"Referência {referencia} selecionada para {tipo_veiculo}")
        time.sleep(3)  # Aguarda o carregamento das marcas
        return True
    except Exception as e:
        logging.error(f"Erro ao selecionar referência {referencia}: {e}")
        return False

def selecionar_marca(driver, wait, marca, tipo_veiculo):
    """Seleciona a marca na página"""
    try:
        select_marcas = wait.until(
            EC.presence_of_element_located((By.ID, f"selectMarca{tipo_veiculo}"))
        )
        driver.execute_script("arguments[0].style.display = 'block';", select_marcas)
        time.sleep(2)  # Aguarda o elemento ficar visível
        select = Select(select_marcas)
        select.select_by_visible_text(marca)
        logging.info(f"Marca {marca} selecionada")
        time.sleep(3)  # Aguarda o carregamento dos modelos
        return True
    except Exception as e:
        logging.error(f"Erro ao selecionar marca {marca}: {e}")
        return False

def get_modelos_site(driver, wait, tipo_veiculo):
    """Obtém a lista de modelos do site para a marca selecionada"""
    try:
        select_modelos = wait.until(
            EC.presence_of_element_located((By.ID, f"selectModelo{tipo_veiculo}"))
        )
        driver.execute_script("arguments[0].style.display = 'block';", select_modelos)
        time.sleep(2)  # Aguarda o elemento ficar visível
        select = Select(select_modelos)
        
        # Obtém todas as opções do select
        options = select.options
        modelos = []
        
        # Itera sobre as opções para obter o texto e o value (fipeid)
        for option in options:
            if option.text and option.text.strip():
                modelo = {
                    'nome': option.text.strip().upper(),
                    'fipeid': int(option.get_attribute('value'))
                }
                modelos.append(modelo)
        
        logging.info(f"Encontrados {len(modelos)} modelos")
        return modelos
        
    except Exception as e:
        logging.error(f"Erro ao obter modelos do site: {e}")
        return []

def processar_marca(driver, wait, cur, conn, marca_id, marca_nome, referencia_id, referencia, tipo_veiculo):
    """Processa os modelos para uma marca específica"""
    try:
        # Obtém modelos existentes para esta marca e referência
        modelos_existentes = get_modelos_existentes(cur, marca_id, referencia_id)
        
        # Seleciona a marca na página
        if not selecionar_marca(driver, wait, marca_nome, tipo_veiculo):
            return
        
        # Obtém modelos do site
        modelos = get_modelos_site(driver, wait, tipo_veiculo)
        
        if not modelos:
            logging.warning(f"Nenhum modelo encontrado para a marca {marca_nome} e referência {referencia}")
            return
        
        # Filtra apenas os modelos que não existem no banco para esta marca e referência
        novos_modelos = [modelo for modelo in modelos if modelo['nome'] not in modelos_existentes]
        
        if not novos_modelos:
            logging.info(f"Não há novos modelos para adicionar para a marca {marca_nome} e referência {referencia}")
            return
        
        # Insere os novos modelos no banco
        for modelo in novos_modelos:
            cur.execute(
                "INSERT INTO modelo (nome, fipeid, marca_id, referencia_id) VALUES (%s, %s, %s, %s)",
                (modelo['nome'], modelo['fipeid'], marca_id, referencia_id)
            )
        
        conn.commit()
        logging.info(f"Adicionados {len(novos_modelos)} novos modelos para a marca {marca_nome} e referência {referencia}")
        
    except Exception as e:
        logging.error(f"Erro ao processar marca {marca_nome} e referência {referencia}: {str(e)}")
        conn.rollback()

def processar_referencia(driver, wait, cur, conn, referencia_id, referencia, tipo_veiculo):
    """Processa os modelos para uma referência específica"""
    try:
        # Seleciona o tipo de veículo
        if not selecionar_tipo_veiculo(driver, tipo_veiculo):
            return
        
        # Seleciona a referência
        if not selecionar_referencia(driver, wait, referencia, tipo_veiculo):
            return
        
        # Obtém marcas para processar
        marcas = get_marcas_para_processar(cur, tipo_veiculo, referencia_id)
        
        if not marcas:
            logging.info(f"Não há marcas para processar para a referência {referencia} do tipo {tipo_veiculo}")
            return
        
        for marca_id, marca_nome in marcas:
            logging.info(f"Processando marca: {marca_nome} para referência {referencia}")
            processar_marca(driver, wait, cur, conn, marca_id, marca_nome, referencia_id, referencia, tipo_veiculo)
            
    except Exception as e:
        logging.error(f"Erro ao processar referência {referencia}: {e}")
        conn.rollback()

def main():
    parser = argparse.ArgumentParser(description='Processa modelos de veículos da FIPE')
    parser.add_argument('--referencia', type=str, help='Mês/Ano da referência específica (ex: "abril/2025")')
    args = parser.parse_args()
    
    try:
        # Conecta ao banco de dados
        logging.info("Conectando ao banco de dados...")
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Verifica/cria a tabela modelo
        verificar_tabela_modelo(cur)
        conn.commit()
        
        # Obtém as referências do banco
        referencias = get_referencias(cur, args.referencia)
        logging.info(f"Encontradas {len(referencias)} referências no banco")
        
        if not referencias:
            if args.referencia:
                logging.error(f"Referência {args.referencia} não encontrada")
            else:
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
        time.sleep(3)
        
        # Processa cada tipo de veículo
        tipos_veiculos = ['carro', 'caminhao', 'moto']
        
        for tipo_veiculo in tipos_veiculos:
            logging.info(f"Iniciando processamento para {tipo_veiculo}")
            for referencia_id, referencia in referencias:
                logging.info(f"Processando referência: {referencia}")
                processar_referencia(driver, wait, cur, conn, referencia_id, referencia, tipo_veiculo)
        
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