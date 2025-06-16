from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os

# --- Configuração Inicial ---
chromedriver_path = "./chromedriver.exe"
site_url = "https://comunica.pje.jus.br/"

# Dados para a pesquisa
data_pesquisa = "13/06/2025"
termo_pesquisa = "tepedino"

# Diretório para salvar os PDFs
output_folder = "pdfs_pje"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"Diretório '{output_folder}' criado para salvar os PDFs.")

# --- Inicializando o Navegador ---
print("Iniciando o navegador...")
driver = None

try:
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()

    print(f"Navegador aberto! Acessando o site: {site_url}")
    driver.get(site_url)

    # --- Espera Inteligente: Aguarda o campo de data carregar ---
    print(f"Aguardando o campo de data ('{data_pesquisa}') carregar...")
    campo_data_locator = (By.CSS_SELECTOR, 'input[formcontrolname="dataDisponibilizacao"]')
    campo_data = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(campo_data_locator)
    )
    print("Campo de data encontrado!")

    # --- Limpando e Digitando a Data ---
    campo_data.clear()
    print(f"Digitando a data: '{data_pesquisa}'")
    campo_data.send_keys(data_pesquisa)
    print("Data digitada!")
    time.sleep(1)

    # --- Espera Inteligente: Aguarda o campo de pesquisa textual carregar ---
    print("Aguardando o campo de pesquisa textual carregar...")
    campo_pesquisa_texto_locator = (By.CSS_SELECTOR, 'input[formcontrolname="texto"]')

    campo_pesquisa_texto = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(campo_pesquisa_texto_locator)
    )
    print("Campo de pesquisa textual encontrado!")

    # --- Digitando o Termo de Pesquisa ---
    print(f"Digitando o termo: '{termo_pesquisa}'")
    campo_pesquisa_texto.send_keys(termo_pesquisa)
    print("Termo digitado!")

    # --- Acionando a Pesquisa com a Tecla ENTER ---
    print("Pressionando ENTER para iniciar a pesquisa...")
    campo_pesquisa_texto.send_keys(Keys.ENTER)
    print("Busca iniciada!")

    # --- Espera para os resultados carregarem ---
    print("Aguardando os resultados da pesquisa carregarem...")
    resultado_card_locator = (By.CSS_SELECTOR, 'article.card.fadeIn')

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(resultado_card_locator)
        )
        print("Resultados da pesquisa carregados!")
    except Exception as timeout_e:
        print(f"Tempo limite excedido para carregar resultados. Pode não haver resultados para a data/termo: {timeout_e}")
        pass 

    # --- Extraindo e Interagindo com Cada Resultado ---
    print("\n--- Processando Resultados ---")
    
    # Guarda o handle da janela principal antes de abrir novas guias
    main_window_handle = driver.current_window_handle

    # Loop para processar os resultados
    # NOTA: O loop será baseado em `range(len(resultados_encontrados))`.
    # A lista `resultados_encontrados` será RE-OBTIDA a cada iteração
    # para evitar elementos 'stale' (obsoletos) após alternar janelas.
    
    # Primeiro, obtemos o número total de resultados
    total_resultados = len(driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn'))
    
    if total_resultados == 0:
        print("Nenhum resultado de pesquisa encontrado com os critérios especificados.")
    else:
        print(f"Encontrados {total_resultados} resultados.")

        # Iterar por índice e re-encontrar o elemento 'resultado' a cada vez
        for i in range(total_resultados):
            print(f"\nProcessando resultado {i+1}:")
            numero_processo = "Não encontrado" # Inicializa com valor padrão

            try:
                # Re-localiza todos os cards a cada iteração
                # Isso garante que estamos trabalhando com elementos frescos após alternar janelas
                resultados_atuais = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn')
                
                # Pega o card específico para a iteração atual
                resultado = resultados_atuais[i] 

                # --- Extraindo o Número do Processo ---
                # Seletor correto baseado na sua inspeção
                numero_processo_elem = resultado.find_element(By.CSS_SELECTOR, 'div#numero-processo > span.numero-unico-formatado')
                numero_processo = numero_processo_elem.text.strip() # .strip() para remover espaços em branco extras
                print(f"  Número do Processo: {numero_processo}")
            except Exception as np_e:
                print(f"  Número do Processo: {numero_processo} (Erro ao extrair: {np_e})")
                # Se o número do processo não for encontrado, ele será "Não encontrado" no nome do arquivo.
                # Isso é aceitável por enquanto, já que é um erro na extração do dado, não na lógica do loop.

            try:
                # --- Localizando e Clicando no Link "Imprimir" dentro DESTE resultado ---
                print("  Localizando link 'Imprimir'...")
                # O seletor CSS para o link 'a' dentro do 'li' que tem title='Imprimir'
                link_imprimir_locator = (By.CSS_SELECTOR, 'li[title="Imprimir"] > a')
                
                # Espera o link 'Imprimir' estar clicável DENTRO DO CARD ATUAL
                link_imprimir = WebDriverWait(resultado, 10).until(
                    EC.element_to_be_clickable(link_imprimir_locator)
                )
                print("  Link 'Imprimir' encontrado! Clicando...")
                link_imprimir.click()

                # --- Lidar com a Nova Guia/Janela (PDF) ---
                print("  Lidando com a nova guia de impressão (PDF)...")
                WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

                for window_handle in driver.window_handles:
                    if window_handle != main_window_handle:
                        driver.switch_to.window(window_handle)
                        break
                
                pdf_url = driver.current_url
                print(f"  URL do PDF: {pdf_url}")

                # --- Salvando o PDF ---
                if pdf_url.endswith(".pdf") or "certidao" in pdf_url:
                    # Usa o número do processo para o nome do arquivo, tratando caracteres inválidos
                    # Adicione um ID único se o número do processo puder se repetir e gerar nomes iguais
                    # Por exemplo, você pode pegar uma parte do hash do URL da certidão
                    unique_id = pdf_url.split('/')[-2] # Pega a parte única da URL da certidao
                    file_name = f"{numero_processo.replace('.', '_').replace('-', '_').replace('/', '_')}_{unique_id}_Certidao.pdf"
                    file_path = os.path.join(output_folder, file_name)
                    
                    print(f"  Baixando e salvando PDF como: {file_path}")
                    try:
                        response = requests.get(pdf_url, stream=True)
                        response.raise_for_status() 

                        with open(file_path, 'wb') as pdf_file:
                            for chunk in response.iter_content(chunk_size=8192):
                                pdf_file.write(chunk)
                        print("  PDF salvo com sucesso!")
                    except requests.exceptions.RequestException as req_e:
                        print(f"  Erro ao baixar/salvar o PDF '{pdf_url}': {req_e}")
                else:
                    print(f"  O URL '{pdf_url}' não parece ser um PDF/certidão diretamente baixável.")

                print("  Fechando a nova guia.")
                driver.close()

                driver.switch_to.window(main_window_handle)
                print("  Foco retornado para a guia principal.")
                # Pequeno sleep para garantir que a página principal esteja pronta antes da próxima iteração
                time.sleep(1) 

            except Exception as inner_e:
                print(f"  Erro ao processar o link 'Imprimir' ou a nova guia para o resultado {i+1}: {inner_e}")
                # Garante que o navegador volte para a janela principal em caso de erro
                if len(driver.window_handles) > 1 and driver.current_window_handle != main_window_handle:
                    print("  Tentando fechar janela extra e voltar ao foco principal após erro.")
                    driver.close()
                    driver.switch_to.window(main_window_handle)
                time.sleep(1) # Pequeno delay para não sobrecarregar
    print("\n--- Processamento de Resultados Concluído ---")

    # --- Pausa final e Fechamento ---
    print("Aguardando 5 segundos antes de fechar o navegador principal.")
    time.sleep(5)

    print("Fechando o navegador.")
    driver.quit()
    print("Navegador fechado.")

except Exception as e:
    print(f"Ocorreu um erro geral: {e}")
    print("Verifique:")
    print("- Se o chromedriver.exe está no caminho correto.")
    print("- Se a versão do chromedriver é compatível com a do seu Chrome.")
    print("- Se os seletores (data: 'input[formcontrolname=\"dataDisponibilizacao\"]', termo: 'input[formcontrolname=\"texto\"]', cards: 'article.card.fadeIn', numero_processo: 'div#numero-processo > span.numero-unico-formatado', imprimir: 'li[title=\"Imprimir\"] > a') ainda são válidos para o site.")
    if driver:
        driver.quit()