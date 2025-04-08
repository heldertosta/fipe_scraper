from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import time
import logging

logger = logging.getLogger(__name__)

class FipeScraper:
    def __init__(self):
        """Inicializa o scraper com as configurações do Chrome."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Executa em modo headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")  # Define uma resolução maior
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 20)
        self.actions = ActionChains(self.driver)

    def fechar(self):
        """Fecha o navegador."""
        if self.driver:
            self.driver.quit()

    def esperar_e_clicar(self, by, value, timeout=20):
        """Espera um elemento ficar clicável e clica nele."""
        try:
            elemento = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            self.actions.move_to_element(elemento).click().perform()
            time.sleep(2)  # Aguarda o carregamento
            return elemento
        except Exception as e:
            logger.error(f"Erro ao clicar no elemento {value}: {str(e)}")
            raise

    def selecionar_tipo_veiculo(self, tipo):
        """Seleciona o tipo de veículo (carro, moto, caminhao)."""
        try:
            # Mapeia o tipo de veículo para o slug
            tipo_map = {
                'carro': 'carro',
                'moto': 'moto',
                'caminhao': 'caminhao'
            }
            
            slug = tipo_map.get(tipo)
            if not slug:
                raise ValueError(f"Tipo de veículo inválido: {tipo}")
            
            # Aguarda a página carregar completamente
            time.sleep(5)
            
            # Encontra o botão usando o seletor CSS que já está funcionando
            botao = self.driver.find_element(
                By.CSS_SELECTOR, 
                f'div.tab-veiculos ul li.ilustra a[data-slug="{slug}"]'
            )
            
            # Clica usando JavaScript
            self.driver.execute_script("arguments[0].click();", botao)
            
            # Aguarda o carregamento
            time.sleep(5)
            
            logger.info(f"Tipo de veículo '{tipo}' selecionado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao selecionar tipo de veículo '{tipo}': {str(e)}")
            return False

    def selecionar_referencia(self, referencia):
        """Seleciona uma referência no dropdown."""
        try:
            # Encontra o select de referências
            select_ref = self.wait.until(
                EC.presence_of_element_located((By.ID, "selectTabelaReferenciacarro"))
            )
            
            # Usa JavaScript para tornar o elemento visível
            self.driver.execute_script("arguments[0].style.display = 'block';", select_ref)
            
            # Cria um objeto Select
            select = Select(select_ref)
            
            # Seleciona a referência pelo texto visível
            select.select_by_visible_text(referencia)
            
            # Aguarda o carregamento
            time.sleep(5)
            
            logger.info(f"Referência '{referencia}' selecionada com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao selecionar referência '{referencia}': {str(e)}")
            return False

    def selecionar_marca(self, marca):
        """Seleciona uma marca no dropdown."""
        try:
            # Encontra o select de marcas
            select_marca = self.wait.until(
                EC.presence_of_element_located((By.ID, "selectMarcacarro"))
            )
            
            # Usa JavaScript para tornar o elemento visível
            self.driver.execute_script("arguments[0].style.display = 'block';", select_marca)
            
            # Cria um objeto Select
            select = Select(select_marca)
            
            # Seleciona a marca pelo texto visível
            select.select_by_visible_text(marca)
            
            # Aguarda o carregamento
            time.sleep(5)
            
            logger.info(f"Marca '{marca}' selecionada com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao selecionar marca '{marca}': {str(e)}")
            return False

    def get_modelos(self):
        """Extrai os modelos da marca selecionada."""
        try:
            # Aguarda o dropdown de modelos estar visível
            modelo_select = self.wait.until(
                EC.presence_of_element_located((By.ID, "selectAnoModelocarro"))
            )
            
            # Usa JavaScript para tornar o elemento visível
            self.driver.execute_script("arguments[0].style.display = 'block';", modelo_select)
            
            # Cria um objeto Select
            select = Select(modelo_select)
            
            # Obtém todas as opções
            options = select.options
            
            # Extrai os textos das opções (ignorando a primeira opção que é vazia)
            modelos = []
            for option in options[1:]:  # Ignora a primeira opção
                texto = option.text.strip()
                if texto:  # Só adiciona se não for vazio
                    modelos.append(texto)
            
            logger.info(f"Encontrados {len(modelos)} modelos")
            return modelos
            
        except Exception as e:
            logger.error(f"Erro ao extrair modelos: {str(e)}")
            return [] 