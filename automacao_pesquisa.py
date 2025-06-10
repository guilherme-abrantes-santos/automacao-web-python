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

    # --- Verificação ---
    print(f"Título da página atual: {driver.title}")

    # --- Pausa e Fechamento ---
    print("Mantendo o navegador aberto por 5 segundos para você visualizar...")

    time.sleep(10) # Pausa o programa por 5 segundos

    print("Fechando o navegador.")
    driver.quit() # Fecha o navegador
    print("Navegador fechado.")

except Exception as e:
    print(f"Ocorreu um erro: {e}")
    print("Verifique:")
    print("- Se o chromedriver.exe está no caminho correto.")
    print("- Se a versão do chromedriver é compatível com a do seu Chrome.")
    if driver:
        driver.quit()
