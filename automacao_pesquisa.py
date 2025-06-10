# Importa a classe WebDriver do módulo selenium para controlar o navegador
from selenium import webdriver

# Importa a classe By para localizar elementos na página
# (Vamos usar isso mais tarde, mas já deixamos importado)
from selenium.webdriver.common.by import By

# Importa a classe Keys para enviar teclas (como Enter)
# (Vamos usar isso mais tarde também)
from selenium.webdriver.common.keys import Keys

# Importa a classe Service para especificar o caminho do chromedriver
from selenium.webdriver.chrome.service import Service

# --- Configuração Inicial ---
# Onde está o seu chromedriver.exe?
# LEMBRE-SE: Coloque o caminho completo ou o nome do arquivo
# se ele estiver na mesma pasta do seu script Python.
# Se estiver na mesma pasta, pode ser apenas "chromedriver.exe"
# Exemplo Windows: chromedriver_path = "C:/caminho/para/seu/chromedriver.exe"
# Exemplo Linux/macOS: chromedriver_path = "/caminho/para/seu/chromedriver"
chromedriver_path = "./chromedriver.exe" # <-- Mude isso se seu chromedriver não estiver na mesma pasta

# URL do site que queremos acessar
# Para este exemplo, vamos usar o Google, mas você pode mudar para o site que desejar.
site_url = "https://comunica.pje.jus.br/"

# --- Inicializando o Navegador ---
print("Iniciando o navegador...")

try:
    # Cria um objeto Service que aponta para o caminho do chromedriver
    service = Service(executable_path=chromedriver_path)

    # Cria uma instância do navegador Chrome.
    # Isso vai abrir uma nova janela do Chrome controlada pelo Selenium.
    driver = webdriver.Chrome(service=service)

    print(f"Navegador aberto! Acessando o site: {site_url}")

    # Abre a URL especificada no navegador
    driver.get(site_url)

    # --- Verificação (Opcional, mas útil para debug) ---
    print(f"Título da página atual: {driver.title}")

    # --- Pausa e Fechamento (Para você ver o que aconteceu) ---
    print("Mantendo o navegador aberto por 5 segundos para você visualizar...")
    # Importa a função sleep do módulo time para pausar a execução
    import time
    time.sleep(5) # Pausa o programa por 5 segundos

    print("Fechando o navegador.")
    driver.quit() # Fecha o navegador
    print("Navegador fechado.")

except Exception as e:
    print(f"Ocorreu um erro: {e}")
    print("Certifique-se de que o chromedriver.exe está no caminho correto e que sua versão é compatível com o Chrome.")
