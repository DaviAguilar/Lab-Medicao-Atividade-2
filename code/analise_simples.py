import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr, pearsonr
import warnings
warnings.filterwarnings('ignore')

# Configuração para melhor visualização
plt.style.use('default')


def analyze_correlation(df, x_col, y_col, title, x_label, y_label, use_log_x=False):
    """
    Função para calcular correlações e gerar gráficos de dispersão.
    """
    # Remove linhas com valores infinitos ou ausentes
    df_clean = df.dropna(subset=[x_col, y_col]).copy()
    
    if df_clean.empty:
        print(f"Não há dados suficientes para analisar: {title}")
        return None, None, None
    
    # Calcula correlações
    spearman_corr, spearman_p = spearmanr(df_clean[x_col], df_clean[y_col])
    pearson_corr, pearson_p = pearsonr(df_clean[x_col], df_clean[y_col])
    
    print(f"\n--- Análise: {title} ---")
    print(f"Correlação de Spearman: {spearman_corr:.3f} (p={spearman_p:.3f})")
    print(f"Correlação de Pearson: {pearson_corr:.3f} (p={pearson_p:.3f})")
    
    if spearman_p < 0.05:
        print("✅ Correlação Spearman é estatisticamente significativa (p < 0.05)")
    else:
        print("❌ Correlação Spearman não é significativa (p >= 0.05)")
    
    # Gera gráfico
    plt.figure(figsize=(10, 6))
    
    if use_log_x:
        df_clean[f'{x_col}_log'] = np.log10(df_clean[x_col] + 1)
        plt.scatter(df_clean[f'{x_col}_log'], df_clean[y_col], alpha=0.6, s=30)
        # Adiciona linha de tendência
        z = np.polyfit(df_clean[f'{x_col}_log'], df_clean[y_col], 1)
        p = np.poly1d(z)
        plt.plot(df_clean[f'{x_col}_log'], p(df_clean[f'{x_col}_log']), "r--", alpha=0.8)
        plt.xlabel(f'{x_label} (log10)')
    else:
        plt.scatter(df_clean[x_col], df_clean[y_col], alpha=0.6, s=30)
        # Adiciona linha de tendência
        z = np.polyfit(df_clean[x_col], df_clean[y_col], 1)
        p = np.poly1d(z)
        plt.plot(df_clean[x_col], p(df_clean[x_col]), "r--", alpha=0.8)
        plt.xlabel(x_label)
    
    plt.ylabel(y_label)
    plt.title(f'{title}\nSpearman: {spearman_corr:.3f} | Pearson: {pearson_corr:.3f}')
    plt.grid(True, alpha=0.3)
    
    # Salva o gráfico
    filename = f"analise_{y_col}_vs_{x_col}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"📊 Gráfico salvo: {filename}")
    plt.show()
    
    return spearman_corr, spearman_p, pearson_corr


def analyze_quality_metrics(df):
    """
    Análise das métricas de qualidade de código.
    """
    print("\n" + "="*60)
    print("📊 ANÁLISE DAS MÉTRICAS DE QUALIDADE")
    print("="*60)
    
    # Métricas básicas
    quality_metrics = ['cbo_mean', 'dit_mean', 'lcom_mean', 'wmc_mean', 'rfc_mean', 'noc_mean']
    available_metrics = [m for m in quality_metrics if m in df.columns]
    
    if not available_metrics:
        print("❌ Nenhuma métrica de qualidade encontrada!")
        return
    
    print(f"\n📈 Estatísticas das métricas de qualidade:")
    for metric in available_metrics:
        if metric in df.columns:
            values = df[metric].dropna()
            if len(values) > 0:
                print(f"\n{metric.upper()}:")
                print(f"  Média: {values.mean():.2f}")
                print(f"  Mediana: {values.median():.2f}")
                print(f"  Desvio Padrão: {values.std():.2f}")
                print(f"  Min: {values.min():.2f}")
                print(f"  Max: {values.max():.2f}")
    
    # Análise de correlações entre métricas
    print(f"\n🔗 Correlações entre métricas de qualidade:")
    correlation_matrix = df[available_metrics].corr()
    
    plt.figure(figsize=(10, 8))
    im = plt.imshow(correlation_matrix, cmap='coolwarm', aspect='auto')
    plt.colorbar(im)
    
    # Adiciona valores na matriz
    for i in range(len(available_metrics)):
        for j in range(len(available_metrics)):
            plt.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}', 
                    ha='center', va='center', fontsize=8)
    
    plt.xticks(range(len(available_metrics)), available_metrics, rotation=45)
    plt.yticks(range(len(available_metrics)), available_metrics)
    plt.title('Matriz de Correlação das Métricas de Qualidade')
    plt.tight_layout()
    plt.savefig('correlacao_metricas_qualidade.png', dpi=300, bbox_inches='tight')
    plt.show()


def analyze_popularity_vs_quality(df):
    """
    RQ1: Relação entre Popularidade e Qualidade
    """
    print("\n" + "="*60)
    print("🔍 RQ1: RELAÇÃO ENTRE POPULARIDADE E QUALIDADE")
    print("="*60)
    
    # Análises de correlação
    quality_metrics = ['cbo_mean', 'dit_mean', 'lcom_mean', 'wmc_mean', 'rfc_mean']
    
    for metric in quality_metrics:
        if metric in df.columns:
            analyze_correlation(df, 'stars', metric, 
                               f'Popularidade vs {metric.upper()}', 
                               'Número de Estrelas (log)', 
                               f'{metric.upper()} Médio',
                               use_log_x=True)


def analyze_maturity_vs_quality(df):
    """
    RQ2: Relação entre Maturidade e Qualidade
    """
    print("\n" + "="*60)
    print("🔍 RQ2: RELAÇÃO ENTRE MATURIDADE E QUALIDADE")
    print("="*60)
    
    if 'age_years' not in df.columns:
        print("❌ Dados de idade não disponíveis!")
        return
    
    quality_metrics = ['cbo_mean', 'dit_mean', 'lcom_mean', 'wmc_mean', 'rfc_mean']
    
    for metric in quality_metrics:
        if metric in df.columns:
            analyze_correlation(df, 'age_years', metric,
                               f'Maturidade vs {metric.upper()}',
                               'Idade do Projeto (anos)',
                               f'{metric.upper()} Médio')


def analyze_size_vs_quality(df):
    """
    RQ3: Relação entre Tamanho e Qualidade
    """
    print("\n" + "="*60)
    print("🔍 RQ3: RELAÇÃO ENTRE TAMANHO E QUALIDADE")
    print("="*60)
    
    if 'size_kb' not in df.columns:
        print("❌ Dados de tamanho não disponíveis!")
        return
    
    quality_metrics = ['cbo_mean', 'dit_mean', 'lcom_mean', 'wmc_mean', 'rfc_mean']
    
    for metric in quality_metrics:
        if metric in df.columns:
            analyze_correlation(df, 'size_kb', metric,
                               f'Tamanho vs {metric.upper()}',
                               'Tamanho do Projeto (KB)',
                               f'{metric.upper()} Médio',
                               use_log_x=True)


def analyze_activity_vs_quality(df):
    """
    RQ4: Relação entre Atividade e Qualidade
    """
    print("\n" + "="*60)
    print("🔍 RQ4: RELAÇÃO ENTRE ATIVIDADE E QUALIDADE")
    print("="*60)
    
    # Calcula métricas de atividade
    if 'updated_at' in df.columns:
        df['days_since_update'] = (pd.to_datetime('now') - pd.to_datetime(df['updated_at'])).dt.days
        df['is_active'] = df['days_since_update'] < 30  # Ativo se atualizado nos últimos 30 dias
    
    activity_metrics = ['forks', 'watchers', 'open_issues']
    quality_metrics = ['cbo_mean', 'dit_mean', 'lcom_mean', 'wmc_mean', 'rfc_mean']
    
    for activity in activity_metrics:
        if activity in df.columns:
            for quality in quality_metrics:
                if quality in df.columns:
                    analyze_correlation(df, activity, quality,
                                       f'{activity.upper()} vs {quality.upper()}',
                                       f'{activity.upper()}',
                                       f'{quality.upper()} Médio',
                                       use_log_x=True)


def generate_summary_report(df):
    """
    Gera relatório resumo da análise.
    """
    print("\n" + "="*60)
    print("📋 RELATÓRIO RESUMO")
    print("="*60)
    
    print(f"\n📊 Dados coletados:")
    print(f"  Total de repositórios: {len(df)}")
    print(f"  Repositórios com métricas válidas: {len(df.dropna(subset=['cbo_mean', 'dit_mean', 'lcom_mean']))}")
    
    if 'stars' in df.columns:
        print(f"  Estrelas médias: {df['stars'].mean():.0f}")
        print(f"  Estrelas mediana: {df['stars'].median():.0f}")
    
    if 'age_years' in df.columns:
        print(f"  Idade média: {df['age_years'].mean():.1f} anos")
        print(f"  Idade mediana: {df['age_years'].median():.1f} anos")
    
    # Salva relatório em arquivo
    with open('relatorio_analise.txt', 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE ANÁLISE DE QUALIDADE DE CÓDIGO JAVA\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total de repositórios analisados: {len(df)}\n")
        f.write(f"Data da análise: {pd.Timestamp.now()}\n\n")
        
        # Adiciona estatísticas básicas
        f.write("ESTATÍSTICAS BÁSICAS:\n")
        f.write("-" * 20 + "\n")
        for col in ['stars', 'age_years', 'cbo_mean', 'dit_mean', 'lcom_mean']:
            if col in df.columns:
                f.write(f"{col}: {df[col].mean():.2f} ± {df[col].std():.2f}\n")
    
    print("\n📄 Relatório salvo em 'relatorio_analise.txt'")


def main():
    try:
        # Tenta carregar o arquivo completo primeiro
        try:
            df = pd.read_csv('resultados_completos.csv')
            print("✅ Carregando dados completos...")
        except FileNotFoundError:
            # Se não encontrar, tenta o arquivo básico
            df = pd.read_csv('resultados_finais.csv')
            print("⚠️ Carregando dados básicos (arquivo completo não encontrado)...")
    except FileNotFoundError:
        print("❌ ERRO: Nenhum arquivo de resultados encontrado!")
        print("Execute primeiro o script de coleta de dados (main.py ou main_enhanced.py)")
        return
    
    print(f"📊 Dados carregados: {len(df)} repositórios")
    
    # Limpeza básica
    df = df.dropna(subset=['cbo_mean', 'dit_mean', 'lcom_mean'])
    print(f"📊 Após limpeza: {len(df)} repositórios com métricas válidas")
    
    if len(df) == 0:
        print("❌ Nenhum dado válido para análise!")
        return
    
    # Executa análises
    analyze_quality_metrics(df)
    analyze_popularity_vs_quality(df)
    analyze_maturity_vs_quality(df)
    analyze_size_vs_quality(df)
    analyze_activity_vs_quality(df)
    generate_summary_report(df)
    
    print("\n🎉 Análise concluída com sucesso!")
    print("📁 Verifique os arquivos de gráficos e relatórios gerados.")


if __name__ == '__main__':
    main()
