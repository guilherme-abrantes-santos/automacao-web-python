# Importa a classe WebDriver do módulo selenium para controlar o navegador
from selenium import webdriver

# Importa a classe By para localizar elementos na página
from selenium.webdriver.common.by import By

# Importa a classe Keys para enviar teclas (como Enter)
from selenium.webdriver.common.keys import Keys

# Importa a classe Service para especificar o caminho do chromedriver
from selenium.webdriver.chrome.service import Service

# Importa a função sleep do módulo time para pausar a execução
import time

# Para esperas inteligentes
from selenium.webdriver.support.ui import WebDriverWait

# Para condições de espera
from selenium.webdriver.support import expected_conditions as EC

# --- Configuração Inicial ---
chromedriver_path = "./chromedriver.exe"

# URL do site que queremos acessar
site_url = "https://comunica.pje.jus.br/"

termo_pesquisa = "automação python selenium"

# --- Inicializando o Navegador ---
print("Iniciando o navegador...")
driver = None

try:
    # Cria um objeto Service que aponta para o caminho do chromedriver
    service = Service(executable_path=chromedriver_path)

    # Cria uma instância do navegador Chrome.
    # Isso vai abrir uma nova janela do Chrome controlada pelo Selenium.
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    print(f"Navegador aberto! Acessando o site: {site_url}")

    # Abre a URL especificada no navegador
    driver.get(site_url)

    # --- Espera Inteligente: Aguarda o campo de pesquisa estar visível e clicável ---
    print("Aguardando o campo de pesquisa carregar...")
    campo_pesquisa_locator = (By.CSS_SELECTOR, 'input[formcontrolname="texto"]')

    # WebDriverWait espera até 10 segundos para a condição ser verdadeira
    campo_pesquisa = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(campo_pesquisa_locator)
    )
    print("Campo de pesquisa encontrado!")

    # --- Digitando o Termo de Pesquisa ---
    print(f"Digitando o termo: '{termo_pesquisa}'")
    campo_pesquisa.send_keys(termo_pesquisa)
    print("Termo digitado!")

    # --- Localizando e Clicando no Botão de Busca ---
    print("Localizando o botão de busca...")
    # Define o localizador do botão
    botao_busca_locator = (By.CLASS_NAME, 'button-icon-search')

    # Espera até o botão estar visível e clicável
    botao_busca = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(botao_busca_locator)
    )
    print("Botão de busca encontrado!")

    print("Clicando no botão de busca...")
    # Clica no botão
    botao_busca.click()
    print("Busca iniciada!")

    # --- Pausa para visualizar os resultados da pesquisa ---
    print("Aguardando 15 segundos para você visualizar os resultados...")
    time.sleep(15)

    # --- Fechando o Navegador ---
    print("Fechando o navegador.")
    driver.quit()
    print("Navegador fechado.")

except Exception as e:
    print(f"Ocorreu um erro: {e}")
    print("Verifique:")
    print("- Se o chromedriver.exe está no caminho correto.")
    print("- Se a versão do chromedriver é compatível com a do seu Chrome.")
    print("- Se os seletores do campo e botão de pesquisa ('input[formcontrolname=\"texto\"]' e 'button-icon-search') ainda são válidos para o site.")
    if driver:
        driver.quit()
