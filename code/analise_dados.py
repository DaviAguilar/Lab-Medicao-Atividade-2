import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr


def analyze_correlation(df, x_col, y_col, title, x_label, y_label):
    """
    Função para calcular a correlação de Spearman e gerar um gráfico de dispersão.
    """
    # Remove linhas com valores infinitos ou ausentes para um cálculo limpo
    df_clean = df.dropna(subset=[x_col, y_col]).copy()

    if df_clean.empty:
        print(f"Não há dados suficientes para analisar a correlação: {title}")
        return

    # Calcula a correlação de Spearman
    # Usamos Spearman porque não assume uma relação linear entre as variáveis.
    corr, p_value = spearmanr(df_clean[x_col], df_clean[y_col])

    print(f"--- Análise: {title} ---")
    print(f"Correlação de Spearman ({x_label} vs. {y_label}): {corr:.3f}")
    print(f"P-valor: {p_value:.3f}")
    if p_value < 0.05:
        print("A correlação é estatisticamente significativa (p < 0.05).")
    else:
        print("A correlação não é estatisticamente significativa (p >= 0.05).")

    # Gerar o gráfico de dispersão com linha de regressão
    plt.figure(figsize=(10, 6))
    sns.regplot(data=df_clean, x=x_col, y=y_col,
                scatter_kws={'alpha': 0.3}, line_kws={'color': 'red'})
    plt.title(f'{title}\nCorrelação de Spearman: {corr:.3f} (p={p_value:.3f})')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    # Usar escala de log para popularidade para melhor visualização
    if x_col == 'stars':
        plt.xscale('log')
    plt.grid(True, which="both", ls="--", linewidth=0.5)

    # Salva a figura em um arquivo
    filename = f"analise_{y_col}_vs_{x_col}.png"
    plt.savefig(filename)
    print(f"Gráfico salvo como '{filename}'")
    plt.show()


def main():
    try:
        # Carrega os dados coletados pelo script main.py
        df = pd.read_csv('resultados_finais.csv')
    except FileNotFoundError:
        print("ERRO: O arquivo 'resultados_finais.csv' não foi encontrado.")
        print("Certifique-se de executar o 'main.py' primeiro para coletar os dados.")
        return

    print("Dados carregados com sucesso. Iniciando análise...")
    print(f"Total de repositórios no CSV: {len(df)}")

    # Limpeza básica de dados (remove linhas onde as métricas principais são nulas)
    df.dropna(subset=['cbo_mean', 'dit_mean', 'lcom_mean'], inplace=True)
    print(f"Repositórios após limpeza de dados: {len(df)}")

    # --- RQ 01: Relação entre Popularidade e Qualidade ---
    # Popularidade é medida pelo número de 'stars'
    analyze_correlation(df, 'stars', 'cbo_mean', 'Popularidade vs. Acoplamento (CBO)', 'Estrelas (log)', 'CBO Médio')
    analyze_correlation(df, 'stars', 'dit_mean', 'Popularidade vs. Profundidade de Herança (DIT)', 'Estrelas (log)',
                        'DIT Médio')
    analyze_correlation(df, 'stars', 'lcom_mean', 'Popularidade vs. Coesão (LCOM)', 'Estrelas (log)', 'LCOM Médio')

    # Para responder às outras RQs, você precisaria adicionar a coleta de mais dados no `main.py`.
    # Exemplo para RQ02 (Maturidade):
    # 1. No main.py, colete 'created_at'.
    # 2. Converta para idade (anos) e salve no CSV.
    # 3. Rode a análise aqui:
    # if 'idade_anos' in df.columns:
    #     analyze_correlation(df, 'idade_anos', 'cbo_mean', 'Maturidade vs. Acoplamento (CBO)', 'Idade (anos)', 'CBO Médio')

    print("\nAnálise concluída.")


if __name__ == '__main__':
    main()