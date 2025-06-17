import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime

# --- Configuração Inicial ---
chromedriver_path = "./chromedriver.exe" # Certifique-se de que este chromedriver.exe corresponde ao Chrome que você está usando
base_url = "https://comunica.pje.jus.br/consulta"

# Dados para a pesquisa
# Usaremos a data de hoje para a pesquisa
data_pesquisa_inicio = datetime.now().strftime("%Y-%m-%d") # Formato YYYY-MM-DD para URL
data_pesquisa_fim = datetime.now().strftime("%Y-%m-%d")   # Formato YYYY-MM-DD para URL
termo_pesquisa = "tepedino"
tribunal_sigla = "TJSP" # Tribunal do Estado de São Paulo, conforme sua sugestão

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
    
    time.sleep(1.5) # Adicionar um pequeno tempo para garantir que a DOM está estável
    
    resultados_encontrados = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn') 
    
    if not resultados_encontrados:
        print(f"Nenhum resultado de pesquisa encontrado nesta página para o tribunal '{nome_tribunal_atual}'.")
        return False
    
    print(f"Encontrados {len(resultados_encontrados)} resultados nesta página para o tribunal '{nome_tribunal_atual}'.")

    for i in range(len(resultados_encontrados)): 
        # Re-obtém os resultados a cada iteração do loop de cards para evitar StaleElementReferenceException
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
                
                # INCLUINDO O NOME DO TRIBUNAL NO NOME DO ARQUIVO
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
    # URL completa: https://comunica.pje.jus.br/consulta?texto=tepedino&siglaTribunal=TJSP&dataDisponibilizacaoInicio=2025-06-17&dataDisponibilizacaoFim=2025-06-17
    # Usamos f-strings para construir a URL de forma limpa
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
        WebDriverWait(driver, 30).until( # Aumentado o timeout para a página inicial carregar
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
        )
        try:
            WebDriverWait(driver, 10).until_not( # Pode haver um spinner mesmo na carga direta
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'mat-progress-spinner')) 
            )
            print("Spinner de carregamento desapareceu (se existia).")
        except:
            print("Nenhum spinner de carregamento detectado ou desapareceu rapidamente.")

        print(f"Resultados para {tribunal_sigla} carregados!")
    except Exception as timeout_e:
        print(f"Tempo limite excedido para carregar resultados na URL direta. Pode não haver resultados para esta data/termo/tribunal: {timeout_e}")
        # Neste caso, não há o que processar, encerramos.
        driver.quit() 
        exit() 

    time.sleep(3) # Pequeno delay após o carregamento inicial

    # --- Loop de Paginação (agora para um único tribunal) ---
    pagina_atual = 1
    while True:
        print(f"\n--- Processando Página {pagina_atual} para Tribunal: {tribunal_sigla} ---")
        
        current_cards = driver.find_elements(By.CSS_SELECTOR, 'article.card.fadeIn')
        if not current_cards:
            print(f"    Nenhum card de resultado encontrado na página {pagina_atual} para {tribunal_sigla}. Assumindo fim da paginação ou aba sem resultados.")
            break

        processar_resultados_da_pagina_atual(driver, main_window_handle, output_folder, tribunal_sigla)

        proxima_pagina_locator = (By.CSS_SELECTOR, 'li.ui-paginator-next')
        
        try:
            proxima_pagina_button = WebDriverWait(driver, 10).until( 
                EC.element_to_be_clickable(proxima_pagina_locator)
            )
            
            if 'ui-state-disabled' in proxima_pagina_button.get_attribute('class') or \
               proxima_pagina_button.get_attribute('aria-disabled') == 'true':
                print(f"    Botão 'Próxima Página' desabilitado. Última página para '{tribunal_sigla}'.")
                break 
            else:
                print("    Clicando em 'Próxima Página'...")
                # Rolar para o botão de paginação antes de clicar
                driver.execute_script("arguments[0].scrollIntoView(true); window.scrollBy(0, -50);", proxima_pagina_button)
                time.sleep(0.5) 
                
                # Obter uma referência ao primeiro card antes do clique para esperar a mudança de página
                primeiro_card_antes_click = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
                )

                # Clicar no botão da próxima página
                driver.execute_script("arguments[0].click();", proxima_pagina_button) # Usando JS Click aqui, ActionChains pode ser um overkill para paginação simples
                
                try:
                    WebDriverWait(driver, 15).until_not(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'mat-progress-spinner'))
                    )
                    print("    Spinner de carregamento da paginação desapareceu.")
                except:
                    print("    Nenhum spinner de carregamento de paginação detectado ou desapareceu rapidamente.")

                try:
                    WebDriverWait(driver, 15).until(
                        EC.staleness_of(primeiro_card_antes_click) # Espera que o card anterior desapareça
                    )
                    print("    Primeiro card da página anterior se tornou obsoleto.")
                except:
                    print("    Aviso: Primeiro card da página anterior não se tornou obsoleto, mas prosseguindo.")

                WebDriverWait(driver, 15).until( # Espera que novos cards apareçam
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'article.card.fadeIn'))
                )
                print("    Página carregada com sucesso (novos cards detectados)!")
                pagina_atual += 1
                time.sleep(3) # Pequeno delay entre as páginas
        except Exception as page_nav_e:
            print(f"    Erro ao navegar para a próxima página ou botão 'Próxima Página' não encontrado/clicável: {page_nav_e}")
            try:
                failed_button = driver.find_element(*proxima_pagina_locator)
                print(f"    HTML do botão 'Próxima Página' que falhou: {failed_button.get_attribute('outerHTML')}")
            except:
                print("    Não foi possível obter o HTML do botão 'Próxima Página'.")
            print(f"    Assumindo que não há mais páginas para o tribunal '{tribunal_sigla}'.")
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
