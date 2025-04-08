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

# Configuração do logging
setup_logging(__file__)

def get_marcas_para_processar(cur, tipo_veiculo, referencia_id):
    """Obtém as marcas que precisam ter seus modelos processados"""
    try:
        cur.execute("""
            SELECT m.id, m.nome 
            FROM marcas m
            LEFT JOIN modelos mo ON m.id = mo.marca_id AND mo.referencia_id = %s
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
            "SELECT nome FROM modelos WHERE marca_id = %s AND referencia_id = %s",
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
        time.sleep(2)  # Aumentado para 2 segundos
        driver.execute_script("arguments[0].click();", elemento)
        return True
    except Exception as e:
        logging.error(f"Erro ao clicar no elemento {value}: {e}")
        return False

def verificar_visibilidade_dropdown(driver, select_element):
    """Verifica se o dropdown está realmente visível e utilizável"""
    try:
        # Verifica se o elemento está visível
        if not select_element.is_displayed():
            driver.execute_script("arguments[0].style.display = 'block';", select_element)
            time.sleep(1)
        
        # Verifica se o elemento tem opções
        options = Select(select_element).options
        if len(options) <= 1:  # Se só tem a opção vazia
            return False
            
        return True
    except Exception as e:
        logging.error(f"Erro ao verificar visibilidade do dropdown: {e}")
        return False

def recarregar_pagina(driver, wait):
    """Recarrega a página e aguarda o carregamento"""
    try:
        driver.refresh()
        time.sleep(5)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        return True
    except Exception as e:
        logging.error(f"Erro ao recarregar página: {e}")
        return False

def get_all_options(driver, select_element):
    """Obtém todas as opções do select, incluindo as que precisam de rolagem"""
    try:
        # Primeiro, vamos tentar obter todas as opções visíveis
        select = Select(select_element)
        options = select.options[1:]  # Ignora a primeira opção vazia
        modelos = set()  # Usa set para evitar duplicatas
        
        # Adiciona os modelos visíveis inicialmente
        for option in options:
            texto = option.text.strip()
            if texto:
                modelos.add(texto)
        
        # Tenta rolar o select para ver se há mais opções
        for i in range(10):  # Tenta rolar até 10 vezes
            # Rola para o último elemento visível
            last_option = options[-1]
            driver.execute_script("arguments[0].scrollIntoView(true);", last_option)
            time.sleep(1)  # Aguarda a rolagem
            
            # Obtém as opções novamente após a rolagem
            new_options = select.options[1:]
            if len(new_options) == len(options):  # Se não apareceram novas opções
                break
                
            # Adiciona apenas as novas opções
            for option in new_options[len(options):]:
                texto = option.text.strip()
                if texto:
                    modelos.add(texto)
            
            options = new_options
        
        return list(modelos)
        
    except Exception as e:
        logging.error(f"Erro ao obter todas as opções do select: {e}")
        return []

def processar_marca(driver, wait, cur, conn, marca_id, marca_nome, referencia_id, referencia, tipo_veiculo, tentativas=2):
    """Processa os modelos de uma marca específica"""
    logging.info(f"Processando modelos para marca: {marca_nome}")
    
    for tentativa in range(tentativas):
        try:
            if tentativa > 0:
                logging.info(f"Tentativa {tentativa + 1} para a marca {marca_nome}")
                if not recarregar_pagina(driver, wait):
                    continue
            
            # Seleciona o tipo de veículo
            if not esperar_e_clicar(
                driver, wait, 
                By.CSS_SELECTOR, 
                f'div.tab-veiculos ul li.ilustra a[data-slug="{tipo_veiculo}"]'
            ):
                logging.error(f"Não foi possível selecionar o tipo de veículo {tipo_veiculo}")
                continue
            
            time.sleep(5)
            
            # Seleciona a referência
            try:
                select_ref = wait.until(
                    EC.presence_of_element_located((By.ID, f"selectTabelaReferencia{tipo_veiculo}"))
                )
                if not verificar_visibilidade_dropdown(driver, select_ref):
                    logging.error("Dropdown de referência não está utilizável")
                    continue
                    
                select = Select(select_ref)
                select.select_by_visible_text(referencia)
                time.sleep(5)
            except Exception as e:
                logging.error(f"Erro ao selecionar referência {referencia}: {e}")
                continue
            
            # Seleciona a marca
            try:
                select_marca = wait.until(
                    EC.presence_of_element_located((By.ID, f"selectMarca{tipo_veiculo}"))
                )
                if not verificar_visibilidade_dropdown(driver, select_marca):
                    logging.error("Dropdown de marca não está utilizável")
                    continue
                    
                select = Select(select_marca)
                select.select_by_visible_text(marca_nome)
                time.sleep(5)
            except Exception as e:
                logging.error(f"Erro ao selecionar marca {marca_nome}: {e}")
                continue
            
            # Obtém os modelos
            try:
                select_modelo = wait.until(
                    EC.presence_of_element_located((By.ID, f"selectAnoModelo{tipo_veiculo}"))
                )
                if not verificar_visibilidade_dropdown(driver, select_modelo):
                    logging.error("Dropdown de modelo não está utilizável")
                    continue
                
                # Obtém todos os modelos, incluindo os que precisam de rolagem
                modelos = get_all_options(driver, select_modelo)
                
                if not modelos:
                    logging.warning(f"Nenhum modelo encontrado para a marca {marca_nome}")
                    return True
                
                # Obtém modelos existentes
                modelos_existentes = get_modelos_existentes(cur, marca_id, referencia_id)
                
                # Filtra apenas os modelos que não existem no banco
                novos_modelos = [modelo for modelo in modelos if modelo not in modelos_existentes]
                
                if not novos_modelos:
                    logging.info(f"Não há novos modelos para adicionar para a marca {marca_nome}")
                    return True
                
                # Insere os novos modelos no banco
                for modelo in novos_modelos:
                    try:
                        cur.execute(
                            "INSERT INTO modelos (nome, marca_id, referencia_id) VALUES (%s, %s, %s)",
                            (modelo, marca_id, referencia_id)
                        )
                    except psycopg2.IntegrityError:
                        # Ignora erros de chave duplicada
                        continue
                
                conn.commit()
                logging.info(f"Adicionados {len(novos_modelos)} novos modelos para a marca {marca_nome}")
                return True
                
            except Exception as e:
                logging.error(f"Erro ao obter modelos para marca {marca_nome}: {e}")
                continue
            
        except Exception as e:
            logging.error(f"Erro ao processar marca {marca_nome} (tentativa {tentativa + 1}): {str(e)}")
            conn.rollback()
            continue
    
    logging.error(f"Todas as tentativas falharam para a marca {marca_nome}")
    return False

def processar_referencia(driver, wait, cur, conn, referencia_id, referencia, tipo_veiculo):
    """Processa uma referência específica para um tipo de veículo"""
    logging.info(f"Processando referência: {referencia} para {tipo_veiculo}")
    
    try:
        # Obtém marcas para processar
        marcas = get_marcas_para_processar(cur, tipo_veiculo, referencia_id)
        
        if not marcas:
            logging.info(f"Não há marcas para processar para a referência {referencia}")
            return
        
        for marca_id, marca_nome in marcas:
            if not processar_marca(driver, wait, cur, conn, marca_id, marca_nome, referencia_id, referencia, tipo_veiculo):
                logging.warning(f"Pulando marca {marca_nome} devido a erro no processamento")
                continue
            time.sleep(3)  # Espera entre processamento de marcas
        
    except Exception as e:
        logging.error(f"Erro ao processar referência {referencia}: {str(e)}")
        conn.rollback()

def main():
    try:
        # Conecta ao banco de dados
        logging.info("Conectando ao banco de dados...")
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()
        
        # Obtém as referências do banco
        cur.execute("SELECT id, mes_ano FROM referencias ORDER BY id")
        referencias = cur.fetchall()
        
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
        
        # Processa cada tipo de veículo
        tipos_veiculos = ['carro', 'caminhao', 'moto']
        for tipo_veiculo in tipos_veiculos:
            logging.info(f"Iniciando processamento para {tipo_veiculo}")
            for referencia_id, referencia in referencias:
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