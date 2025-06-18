import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime

# --- Configuração Inicial ---
chromedriver_path = "./chromedriver.exe" 
base_url = "https://comunica.pje.jus.br/consulta"

# Dados para a pesquisa
data_pesquisa_inicio = "2025-06-16"
data_pesquisa_fim = "2025-06-16"
termo_pesquisa = "tepedino"
tribunal_sigla = "TJSP" 

# Diretório para salvar os PDFs
output_folder = "pdfs_pje_tjsp"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"Diretório '{output_folder}' criado para salvar os PDFs.")

# --- Funções Auxiliares ---

def processar_resultados_da_pagina_atual(driver, main_window_handle, output_folder, nome_tribunal_atual):
    """
    Processa todos os cards de resultado da página atual, extraindo o número do processo
    e baixando o PDF. Retorna True se encontrou e processou resultados, False caso contrário.
    """
    print("\n--- Processando Resultados da Página Atual ---")
    
    time.sleep(1.5) 
    
    resultados_encontrados = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn') 
    
    if not resultados_encontrados:
        print(f"Nenhum resultado de pesquisa encontrado nesta página para o tribunal '{nome_tribunal_atual}'.")
        return False
    
    print(f"Encontrados {len(resultados_encontrados)} resultados nesta página para o tribunal '{nome_tribunal_atual}'.")

    for i in range(len(resultados_encontrados)): 
        resultados_atuais = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn')
        if i >= len(resultados_atuais): 
            print(f"    Pulando resultado {i+1}, pois a lista de resultados encolheu inesperadamente.")
            continue

        resultado = resultados_atuais[i] 

        print(f"\nProcessando resultado {i+1} do Tribunal 'TJSP':") # Mantendo TJSP fixo aqui
        numero_processo = "Nao_encontrado" 

        try:
            numero_processo_elem = resultado.find_element(By.CSS_SELECTOR, 'div#numero-processo > span.numero-unico-formatado')
            numero_processo = numero_processo_elem.text.strip()
            print(f"    Número do Processo: {numero_processo}")
        except Exception as np_e:
            print(f"    Número do Processo: {numero_processo} (Erro ao extrair: {np_e})")

        try:
            print("    Localizando link 'Imprimir'...")
            link_imprimir_locator = (By.CSS_SELECTOR, 'li[title="Imprimir"] > a')
            
            link_imprimir = WebDriverWait(resultado, 10).until(
                EC.element_to_be_clickable(link_imprimir_locator) 
            )
            print("    Link 'Imprimir' encontrado! Clicando...")
            
            driver.execute_script("arguments[0].click();", link_imprimir)

            print("    Lidando com a nova guia de impressão (PDF)...")
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

            for window_handle in driver.window_handles:
                if window_handle != main_window_handle:
                    driver.switch_to.window(window_handle)
                    break
            
            pdf_url = driver.current_url
            print(f"    URL do PDF: {pdf_url}")

            if pdf_url.endswith(".pdf") or "certidao" in pdf_url:
                unique_id = pdf_url.split('/')[-2] if "/certidao" in pdf_url else pdf_url.split('/')[-1].replace(".pdf", "")
                sanitized_numero_processo = numero_processo.replace('.', '_').replace('-', '_').replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                
                file_name = f"{sanitized_numero_processo}_{nome_tribunal_atual.replace(' ', '_').replace('\n', '')}_{unique_id}_Certidao.pdf"
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
                print("    Tentando fechar janela extra e voltar ao foco principal após erro no download.")
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
    main_window_handle = driver.current_window_handle 

    # --- Construindo a URL de pesquisa diretamente ---
    search_url = (
        f"{base_url}?"
        f"texto={termo_pesquisa}"
        f"&siglaTribunal={tribunal_sigla}"
        f"&dataDisponibilizacaoInicio={data_pesquisa_inicio}"
        f"&dataDisponibilizacaoFim={data_pesquisa_fim}"
    )
    
    print(f"Acessando diretamente a URL de pesquisa filtrada: {search_url}")
    driver.get(search_url)

    print("Aguardando os resultados da pesquisa carregarem na URL direta...")
    try:
        WebDriverWait(driver, 30).until( 
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
        )
        try:
            WebDriverWait(driver, 10).until_not( 
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'mat-progress-spinner')) 
            )
            print("Spinner de carregamento desapareceu (se existia).")
        except:
            print("Nenhum spinner de carregamento detectado ou desapareceu rapidamente.")

        print(f"Resultados para {tribunal_sigla} carregados!")
    except Exception as timeout_e:
        print(f"Tempo limite excedido para carregar resultados na URL direta. Pode não haver resultados para esta data/termo/tribunal: {timeout_e}")
        driver.quit() 
        exit() 

    time.sleep(3) 

    # --- Loop de Paginação (agora para um único tribunal) ---
    pagina_atual = 1
    while True:
        print(f"\n--- Processando Página {pagina_atual} para Tribunal: {tribunal_sigla} ---")
        
        current_cards = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn')
        if not current_cards:
            print(f"    Nenhum card de resultado encontrado na página {pagina_atual} para {tribunal_sigla}. Assumindo fim da paginação ou aba sem resultados.")
            break

        processar_resultados_da_pagina_atual(driver, main_window_handle, output_folder, tribunal_sigla)

        # Localizadores
        proxima_pagina_seta_locator = (By.CSS_SELECTOR, 'li.ui-paginator-next > a')
        numeros_pagina_locator = (By.CSS_SELECTOR, 'span.ui-paginator-pages > a.ui-paginator-page')

        try:
            # 1. Esperar que os números de página do paginador se tornem visíveis
            print("    Esperando que os números de página do paginador se tornem visíveis...")
            paginas_numeradas_visiveis = WebDriverWait(driver, 20).until(
                EC.visibility_of_all_elements_located(numeros_pagina_locator)
            )
            print(f"    Números de página visíveis. Paginador renderizado. Total de números visíveis: {len(paginas_numeradas_visiveis)}")

            # 2. Tentar encontrar e clicar no botão de seta "Próxima Página"
            proxima_pagina_button = None
            is_disabled = True # Inicia como desabilitado e tenta provar o contrário

            try:
                print("    Tentando localizar o botão de seta 'Próxima Página'...")
                # Não usamos WebDriverWait aqui para evitar TimeoutException, apenas tentamos encontrar.
                # Se não encontrar, o NoSuchElementException será capturado no 'except'.
                proxima_pagina_button = driver.find_element(*proxima_pagina_seta_locator)
                print(f"    Botão de seta 'Próxima Página' encontrado no DOM. HTML: {proxima_pagina_button.get_attribute('outerHTML')}")

                # Verifica o estado de disabled
                is_disabled = proxima_pagina_button.get_attribute('aria-disabled') == 'true'
                if not is_disabled: # Se não está desabilitado por aria-disabled, verifica a classe no LI pai
                    try:
                        parent_li = proxima_pagina_button.find_element(By.XPATH, '..')
                        if 'ui-state-disabled' in parent_li.get_attribute('class'):
                            is_disabled = True
                            print("    Botão de seta 'Próxima Página' desabilitado via classe 'ui-state-disabled' no elemento pai (<li>).")
                    except Exception as e_parent:
                        print(f"    Aviso: Erro ao verificar classe 'ui-state-disabled' no pai do botão de seta: {e_parent}")
                
            except Exception as e_find_arrow:
                print(f"    Aviso: Não foi possível encontrar o botão de seta 'Próxima Página' ou erro ao verificar estado: {e_find_arrow}")
                # Isso significa que NoSuchElementException ocorreu, ou outro erro. Consideramos que o botão não está disponível.
                proxima_pagina_button = None 
                is_disabled = True # Força para verdadeiro para tentar a paginação numérica

            clicked_next_page = False

            if proxima_pagina_button and not is_disabled:
                print("    Botão de seta 'Próxima Página' está habilitado. Tentando clicar...")
                driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -50);", proxima_pagina_button)
                time.sleep(0.5) 
                
                primeiro_card_antes_click = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
                )
                driver.execute_script("arguments[0].click();", proxima_pagina_button)
                print("    Clique no botão de seta 'Próxima Página' executado via JavaScript.")
                clicked_next_page = True
            else:
                print("    Botão de seta 'Próxima Página' não disponível ou desabilitado. Tentando clicar no próximo número de página...")
                
                # Encontrar a página ativa
                pagina_ativa_elem = None
                for pagina_num_elem in paginas_numeradas_visiveis:
                    if 'ui-state-active' in pagina_num_elem.get_attribute('class'):
                        pagina_ativa_elem = pagina_num_elem
                        break
                
                if pagina_ativa_elem:
                    try:
                        pagina_ativa_numero = int(pagina_ativa_elem.text)
                        proxima_pagina_numero = pagina_ativa_numero + 1
                        
                        proxima_pagina_numerica_locator = (By.XPATH, f"//span[contains(@class, 'ui-paginator-pages')]/a[text()='{proxima_pagina_numero}']")
                        
                        print(f"    Tentando encontrar o link para a página numérica: {proxima_pagina_numero}")
                        proxima_pagina_numerica_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(proxima_pagina_numerica_locator)
                        )
                        
                        print(f"    Link da página numérica {proxima_pagina_numero} encontrado. HTML: {proxima_pagina_numerica_button.get_attribute('outerHTML')}")
                        
                        # Verifica se a próxima página numérica não está desabilitada (embora se 'element_to_be_clickable' passou, já estaria)
                        if 'ui-state-disabled' not in proxima_pagina_numerica_button.get_attribute('class'):
                            driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -50);", proxima_pagina_numerica_button)
                            time.sleep(0.5)
                            
                            primeiro_card_antes_click = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
                            )
                            driver.execute_script("arguments[0].click();", proxima_pagina_numerica_button)
                            print(f"    Clique na página numérica {proxima_pagina_numero} executado via JavaScript.")
                            clicked_next_page = True
                        else:
                            print(f"    Página numérica {proxima_pagina_numero} encontrada, mas está desabilitada. Fim da paginação.")
                    except ValueError:
                        print(f"    Erro ao converter número da página ativa '{pagina_ativa_elem.text}' para inteiro.")
                    except Exception as e_num_page:
                        print(f"    Não foi possível clicar na próxima página numérica ou ela não existe: {e_num_page}")
                        
            if not clicked_next_page:
                print("    Não foi possível navegar para a próxima página (botão de seta ou número) ou fim da paginação.")
                break # Sai do loop de paginação

            # --- Esperas para o conteúdo da nova página ---
            try:
                WebDriverWait(driver, 20).until_not( 
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'mat-progress-spinner'))
                )
                print("    Spinner de carregamento da paginação desapareceu (se existia).")
            except:
                print("    Nenhum spinner de carregamento de paginação detectado ou desapareceu rapidamente.")

            try:
                # Espera que o primeiro card da página anterior se torne obsoleto
                WebDriverWait(driver, 20).until( 
                    EC.staleness_of(primeiro_card_antes_click) 
                )
                print("    Primeiro card da página anterior se tornou obsoleto.")
            except Exception as stale_e:
                print(f"    Aviso: Primeiro card da página anterior não se tornou obsoleto em 20s. (Pode ser atualização in-place ou erro: {stale_e})")
            
            # Esperar pelos novos cards na página
            WebDriverWait(driver, 20).until( 
                EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
            )
            
            time.sleep(3) # Pausa adicional para garantir que tudo esteja renderizado

            print("    Página carregada com sucesso (novos cards detectados/DOM atualizada)!")
            pagina_atual += 1
            time.sleep(2) # Pequena pausa entre páginas

        except Exception as page_nav_e:
            print(f"    Erro geral ao navegar para a próxima página ou ao processar o paginador: {type(page_nav_e).__name__}: {page_nav_e}")
            try:
                paginator_section = driver.find_element(By.CSS_SELECTOR, 'div.ui-paginator')
                print(f"    HTML da seção do paginador (div.ui-paginator) no momento do erro: {paginator_section.get_attribute('outerHTML')}")
            except Exception as paginator_e:
                print(f"    Não foi possível encontrar a seção do paginador para debug após o erro: {paginator_e}")

            print(f"    Assumindo que não há mais páginas ou erro persistente para o tribunal '{tribunal_sigla}'.")
            break 
                
except Exception as e: 
    print(f"\nOcorreu um erro inesperado durante a execução principal: {e}")
    if driver:
        try:
            screenshot_path_fatal = os.path.join(output_folder, f"erro_fatal_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path_fatal)
            print(f"Screenshot do erro fatal salva em: {screenshot_path_fatal}")
        except:
            pass 
finally: 
    print("Aguardando 5 segundos antes de fechar o navegador principal.")
    time.sleep(5)

    if driver:
        print("Fechando o navegador.")
        driver.quit()
        print("Navegador fechado.")
    else:
        print("Navegador não foi inicializado ou já estava fechado.")
