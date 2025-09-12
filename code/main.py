import os
import requests
import subprocess
import csv
import shutil
import stat
import numpy as np
from datetime import datetime
from dotenv import load_dotenv


# --- FUNÇÃO DE AJUDA PARA DELEÇÃO DE ARQUIVOS (WINDOWS) ---
def remove_readonly(func, path, exc_info):
    if not isinstance(exc_info[1], PermissionError):
        raise exc_info[1]
    os.chmod(path, stat.S_IWRITE)
    func(path)


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


def process_repositories(repos_to_process):
    all_repo_metrics = []
    total_to_process = len(repos_to_process)

    for i, repo in enumerate(repos_to_process):
        repo_full_name = repo['full_name']
        safe_repo_name = repo_full_name.replace('/', '_')
        repo_path = os.path.join(CLONE_DIR, safe_repo_name)
        metrics_path = os.path.join(RESULTS_DIR, safe_repo_name)

        print(f"\n--- Processando {i + 1}/{total_to_process}: {repo_full_name} ---")

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

            # =======================================================================
            # **** LÓGICA CORRIGIDA PARA ENCONTRAR OS ARQUIVOS CSV ****
            # Verifica se o CK gerou os arquivos na pasta raiz do projeto.
            # =======================================================================
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

                # Agora, o script vai encontrar o arquivo no local certo
                with open(dest_csv_path, 'r', encoding='utf-8') as f:
                    reader = list(csv.DictReader(f))
                    if reader:
                        created_at = datetime.strptime(repo['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                        age_days = (datetime.now() - created_at).days

                        cbo_values = [float(row['cbo']) for row in reader if row['cbo'].replace('.', '', 1).isdigit()]
                        dit_values = [float(row['dit']) for row in reader if row['dit'].replace('.', '', 1).isdigit()]
                        lcom_values = [float(row['lcom']) for row in reader if
                                       row['lcom'].replace('.', '', 1).isdigit()]

                        if not cbo_values:
                            print("⚠️ Nenhuma métrica válida encontrada no CSV.")
                            continue

                        repo_summary = {
                            'repository': repo_full_name,
                            'stars': repo.get('stargazers_count', 0),
                            'age_days': age_days,
                            'cbo_mean': np.mean(cbo_values), 'dit_mean': np.mean(dit_values),
                            'lcom_mean': np.mean(lcom_values),
                            'cbo_median': np.median(cbo_values), 'dit_median': np.median(dit_values),
                            'lcom_median': np.median(lcom_values),
                            'cbo_std': np.std(cbo_values), 'dit_std': np.std(dit_values),
                            'lcom_std': np.std(lcom_values)
                        }
                        all_repo_metrics.append(repo_summary)
                        print(
                            f"✅ Métricas sumarizadas: CBO Médio={repo_summary['cbo_mean']:.2f}, LCOM Médio={repo_summary['lcom_mean']:.2f}")
            else:
                print("⚠️ Nenhuma métrica gerada (provavelmente não é um projeto de código Java).")

        except subprocess.CalledProcessError as e:
            print(f"❌ ERRO: O processo CK falhou para {repo_full_name}. Detalhes: {e.stderr}")
        except Exception as e:
            print(f"❌ Ocorreu um erro inesperado com {repo_full_name}: {e}")
        finally:
            if os.path.exists(repo_path):
                print(f"Limpeza de {repo_path}...")
                shutil.rmtree(repo_path, onerror=remove_readonly)
            if os.path.exists(metrics_path):
                shutil.rmtree(metrics_path, onerror=remove_readonly)

    return all_repo_metrics


def save_results_to_csv(metrics):
    if not metrics:
        print("\nNenhuma métrica foi coletada. Nenhum arquivo de resultado foi gerado.")
        return
    final_csv_path = 'resultados_finais.csv'
    print(f"\nSalvando resultados consolidados em '{final_csv_path}'...")
    try:
        with open(final_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
            writer.writeheader()
            writer.writerows(metrics)
        print("✨ Processo concluído com sucesso! ✨")
    except Exception as e:
        print(f"Erro ao salvar o arquivo CSV final: {e}")


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
        metrics_data = process_repositories(all_repos[:5])  # Testando com os 5 primeiros
        save_results_to_csv(metrics_data)
    else:
        print("Nenhum repositório foi encontrado. O script será encerrado.")


if __name__ == "__main__":
    main()