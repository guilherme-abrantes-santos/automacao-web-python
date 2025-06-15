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

# Dados para a pesquisa
data_pesquisa = "13/06/2025"
termo_pesquisa = "tepedino"

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

    # --- Espera Inteligente: Aguarda o campo de data carregar ---
    print(f"Aguardando o campo de data ('{data_pesquisa}') carregar...")
    # Seletor para o campo de data
    campo_data_locator = (By.CSS_SELECTOR, 'input[formcontrolname="dataDisponibilizacao"]')
    campo_data = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(campo_data_locator)
    )
    print("Campo de data encontrado!")

    # --- Limpando e Digitando a Data ---
    campo_data.clear() # É uma boa prática limpar o campo antes de digitar, caso já haja algo.
    print(f"Digitando a data: '{data_pesquisa}'")
    campo_data.send_keys(data_pesquisa) #! NOVO: Digita a data
    print("Data digitada!")
    time.sleep(1)

    # --- Espera Inteligente: Aguarda o campo de pesquisa estar visível e clicável ---
    print("Aguardando o campo de pesquisa carregar...")
    campo_pesquisa_locator = (By.CSS_SELECTOR, 'input[formcontrolname="texto"]')

    # WebDriverWait espera até 10 segundos para a condição ser verdadeira
    campo_pesquisa = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(campo_pesquisa_locator)
    )
    print("Campo de pesquisa encontrado!")

    # --- Digitando o Termo de Pesquisa ---
    print(f"Digitando o termo: '{termo_pesquisa}'")
    campo_pesquisa.send_keys(termo_pesquisa)
    print("Termo digitado!")

    # --- Acionando a Pesquisa com a Tecla ENTER ---
    print("Pressionando ENTER para iniciar a pesquisa...")
    campo_pesquisa.send_keys(Keys.ENTER)
    print("Busca iniciada!")

    # --- Espera para os resultados carregarem ---
    print("Aguardando os resultados da pesquisa carregarem...")
    #Seletor para o card de resultado
    resultado_card_locator = (By.CSS_SELECTOR, 'article.card.fadeIn')

    # Espera até que pelo menos um resultado de card esteja presente
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(resultado_card_locator)
        )
        print("Resultados da pesquisa carregados!")
    except Exception as timeout_e:
        print(f"Tempo limite excedido para carregar resultados. Pode não haver resultados para a data/termo: {timeout_e}")

    # --- Extraindo e Interagindo com Cada Resultado ---
    print("\n--- Processando Resultados ---")
    # Encontra TODOS os cards
    resultados_encontrados = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn')

    if not resultados_encontrados:
        print("Nenhum resultado de pesquisa encontrado com o seletor especificado.")
    else:
        print(f"Encontrados {len(resultados_encontrados)} resultados.")

        # Guarda o handle da janela principal antes de abrir novas guias
        main_window_handle = driver.current_window_handle

        for i, resultado in enumerate(resultados_encontrados):
            print(f"\nProcessando resultado {i+1}:")
            try:
                # Exemplo: Tentando pegar o número do processo (se existir)
                # Você precisaria inspecionar o elemento do número do processo dentro do card!
                try:
                    numero_processo_elem = resultado.find_element(By.CSS_SELECTOR, 'span[id^="numero-processo"]') # Exemplo: id que começa com "numero-processo"
                    numero_processo = numero_processo_elem.text
                    print(f"  Número do Processo: {numero_processo}")
                except Exception as np_e:
                    numero_processo = "Não encontrado"
                    print(f"  Número do Processo: {numero_processo} (Erro: {np_e})")

                # --- Localizando e Clicando no Link "Imprimir" dentro DESTE resultado ---
                print("  Localizando link 'Imprimir'...")
                # O seletor CSS para o link 'a' dentro do 'li' que tem title='Imprimir'
                link_imprimir_locator = (By.CSS_SELECTOR, 'li[title="Imprimir"] > a')

                link_imprimir = WebDriverWait(resultado, 10).until(
                    EC.element_to_be_clickable(link_imprimir_locator)
                )
                print("  Link 'Imprimir' encontrado! Clicando...")
                link_imprimir.click()

                # --- Lidar com a Nova Guia/Janela ---
                print("  Lidando com a nova guia de impressão...")
                # Espera até que o número de handles (abas/janelas) seja 2 (original + a nova)
                WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
                # Itera sobre todas as janelas abertas
                for window_handle in driver.window_handles: # Pega todos os IDs de janelas
                    if window_handle != main_window_handle: # Se não for a janela principal
                        driver.switch_to.window(window_handle) # Muda o foco para a nova janela
                        break

                # Agora o Selenium está na nova guia
                print(f"  URL da nova guia: {driver.current_url}") # Imprime o URL da nova guia
                # Você pode adicionar lógica aqui para salvar o conteúdo, ou o URL

                print("  Fechando a nova guia.")
                driver.close()

                # Volta o foco para a janela principal
                driver.switch_to.window(main_window_handle)
                print("  Foco retornado para a guia principal.")

            except Exception as inner_e:
                print(f"  Erro ao processar resultado {i+1}: {inner_e}")
                # Volta para a janela principal se um erro ocorreu em uma nova janela e o foco foi perdido
                if len(driver.window_handles) > 1 and driver.current_window_handle != main_window_handle:
                    driver.close()
                    driver.switch_to.window(main_window_handle)
                    # Adiciona um pequeno delay para não sobrecarregar o site, se for processar muitos itens
                    time.sleep(1)

    print("\n--- Processamento de Resultados Concluído ---")

    # --- Pausa final e Fechamento ---
    print("Aguardando 5 segundos antes de fechar o navegador principal.")
    time.sleep(5) # Pausa final antes de fechar tudo

    print("Fechando o navegador.")
    driver.quit()
    print("Navegador fechado.")

except Exception as e:
    print(f"Ocorreu um erro: {e}")
    print("Verifique:")
    print("- Se o chromedriver.exe está no caminho correto.")
    print("- Se a versão do chromedriver é compatível com a do seu Chrome.")
    print("- Se os seletores (data: 'input[formcontrolname=\"dataDisponibilizacao\"]', termo: 'input[formcontrolname=\"texto\"]', cards: 'article.card.fadeIn', imprimir: 'li[title=\"Imprimir\"] > a') ainda são válidos para o site.")
    if driver:
        driver.quit()
