import os
import requests
import subprocess
import csv
import shutil
import stat
import numpy as np
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv


# --- FUNÇÃO DE AJUDA PARA DELEÇÃO DE ARQUIVOS (WINDOWS) ---
def remove_readonly(func, path, exc_info):
    if not isinstance(exc_info[1], PermissionError):
        raise exc_info[1]
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except (PermissionError, OSError) as e:
        # Se ainda não conseguir, tenta forçar a remoção
        try:
            if os.path.isdir(path):
                # Tenta remover o diretório recursivamente
                import time
                time.sleep(0.1)  # Pequena pausa para liberar o arquivo
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
        except:
            # Se ainda falhar, apenas ignora o erro
            pass


# --- CONFIGURAÇÕES GLOBAIS ---
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env, se existir
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    # Substitua pela sua chave caso não queira usar variáveis de ambiente
    GITHUB_TOKEN = "SEU_TOKEN_AQUI"
    if GITHUB_TOKEN == "SEU_TOKEN_AQUI":
        raise ValueError(
            "Token do GitHub não encontrado! Defina a variável de ambiente GITHUB_TOKEN ou substitua no código.")

headers = {'Authorization': f'token {GITHUB_TOKEN}'}
CLONE_DIR = "temp_repos"
RESULTS_DIR = "ck_metrics"
CK_JAR_PATH = "ck.jar"  # Renomeie o 'primeiro.jar' para 'ck.jar' ou mude esta variável


# --- FUNÇÕES PRINCIPAIS ---
def should_skip_repo(repo):
    """Verifica se um repositório deve ser pulado devido a problemas conhecidos"""
    repo_name = repo['full_name'].lower()
    
    # Repositórios conhecidos por terem problemas no Windows
    problematic_repos = {
        'spring-projects/spring-boot': 'Filename too long (Windows limitation)',
        'elastic/elasticsearch': 'Muito grande + filename issues',
        'apache/hadoop': 'Muito grande (>500MB)',
        'apache/kafka': 'Muito grande (>200MB)',
        'apache/spark': 'Muito grande (>300MB)',
    }
    
    if repo_name in problematic_repos:
        return True, problematic_repos[repo_name]
    
    # Filtros por tamanho (se disponível) - mais conservador
    if 'size' in repo:
        size_mb = repo['size'] / 1024  # Converter para MB
        if size_mb > 500:  # Apenas repositórios > 500MB
            return True, f"Repositório muito grande ({size_mb:.1f}MB)"
        elif size_mb > 200:  # Aviso para repositórios grandes
            return False, f"Repositório grande ({size_mb:.1f}MB) - processando com cuidado"
    
    # Filtros por número de arquivos (se disponível)
    if 'size' in repo and repo['size'] > 50000:  # Muitos arquivos
        return False, f"Muitos arquivos ({repo['size']} arquivos) - processando com cuidado"
        
    return False, "Repositório OK para processamento"


def fetch_github_repos():
    print("Buscando repositórios no GitHub...")
    all_repos = []
    try:
        for page in range(1, 11):
            url = f'https://api.github.com/search/repositories?q=language:java&sort=stars&order=desc&per_page=100&page={page}'
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            all_repos.extend(response.json()['items'])
            print(f"Página {page}/10... {len(all_repos)} repositórios encontrados.")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar repositórios: {e}")
        return []
    return all_repos


def calculate_additional_metrics(csv_data):
    """Calcula métricas adicionais para análise de qualidade"""
    if not csv_data:
        return {}
    
    # Converte para DataFrame para facilitar cálculos
    df = pd.DataFrame(csv_data)
    
    # Métricas de complexidade
    wmc_values = [float(row['wmc']) for row in csv_data if row['wmc'].replace('.', '', 1).isdigit()]
    rfc_values = [float(row['rfc']) for row in csv_data if row['rfc'].replace('.', '', 1).isdigit()]
    cbo_values = [float(row['cbo']) for row in csv_data if row['cbo'].replace('.', '', 1).isdigit()]
    dit_values = [float(row['dit']) for row in csv_data if row['dit'].replace('.', '', 1).isdigit()]
    lcom_values = [float(row['lcom']) for row in csv_data if row['lcom'].replace('.', '', 1).isdigit()]
    noc_values = [float(row['noc']) for row in csv_data if row['noc'].replace('.', '', 1).isdigit()]
    
    metrics = {}
    
    if wmc_values:
        metrics.update({
            'wmc_mean': np.mean(wmc_values),
            'wmc_median': np.median(wmc_values),
            'wmc_std': np.std(wmc_values),
            'wmc_max': np.max(wmc_values),
            'wmc_min': np.min(wmc_values)
        })
    
    if rfc_values:
        metrics.update({
            'rfc_mean': np.mean(rfc_values),
            'rfc_median': np.median(rfc_values),
            'rfc_std': np.std(rfc_values),
            'rfc_max': np.max(rfc_values),
            'rfc_min': np.min(rfc_values)
        })
    
    if cbo_values:
        metrics.update({
            'cbo_mean': np.mean(cbo_values),
            'cbo_median': np.median(cbo_values),
            'cbo_std': np.std(cbo_values),
            'cbo_max': np.max(cbo_values),
            'cbo_min': np.min(cbo_values)
        })
    
    if dit_values:
        metrics.update({
            'dit_mean': np.mean(dit_values),
            'dit_median': np.median(dit_values),
            'dit_std': np.std(dit_values),
            'dit_max': np.max(dit_values),
            'dit_min': np.min(dit_values)
        })
    
    if lcom_values:
        metrics.update({
            'lcom_mean': np.mean(lcom_values),
            'lcom_median': np.median(lcom_values),
            'lcom_std': np.std(lcom_values),
            'lcom_max': np.max(lcom_values),
            'lcom_min': np.min(lcom_values)
        })
    
    if noc_values:
        metrics.update({
            'noc_mean': np.mean(noc_values),
            'noc_median': np.median(noc_values),
            'noc_std': np.std(noc_values),
            'noc_max': np.max(noc_values),
            'noc_min': np.min(noc_values)
        })
    
    # Métricas de qualidade calculadas
    if wmc_values and cbo_values:
        # Complexidade média ponderada
        complexity_scores = [w + c for w, c in zip(wmc_values, cbo_values)]
        metrics['complexity_mean'] = np.mean(complexity_scores)
        metrics['complexity_std'] = np.std(complexity_scores)
    
    if lcom_values:
        # Coesão média (inverso do LCOM)
        cohesion_scores = [1.0 / (l + 1) for l in lcom_values]
        metrics['cohesion_mean'] = np.mean(cohesion_scores)
        metrics['cohesion_std'] = np.std(cohesion_scores)
    
    # Contagem de classes
    metrics['total_classes'] = len(csv_data)
    
    return metrics


def process_repositories(repos_to_process):
    all_repo_metrics = []
    total_to_process = len(repos_to_process)
    successful_repos = 0
    failed_repos = 0
    skipped_repos = 0
    start_time = datetime.now()

    print(f"\n📊 Processando {total_to_process} repositórios...")
    print("=" * 60)

    for i, repo in enumerate(repos_to_process):
        repo_full_name = repo['full_name']
        safe_repo_name = repo_full_name.replace('/', '_')
        repo_path = os.path.join(CLONE_DIR, safe_repo_name)
        metrics_path = os.path.join(RESULTS_DIR, safe_repo_name)
        
        # Filtros para repositórios problemáticos
        should_skip, reason = should_skip_repo(repo)
        if should_skip:
            skipped_repos += 1
            print(f"\n--- Pulando {i + 1}/{total_to_process}: {repo_full_name} ---")
            print(f"⚠️ Motivo: {reason}")
            continue
        elif "cuidado" in reason.lower():
            print(f"\n--- Processando {i + 1}/{total_to_process}: {repo_full_name} ---")
            print(f"⚠️ Aviso: {reason}")
        else:
            print(f"\n--- Processando {i + 1}/{total_to_process}: {repo_full_name} ---")
            print(f"✅ {reason}")

        # Cálculo de progresso e tempo estimado
        elapsed_time = datetime.now() - start_time
        if i > 0:
            avg_time_per_repo = elapsed_time.total_seconds() / i
            remaining_repos = total_to_process - i
            estimated_remaining_time = avg_time_per_repo * remaining_repos
            estimated_completion = datetime.now().timestamp() + estimated_remaining_time
            estimated_completion_str = datetime.fromtimestamp(estimated_completion).strftime("%H:%M:%S")
        else:
            estimated_completion_str = "Calculando..."
        
        progress_percent = ((i + 1) / total_to_process) * 100
        
        print(f"⏱️  Tempo decorrido: {elapsed_time}")
        print(f"📈 Sucessos: {successful_repos} | ❌ Falhas: {failed_repos} | ⏭️ Pulados: {skipped_repos}")
        if i > 0:
            print(f"🕐 Previsão de conclusão: {estimated_completion_str}")

        try:
            os.makedirs(metrics_path, exist_ok=True)
            print(f"Clonando {repo['clone_url']}...")
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo['clone_url'], repo_path],
                check=True, capture_output=True, text=True, encoding='utf-8'
            )

            print("Executando a análise do CK...")
            result = subprocess.run(
                ['java', '-jar', CK_JAR_PATH, repo_path, metrics_path],
                capture_output=True, text=True, encoding='utf-8'
            )
            result.check_returncode()

            # Verifica se o CK gerou os arquivos na pasta raiz do projeto
            generated_files_in_root = ['class.csv', 'method.csv', 'field.csv', 'variable.csv']
            source_csv_path = 'class.csv'

            if os.path.exists(source_csv_path):
                # Move o arquivo principal para o diretório de resultados correto
                dest_csv_path = os.path.join(metrics_path, 'class.csv')
                shutil.move(source_csv_path, dest_csv_path)

                # Limpa outros arquivos CSV gerados na raiz
                for f in generated_files_in_root:
                    if f != 'class.csv' and os.path.exists(f):
                        os.remove(f)

                # Lê e processa os dados do CSV
                with open(dest_csv_path, 'r', encoding='utf-8') as f:
                    reader = list(csv.DictReader(f))
                    if reader:
                        created_at = datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                        age_days = (datetime.now() - created_at).days
                        age_years = age_days / 365.25

                        # Calcula métricas básicas
                        basic_metrics = calculate_additional_metrics(reader)
                        
                        if not basic_metrics:
                            print("⚠️ Nenhuma métrica válida encontrada no CSV.")
                            continue

                        # Dados do repositório
                        repo_summary = {
                            'repository': repo_full_name,
                            'stars': repo.get('stargazers_count', 0),
                            'forks': repo.get('forks_count', 0),
                            'watchers': repo.get('watchers_count', 0),
                            'open_issues': repo.get('open_issues_count', 0),
                            'size_kb': repo.get('size', 0),
                            'language': repo.get('language', 'Java'),
                            'created_at': repo['created_at'],
                            'updated_at': repo.get('updated_at', ''),
                            'pushed_at': repo.get('pushed_at', ''),
                            'age_days': age_days,
                            'age_years': age_years,
                            'has_wiki': repo.get('has_wiki', False),
                            'has_pages': repo.get('has_pages', False),
                            'has_downloads': repo.get('has_downloads', False),
                            'has_issues': repo.get('has_issues', True),
                            'has_projects': repo.get('has_projects', False),
                            'archived': repo.get('archived', False),
                            'disabled': repo.get('disabled', False),
                            'fork': repo.get('fork', False),
                            'private': repo.get('private', False),
                            'license': repo.get('license', {}).get('name', '') if repo.get('license') else '',
                            'topics': ', '.join(repo.get('topics', [])),
                            'default_branch': repo.get('default_branch', 'main'),
                        }
                        
                        # Adiciona todas as métricas calculadas
                        repo_summary.update(basic_metrics)
                        
                        all_repo_metrics.append(repo_summary)
                        successful_repos += 1
                        print(f"✅ Métricas sumarizadas: CBO Médio={basic_metrics.get('cbo_mean', 0):.2f}, LCOM Médio={basic_metrics.get('lcom_mean', 0):.2f}")
                        
                        # Salva progresso a cada 50 repositórios
                        if len(all_repo_metrics) % 50 == 0:
                            save_results_to_csv(all_repo_metrics, is_final=False)
            else:
                print("⚠️ Nenhuma métrica gerada (provavelmente não é um projeto de código Java).")

        except subprocess.CalledProcessError as e:
            failed_repos += 1
            print(f"❌ ERRO: O processo CK falhou para {repo_full_name}. Detalhes: {e.stderr}")
        except Exception as e:
            failed_repos += 1
            print(f"❌ Ocorreu um erro inesperado com {repo_full_name}: {e}")
        finally:
            # Limpeza mais robusta dos diretórios
            try:
                if os.path.exists(repo_path):
                    print(f"Limpeza de {repo_path}...")
                    shutil.rmtree(repo_path, onerror=remove_readonly)
            except Exception as e:
                print(f"⚠️ Aviso: Não foi possível limpar {repo_path}: {e}")
                # Tenta forçar a limpeza
                try:
                    import time
                    time.sleep(0.5)
                    shutil.rmtree(repo_path, ignore_errors=True)
                except:
                    pass
            
            try:
                if os.path.exists(metrics_path):
                    shutil.rmtree(metrics_path, onerror=remove_readonly)
            except Exception as e:
                print(f"⚠️ Aviso: Não foi possível limpar {metrics_path}: {e}")
                # Tenta forçar a limpeza
                try:
                    import time
                    time.sleep(0.5)
                    shutil.rmtree(metrics_path, ignore_errors=True)
                except:
                    pass

    # Resumo final
    total_time = datetime.now() - start_time
    processed_repos = successful_repos + failed_repos
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL:")
    print(f"✅ Repositórios processados com sucesso: {successful_repos}")
    print(f"❌ Repositórios com falha: {failed_repos}")
    print(f"⏭️  Repositórios pulados (muito grandes): {skipped_repos}")
    print(f"📈 Taxa de sucesso: {(successful_repos / processed_repos * 100):.1f}%" if processed_repos > 0 else "N/A")
    print(f"⏱️  Tempo total: {total_time}")
    print(f"⚡ Tempo médio por repositório: {total_time.total_seconds() / processed_repos:.1f}s" if processed_repos > 0 else "N/A")
    print("=" * 60)

    return all_repo_metrics


def save_results_to_csv(metrics, is_final=True):
    if not metrics:
        if is_final:
            print("\nNenhuma métrica foi coletada. Nenhum arquivo de resultado foi gerado.")
        return
    
    if is_final:
        final_csv_path = 'resultados_completos.csv'
        print(f"\nSalvando resultados consolidados em '{final_csv_path}'...")
    else:
        final_csv_path = 'resultados_parciais.csv'
        print(f"\n💾 Salvando progresso intermediário em '{final_csv_path}'...")
    
    try:
        with open(final_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
            writer.writeheader()
            writer.writerows(metrics)
        
        if is_final:
            print("✨ Processo concluído com sucesso! ✨")
        else:
            print(f"✅ Progresso salvo: {len(metrics)} repositórios processados")
    except Exception as e:
        print(f"Erro ao salvar o arquivo CSV: {e}")


def main():
    if not os.path.exists(CK_JAR_PATH):
        print(f"ERRO: Arquivo '{CK_JAR_PATH}' não encontrado.")
        return

    # Limpa diretórios de execuções anteriores
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR, onerror=remove_readonly)
    if os.path.exists(RESULTS_DIR):
        shutil.rmtree(RESULTS_DIR, onerror=remove_readonly)

    os.makedirs(CLONE_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    all_repos = fetch_github_repos()
    if all_repos:
        print(f"\n🚀 Iniciando análise de {len(all_repos)} repositórios...")
        print("⚠️  ATENÇÃO: Este processo pode levar várias horas para completar!")
        print("💡 Dica: Você pode interromper o processo com Ctrl+C a qualquer momento.")
        
        # Pergunta ao usuário se quer continuar
        try:
            resposta = input("\nDeseja continuar com a análise de todos os 1000 repositórios? (s/n): ").lower().strip()
            if resposta not in ['s', 'sim', 'y', 'yes']:
                print("❌ Processo cancelado pelo usuário.")
                return
        except KeyboardInterrupt:
            print("\n❌ Processo cancelado pelo usuário.")
            return
        
        metrics_data = process_repositories(all_repos)  # Processando todos os repositórios
        save_results_to_csv(metrics_data)
    else:
        print("Nenhum repositório foi encontrado. O script será encerrado.")


if __name__ == "__main__":
    main()
