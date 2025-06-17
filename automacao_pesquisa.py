from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains # Importar ActionChains
import requests
import os

# Importar Options para configurar opções do Chrome
from selenium.webdriver.chrome.options import Options 

# --- Configuração Inicial ---
chromedriver_path = "./chromedriver.exe" # Certifique-se de que este chromedriver.exe corresponde ao Chrome que você está usando
site_url = "https://comunica.pje.jus.br/"

# Dados para a pesquisa
data_pesquisa = "16/06/2025" 
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
    time.sleep(0.5) 

    # Espera e preenche campo de pesquisa textual
    campo_pesquisa_texto_locator = (By.CSS_SELECTOR, 'input[formcontrolname="texto"]')
    campo_pesquisa_texto = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(campo_pesquisa_texto_locator) 
    )
    campo_pesquisa_texto.clear() 
    campo_pesquisa_texto.send_keys(termo)
    print(f"Termo digitado: '{termo}'")

    # Aciona a pesquisa
    campo_pesquisa_texto.send_keys(Keys.ENTER)
    print("Busca iniciada!")

    # Espera pelos resultados
    print("Aguardando os resultados da pesquisa carregarem...")
    try:
        # Espera que pelo menos um card de resultado apareça
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
        )
        # E também espera que o spinner (se existir) desapareça.
        try:
            WebDriverWait(driver, 5).until_not(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'mat-progress-spinner')) 
            )
            print("Spinner de carregamento desapareceu (se existia).")
        except:
            print("Nenhum spinner de carregamento detectado ou desapareceu rapidamente.")

        print("Resultados da pesquisa carregados!")
    except Exception as timeout_e:
        print(f"Tempo limite excedido para carregar resultados. Pode não haver resultados para a data/termo: {timeout_e}")
        return False
    return True

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

        print(f"\nProcessando resultado {i+1} do Tribunal '{nome_tribunal_atual}':")
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

    print(f"Navegador aberto! Acessando o site: {site_url}")
    driver.get(site_url)

    if not preencher_e_pesquisar(driver, data_pesquisa, termo_pesquisa):
        print("Nenhuma publicação encontrada para a pesquisa inicial. Encerrando.")
        driver.quit() 
        exit() 

    time.sleep(5) 

    abas_tribunais_locator = (By.CSS_SELECTOR, 'div[role="tab"][class*="mat-tab-label"]')
    
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(abas_tribunais_locator) 
    )
    print("Abas de tribunal carregadas.")

    abas_elementos_iniciais = driver.find_elements(*abas_tribunais_locator)
    nomes_tribunais = []
    for aba_elem in abas_elementos_iniciais:
        try:
            full_text = aba_elem.text.strip()
            if full_text: 
                nomes_tribunais.append(full_text)
            else:
                content_div = WebDriverWait(aba_elem, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'mat-tab-label-content'))
                )
                if content_div.text.strip():
                    nomes_tribunais.append(content_div.text.strip())
                else:
                    print(f"Aviso: Nome de tribunal vazio encontrado para uma aba.")

        except Exception as e:
            print(f"Aviso: Não foi possível extrair o nome de uma aba de tribunal. Erro: {e}")
            print(f"HTML da aba que falhou: {aba_elem.get_attribute('outerHTML')}") 
            pass 
    
    print(f"Tribunais encontrados: {nomes_tribunais}")

    # --- LOOP PRINCIPAL DE PROCESSAMENTO POR TRIBUNAL ---
    for i, nome_tribunal_completo in enumerate(nomes_tribunais): 
        print(f"\n***** Processando Tribunal: {nome_tribunal_completo} (Índice {i}) *****")
        
        time.sleep(3) # Tempo para a interface se estabilizar antes de interagir com a aba
        
        try:
            # Re-encontra TODAS as abas disponíveis no DOM a cada iteração
            # Isso é crucial porque o DOM pode ter mudado após a interação com a aba anterior
            todas_abas_disponiveis = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located(abas_tribunais_locator)
            )
            
            aba_para_clicar = None
            for aba_elemento in todas_abas_disponiveis:
                if aba_elemento.text.strip().replace('\n', '') == nome_tribunal_completo.replace('\n', ''):
                    aba_para_clicar = aba_elemento
                    break
            
            if not aba_para_clicar:
                print(f"    Aba para o tribunal '{nome_tribunal_completo}' não foi encontrada na lista de abas disponíveis. Pulando.")
                continue 
            
            aba_tribunal = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(aba_para_clicar)
            )
            
            # Sempre rolar para o topo para garantir visibilidade
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1) 

            # Rolar o elemento da aba para a vista, com um offset maior
            driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -180);", aba_tribunal) # Aumentei o offset
            time.sleep(1) 

            # Verificar se a aba já está ativa (para evitar cliques desnecessários)
            if 'mat-tab-label-active' in aba_tribunal.get_attribute('class'):
                print(f"    Aba '{nome_tribunal_completo}' já está ativa.")
            else:
                print(f"    Clicando na aba '{nome_tribunal_completo}' via ActionChains (simulando clique de mouse)...")
                try:
                    ActionChains(driver).move_to_element(aba_tribunal).click().perform()
                    print(f"    Aba '{nome_tribunal_completo}' clicada com sucesso via ActionChains.")
                except Exception as click_e:
                    print(f"    Erro ao clicar via ActionChains: {click_e}. Tentando via JavaScript (fallback)...")
                    driver.execute_script("arguments[0].click();", aba_tribunal)
                    print(f"    Aba '{nome_tribunal_completo}' clicada com sucesso via JavaScript.")
                
            # --- VERIFICAÇÃO DE ATIVAÇÃO DA ABA E CARREGAMENTO DO CONTEÚDO ---
            # Espera que a aba se torne ativa (após o clique)
            xpath_aba_ativa = f'//div[contains(@class, "mat-tab-label") and contains(@class, "mat-tab-label-active") and normalize-space(.//div[@class="mat-tab-label-content"]) = "{nome_tribunal_completo.replace("\\n", "")}" ]'
            try:
                WebDriverWait(driver, 20).until( # Aumentamos o tempo aqui
                    EC.presence_of_element_located((By.XPATH, xpath_aba_ativa))
                )
                print(f"    Aba '{nome_tribunal_completo}' ativada (classe 'active' detectada).")
            except Exception as active_e:
                print(f"    Aviso: Aba '{nome_tribunal_completo}' não parece ter se tornado ativa dentro do tempo esperado: {active_e}")
                screenshot_path = os.path.join(output_folder, f"erro_ativacao_aba_{nome_tribunal_completo.replace('/', '_').replace('\n', '')}_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                print(f"    Screenshot de erro de ativação salva em: {screenshot_path}")
                continue 
            
            # Espera que o spinner (se existir) desapareça.
            print(f"    Aguardando resultados para '{nome_tribunal_completo}' carregarem (esperando spinner desaparecer)...")
            try:
                WebDriverWait(driver, 25).until_not( 
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'mat-progress-spinner'))
                )
                print("    Spinner de carregamento desapareceu.")
            except:
                print("    Nenhum spinner de carregamento detectado ou desapareceu rapidamente para esta aba.")
            
            # Esperar que um card com o nome do tribunal atual apareça no texto.
            nome_tribunal_simples = nome_tribunal_completo.split('\n')[0].strip()
            try:
                WebDriverWait(driver, 25).until( 
                    EC.presence_of_element_located((By.XPATH, f'//article[contains(@class, "card")]//span[contains(text(), "{nome_tribunal_simples}")]'))
                )
                print(f"    Cards de resultado para '{nome_tribunal_completo}' (contendo '{nome_tribunal_simples}') presentes.")
            except Exception as cards_e:
                print(f"    Nenhum card de resultado contendo '{nome_tribunal_simples}' encontrado para '{nome_tribunal_completo}' após clique na aba: {cards_e}. Pode não haver resultados ou o conteúdo não carregou. Pulando.")
                screenshot_path = os.path.join(output_folder, f"erro_cards_nao_carregados_{nome_tribunal_completo.replace('/', '_').replace('\n', '')}_{int(time.time())}.png")
                driver.save_screenshot(screenshot_path)
                print(f"    Screenshot de erro de carregamento de cards salva em: {screenshot_path}")
                continue 

            time.sleep(3) 

            # --- Loop de Paginação (agora dentro do loop de tribunais) ---
            pagina_atual = 1
            while True:
                print(f"\n--- Processando Página {pagina_atual} para Tribunal: {nome_tribunal_completo} ---")
                
                current_cards = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn')
                if not current_cards:
                    print(f"    Nenhum card de resultado encontrado na página {pagina_atual} para {nome_tribunal_completo}. Assumindo fim da paginação ou aba sem resultados.")
                    break

                processar_resultados_da_pagina_atual(driver, main_window_handle, output_folder, nome_tribunal_completo)

                proxima_pagina_locator = (By.CSS_SELECTOR, 'li.ui-paginator-next')
                
                try:
                    proxima_pagina_button = WebDriverWait(driver, 10).until( 
                        EC.element_to_be_clickable(proxima_pagina_locator)
                    )
                    
                    if 'ui-state-disabled' in proxima_pagina_button.get_attribute('class') or \
                       proxima_pagina_button.get_attribute('aria-disabled') == 'true':
                        print(f"    Botão 'Próxima Página' desabilitado. Última página para '{nome_tribunal_completo}'.")
                        break 
                    else:
                        print("    Clicando em 'Próxima Página'...")
                        driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -50);", proxima_pagina_button)
                        time.sleep(0.5) 
                        
                        primeiro_card_antes_click = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
                        )

                        # Usar ActionChains para o botão de paginação também para consistência
                        ActionChains(driver).move_to_element(proxima_pagina_button).click().perform()
                        
                        try:
                            WebDriverWait(driver, 15).until_not(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, 'mat-progress-spinner'))
                            )
                            print("    Spinner de carregamento da paginação desapareceu.")
                        except:
                            print("    Nenhum spinner de carregamento de paginação detectado ou desapareceu rapidamente.")

                        try:
                            WebDriverWait(driver, 15).until(
                                EC.staleness_of(primeiro_card_antes_click)
                            )
                            print("    Primeiro card da página anterior se tornou obsoleto.")
                        except:
                            print("    Aviso: Primeiro card da página anterior não se tornou obsoleto, mas prosseguindo.")

                        WebDriverWait(driver, 15).until( 
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
                        )
                        print("    Página carregada com sucesso (novos cards detectados)!")
                        pagina_atual += 1
                        time.sleep(3) 
                except Exception as page_nav_e:
                    print(f"    Erro ao navegar para a próxima página ou botão 'Próxima Página' não encontrado/clicável: {page_nav_e}")
                    try:
                        failed_button = driver.find_element(*proxima_pagina_locator)
                        print(f"    HTML do botão 'Próxima Página' que falhou: {failed_button.get_attribute('outerHTML')}")
                    except:
                        print("    Não foi possível obter o HTML do botão 'Próxima Página'.")
                    print(f"    Assumindo que não há mais páginas para o tribunal '{nome_tribunal_completo}'.")
                    break 

        except Exception as aba_e:
            print(f"Erro ao clicar ou processar a aba do tribunal '{nome_tribunal_completo}': {aba_e}")
            screenshot_path = os.path.join(output_folder, f"erro_aba_{nome_tribunal_completo.replace('/', '_').replace('\n', '')}_{int(time.time())}.png")
            html_path = os.path.join(output_folder, f"erro_aba_{nome_tribunal_completo.replace('/', '_').replace('\n', '')}_{int(time.time())}.html")
            try:
                driver.save_screenshot(screenshot_path)
                print(f"    Screenshot de erro salva em: {screenshot_path}")
            except:
                print("    Não foi possível salvar screenshot.")
            try:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"    HTML da página no momento do erro salvo em: {html_path}")
            except:
                print("    Não foi possível salvar o HTML da página.")
            
            continue # Continua para a próxima aba de tribunal
                
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
