from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os

# Importar Options para configurar opções do Chrome
from selenium.webdriver.chrome.options import Options 

# --- Configuração Inicial ---
chromedriver_path = "./chromedriver.exe" # Certifique-se de que este chromedriver.exe corresponde ao Chrome que você está usando
site_url = "https://comunica.pje.jus.br/"

# Dados para a pesquisa
data_pesquisa = "16/06/2025" # Use uma data de dia útil com resultados
termo_pesquisa = "tepedino"

# Diretório para salvar os PDFs
output_folder = "pdfs_pje"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"Diretório '{output_folder}' criado para salvar os PDFs.")

# --- Funções Auxiliares ---

def preencher_e_pesquisar(driver, data, termo):
    """Preenche os campos de data e termo e inicia a pesquisa."""
    print(f"\n--- Iniciando Nova Pesquisa para Data: '{data}', Termo: '{termo}' ---")

    # Espera e preenche campo de data
    campo_data_locator = (By.CSS_SELECTOR, 'input[formcontrolname="dataDisponibilizacao"]')
    campo_data = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(campo_data_locator) 
    )
    campo_data.clear()
    campo_data.send_keys(data)
    print(f"Data digitada: '{data}'")
    time.sleep(0.5) # Pequeno delay após digitar data

    # Espera e preenche campo de pesquisa textual
    campo_pesquisa_texto_locator = (By.CSS_SELECTOR, 'input[formcontrolname="texto"]')
    campo_pesquisa_texto = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(campo_pesquisa_texto_locator) 
    )
    campo_pesquisa_texto.clear() # Garante que o campo está limpo para um novo termo
    campo_pesquisa_texto.send_keys(termo)
    print(f"Termo digitado: '{termo}'")

    # Aciona a pesquisa
    campo_pesquisa_texto.send_keys(Keys.ENTER)
    print("Busca iniciada!")

    # Espera pelos resultados
    print("Aguardando os resultados da pesquisa carregarem...")
    resultado_card_locator = (By.CSS_SELECTOR, 'article.card.fadeIn')
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(resultado_card_locator) 
        )
        print("Resultados da pesquisa carregados!")
    except Exception as timeout_e:
        print(f"Tempo limite excedido para carregar resultados. Pode não haver resultados para a data/termo: {timeout_e}")
        return False
    return True

def processar_resultados_da_pagina_atual(driver, main_window_handle, output_folder):
    """
    Processa todos os cards de resultado da página atual, extraindo o número do processo
    e baixando o PDF. Retorna True se encontrou e processou resultados, False caso contrário.
    """
    print("\n--- Processando Resultados da Página Atual ---")
    
    resultados_encontrados = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn') 
    
    if not resultados_encontrados:
        print("Nenhum resultado de pesquisa encontrado nesta página.")
        return False
    
    print(f"Encontrados {len(resultados_encontrados)} resultados nesta página.")

    for i in range(len(resultados_encontrados)): # Iteramos por índice
        resultados_atuais = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn')
        if i >= len(resultados_atuais): 
            print(f"    Pulando resultado {i+1}, pois a lista de resultados encolheu.")
            continue

        resultado = resultados_atuais[i] 

        print(f"\nProcessando resultado {i+1}:")
        numero_processo = "Nao_encontrado" 

        try:
            numero_processo_elem = resultado.find_element(By.CSS_SELECTOR, 'div#numero-processo > span.numero-unico-formatado')
            numero_processo = numero_processo_elem.text.strip()
            print(f"    Número do Processo: {numero_processo}")
        except Exception as np_e:
            print(f"    Número do Processo: {numero_processo} (Erro ao extrair: {np_e})")

        try:
            # --- Localizando e Clicando no Link "Imprimir" dentro DESTE resultado ---
            print("    Localizando link 'Imprimir'...")
            link_imprimir_locator = (By.CSS_SELECTOR, 'li[title="Imprimir"] > a')
            
            link_imprimir = WebDriverWait(resultado, 10).until(
                EC.element_to_be_clickable(link_imprimir_locator) 
            )
            print("    Link 'Imprimir' encontrado! Clicando...")
            link_imprimir.click()

            # --- Lidar com a Nova Guia/Janela (PDF) ---
            print("    Lidando com a nova guia de impressão (PDF)...")
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

            for window_handle in driver.window_handles:
                if window_handle != main_window_handle:
                    driver.switch_to.window(window_handle)
                    break
            
            pdf_url = driver.current_url
            print(f"    URL do PDF: {pdf_url}")

            # --- Salvando o PDF ---
            if pdf_url.endswith(".pdf") or "certidao" in pdf_url:
                unique_id = pdf_url.split('/')[-2] 
                sanitized_numero_processo = numero_processo.replace('.', '_').replace('-', '_').replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                file_name = f"{sanitized_numero_processo}_{unique_id}_Certidao.pdf"
                file_path = os.path.join(output_folder, file_name)
                
                print(f"    Baixando e salvando PDF como: {file_path}")
                try:
                    response = requests.get(pdf_url, stream=True)
                    response.raise_for_status() 

                    with open(file_path, 'wb') as pdf_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            pdf_file.write(chunk)
                    print("    PDF salvo com sucesso!")
                except requests.exceptions.RequestException as req_e:
                    print(f"    Erro ao baixar/salvar o PDF '{pdf_url}': {req_e}")
            else:
                print(f"    O URL '{pdf_url}' não parece ser um PDF/certidão diretamente baixável.")

            print("    Fechando a nova guia.")
            driver.close()

            driver.switch_to.window(main_window_handle)
            print("    Foco retornado para a guia principal.")
            time.sleep(0.5) 

        except Exception as inner_e:
            print(f"    Erro ao processar o link 'Imprimir' ou a nova guia para o resultado {i+1}: {inner_e}")
            if len(driver.window_handles) > 1 and driver.current_window_handle != main_window_handle:
                print("    Tentando fechar janela extra e voltar ao foco principal após erro.")
                driver.close()
                driver.switch_to.window(main_window_handle)
            time.sleep(1) 
    
    print("\n--- Processamento de Resultados da Página Concluído ---")
    return True

# --- Inicializando o Navegador ---
print("Iniciando o navegador...")
driver = None

try:
    service = Service(executable_path=chromedriver_path)
    
    chrome_options = Options()

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized") 

    driver = webdriver.Chrome(service=service, options=chrome_options)

    print(f"Navegador aberto! Acessando o site: {site_url}")
    driver.get(site_url)

    main_window_handle = driver.current_window_handle 

    if not preencher_e_pesquisar(driver, data_pesquisa, termo_pesquisa):
        print("Nenhuma publicação encontrada para a pesquisa inicial. Encerrando.")
    else:
        abas_tribunais_locator = (By.CSS_SELECTOR, 'div[role="tab"][class*="mat-tab-label"]')
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(abas_tribunais_locator) 
        )
        print("Abas de tribunal carregadas.")

        abas_elementos_iniciais = driver.find_elements(*abas_tribunais_locator)
        nomes_tribunais = []
        for aba in abas_elementos_iniciais:
            try:
                # Tenta pegar o texto diretamente da div da aba (mat-tab-label)
                nome = aba.text.strip()
                
                # Se o texto direto estiver vazio, tenta procurar o div.mat-tab-label-content
                if not nome:
                    # Tenta encontrar o div que contém o nome do tribunal dentro da aba
                    nome_element = WebDriverWait(aba, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.mat-tab-label-content'))
                    )
                    nome = nome_element.text.strip()
                
                if nome: 
                    nomes_tribunais.append(nome)
            except Exception as e:
                print(f"Aviso: Não foi possível extrair o nome de uma aba de tribunal. Erro: {e}")
                pass 
        
        print(f"Tribunais encontrados: {nomes_tribunais}")

        for nome_tribunal in nomes_tribunais:
            print(f"\n***** Filtrando por Tribunal: {nome_tribunal} *****")
            
            try:
                abas_genericas_locator = (By.CSS_SELECTOR, 'div[role="tab"][class*="mat-tab-label"]')
                todas_abas = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(abas_genericas_locator)
                )
                
                aba_encontrada = None
                for aba in todas_abas:
                    try:
                        # Re-verificamos se é a aba correta antes de clicar
                        # Usando a mesma lógica de extração de nome
                        current_aba_text = aba.text.strip()
                        if not current_aba_text:
                            # Se o texto direto estiver vazio, tenta procurar o div.mat-tab-label-content
                            temp_name_element = WebDriverWait(aba, 1).until( # Reduzindo o timeout aqui para não atrasar muito
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.mat-tab-label-content'))
                            )
                            current_aba_text = temp_name_element.text.strip()

                        if current_aba_text == nome_tribunal:
                            aba_encontrada = aba
                            break 
                    except:
                        pass 

                if aba_encontrada:
                    aba_tribunal = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(aba_encontrada))

                    if 'mat-tab-label-active' not in aba_tribunal.get_attribute('class'):
                        print(f"    Clicando na aba '{nome_tribunal}'...")
                        aba_tribunal.click()
                        print(f"    Aguardando resultados para '{nome_tribunal}' carregarem...")
                        WebDriverWait(driver, 10).until(
                             EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
                        )
                        time.sleep(2) 
                        print(f"    Resultados para '{nome_tribunal}' carregados.")
                    else:
                        print(f"    Aba '{nome_tribunal}' já está ativa.")
                else:
                    print(f"    Aba para o tribunal '{nome_tribunal}' NÃO ENCONTRADA após a filtragem de texto.")
                    continue 

            except Exception as aba_e:
                print(f"Erro ao clicar ou processar a aba do tribunal '{nome_tribunal}': {aba_e}")
                continue 

            pagina_atual = 1
            while True:
                print(f"\n--- Processando Página {pagina_atual} para Tribunal: {nome_tribunal} ---")
                
                processar_resultados_da_pagina_atual(driver, main_window_handle, output_folder)

                proxima_pagina_locator = (By.CSS_SELECTOR, 'li.ui-paginator-next')
                
                try:
                    proxima_pagina_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(proxima_pagina_locator)
                    )
                    if 'ui-state-disabled' in proxima_pagina_button.get_attribute('class'):
                        print(f"    Botão 'Próxima Página' desabilitado. Última página para '{nome_tribunal}'.")
                        break 
                    else:
                        print("    Clicando em 'Próxima Página'...")
                        primeiro_card_antes_click = driver.find_element(By.CSS_SELECTOR, 'article.card.fadeIn')
                        
                        proxima_pagina_button.click()
                        
                        WebDriverWait(driver, 10).until(
                            EC.staleness_of(primeiro_card_antes_click)
                        )
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
                        )
                        print("    Página carregada com sucesso!")
                        pagina_atual += 1
                        time.sleep(1) 
                except Exception as page_nav_e:
                    print(f"    Erro ao navegar para a próxima página ou botão 'Próxima Página' não encontrado/clicável: {page_nav_e}")
                    print(f"    Assumindo que não há mais páginas para o tribunal '{nome_tribunal}'.")
                    break 

    print("\n--- Processamento de Todos os Tribunais e Páginas Concluído ---")

    print("Aguardando 5 segundos antes de fechar o navegador principal.")
    time.sleep(5)

    print("Fechando o navegador.")
    driver.quit()
    print("Navegador fechado.")

except Exception as e:
    print(f"Ocorreu um erro geral: {e}")
    print("Verifique:")
    print("- Se o chromedriver.exe está no caminho correto e é compatível com a versão do Chrome que está sendo usada.")
    print("- Se os seletores (especialmente os novos para abas e paginação) ainda são válidos para o site.")
    if driver:
        driver.quit()
