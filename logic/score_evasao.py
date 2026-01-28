from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple

import pandas as pd


# =========================
# Configurações do Score v1
# =========================

@dataclass(frozen=True)
class ScoreConfig:
    # janelas
    dias_janela_total: int = 28   # últimas 4 semanas
    dias_janela_recente: int = 14 # últimas 2 semanas

    # pesos (soma máxima = 100)
    peso_baixo_engajamento: int = 30
    peso_queda_recente: int = 30
    peso_ausencia_consecutiva: int = 25
    peso_irregularidade: int = 15


# =========================
# Utilidades
# =========================

def _parse_data(df: pd.DataFrame, coluna_data: str = "data") -> pd.DataFrame:
    out = df.copy()
    out[coluna_data] = pd.to_datetime(out[coluna_data], errors="coerce").dt.date
    out = out.dropna(subset=[coluna_data])
    return out


def _today_from_data(df: pd.DataFrame, coluna_data: str = "data") -> datetime.date:
    # usa a data mais recente do arquivo como "hoje" para tornar o score reprodutível
    return max(df[coluna_data])


def _daterange_days(end_date, days: int):
    start = end_date - timedelta(days=days - 1)
    return start, end_date


# =========================
# Componentes do Score
# =========================

def componente_baixo_engajamento(presencas_28d: int, cfg: ScoreConfig) -> Tuple[int, str]:
    """
    Penaliza quem comparece pouco nas últimas 4 semanas.
    Regras simples (ajustáveis):
    - 0–1 presenças: 100% do peso
    - 2–3 presenças: 70% do peso
    - 4–5 presenças: 40% do peso
    - 6+ presenças: 0% do peso
    """
    if presencas_28d <= 1:
        return cfg.peso_baixo_engajamento, "engajamento muito baixo (0–1 presença em 28 dias)"
    if presencas_28d <= 3:
        return round(cfg.peso_baixo_engajamento * 0.7), "engajamento baixo (2–3 presenças em 28 dias)"
    if presencas_28d <= 5:
        return round(cfg.peso_baixo_engajamento * 0.4), "engajamento moderado (4–5 presenças em 28 dias)"
    return 0, "engajamento bom (6+ presenças em 28 dias)"


def componente_queda_recente(presencas_14d: int, presencas_14d_prev: int, cfg: ScoreConfig) -> Tuple[int, str]:
    """
    Compara as 2 semanas recentes com as 2 semanas anteriores.
    Penaliza queda:
    - Queda >= 50%: 100% do peso
    - Queda 25–49%: 60% do peso
    - Queda 10–24%: 30% do peso
    - Sem queda relevante: 0
    """
    # se no período anterior era zero, não há "queda" mensurável (a pessoa já estava ausente)
    if presencas_14d_prev == 0:
        return 0, "sem base para queda (14 dias anteriores = 0)"

    ratio = presencas_14d / presencas_14d_prev  # <1 significa queda
    if ratio <= 0.5:
        return cfg.peso_queda_recente, "queda forte de frequência (>=50%)"
    if ratio <= 0.75:
        return round(cfg.peso_queda_recente * 0.6), "queda moderada de frequência (25–49%)"
    if ratio <= 0.9:
        return round(cfg.peso_queda_recente * 0.3), "queda leve de frequência (10–24%)"
    return 0, "frequência estável ou melhorou"


def componente_ausencia_consecutiva(dias_desde_ultima: int, cfg: ScoreConfig) -> Tuple[int, str]:
    """
    Penaliza quanto maior o tempo sem aparecer.
    - 0–3 dias: 0
    - 4–7 dias: 40% do peso
    - 8–14 dias: 70% do peso
    - 15+ dias: 100% do peso
    """
    if dias_desde_ultima <= 3:
        return 0, "ausência curta (até 3 dias)"
    if dias_desde_ultima <= 7:
        return round(cfg.peso_ausencia_consecutiva * 0.4), "ausência relevante (4–7 dias)"
    if dias_desde_ultima <= 14:
        return round(cfg.peso_ausencia_consecutiva * 0.7), "ausência alta (8–14 dias)"
    return cfg.peso_ausencia_consecutiva, "ausência crítica (15+ dias)"


def componente_irregularidade(dias_unicos_28d: int, cfg: ScoreConfig) -> Tuple[int, str]:
    """
    Irregularidade (proxy simples): quantos 'dias únicos' a pessoa apareceu na janela.
    Quem aparece em poucos dias únicos tende a ter rotina fraca.
    - 1 dia: 100% do peso
    - 2 dias: 70%
    - 3 dias: 40%
    - 4+ dias: 0
    """
    if dias_unicos_28d <= 1:
        return cfg.peso_irregularidade, "padrão muito irregular (1 dia único em 28 dias)"
    if dias_unicos_28d == 2:
        return round(cfg.peso_irregularidade * 0.7), "padrão irregular (2 dias únicos em 28 dias)"
    if dias_unicos_28d == 3:
        return round(cfg.peso_irregularidade * 0.4), "padrão parcialmente irregular (3 dias únicos em 28 dias)"
    return 0, "padrão consistente (4+ dias únicos em 28 dias)"


# =========================
# Função principal
# =========================

def calcular_score_evasao(
    df_presencas: pd.DataFrame,
    coluna_aluno: str = "aluno_id",
    coluna_data: str = "data",
    cfg: Optional[ScoreConfig] = None,
) -> pd.DataFrame:
    """
    Entrada:
      df_presencas: DataFrame com colunas [aluno_id, data]
        - uma linha por presença (check-in) do aluno

    Saída:
      DataFrame por aluno com:
        - score (0–100)
        - classificação (baixo/moderado/alto)
        - motivos (2 principais)
        - métricas base (para auditoria)
    """
    cfg = cfg or ScoreConfig()

    df = _parse_data(df_presencas, coluna_data=coluna_data)

    if df.empty:
        return pd.DataFrame(columns=[
            coluna_aluno, "score", "classificacao", "motivos",
            "presencas_28d", "presencas_14d", "presencas_14d_prev",
            "dias_desde_ultima", "dias_unicos_28d"
        ])

    hoje = _today_from_data(df, coluna_data=coluna_data)

    ini_28d, fim_28d = _daterange_days(hoje, cfg.dias_janela_total)
    ini_14d, fim_14d = _daterange_days(hoje, cfg.dias_janela_recente)

    # 14 dias anteriores às 2 semanas recentes
    fim_14d_prev = ini_14d - timedelta(days=1)
    ini_14d_prev = fim_14d_prev - timedelta(days=cfg.dias_janela_recente - 1)

    # Filtra janelas
    df_28d = df[(df[coluna_data] >= ini_28d) & (df[coluna_data] <= fim_28d)].copy()
    df_14d = df[(df[coluna_data] >= ini_14d) & (df[coluna_data] <= fim_14d)].copy()
    df_14d_prev = df[(df[coluna_data] >= ini_14d_prev) & (df[coluna_data] <= fim_14d_prev)].copy()

    # Métricas por aluno
    pres_28d = df_28d.groupby(coluna_aluno).size().rename("presencas_28d")
    pres_14d = df_14d.groupby(coluna_aluno).size().rename("presencas_14d")
    pres_14d_prev = df_14d_prev.groupby(coluna_aluno).size().rename("presencas_14d_prev")

    # Dias únicos (irregularidade proxy)
    dias_unicos_28d = df_28d.groupby(coluna_aluno)[coluna_data].nunique().rename("dias_unicos_28d")

    # Última presença geral (não só 28d)
    ultima = df.groupby(coluna_aluno)[coluna_data].max().rename("ultima_presenca")
    dias_desde_ultima = (pd.Series([hoje]) - ultima).apply(lambda x: x.days).rename("dias_desde_ultima")

    # Junta tudo (inclui alunos que aparecem em qualquer momento do dataset)
    alunos = df[coluna_aluno].dropna().unique()
    out = pd.DataFrame({coluna_aluno: alunos}).set_index(coluna_aluno)

    out = out.join(pres_28d, how="left").join(pres_14d, how="left").join(pres_14d_prev, how="left")
    out = out.join(dias_unicos_28d, how="left").join(ultima, how="left").join(dias_desde_ultima, how="left")

    out = out.fillna({
        "presencas_28d": 0,
        "presencas_14d": 0,
        "presencas_14d_prev": 0,
        "dias_unicos_28d": 0,
    })

    # Calcula score por aluno
    scores = []
    motivos = []
    classificacoes = []

    for aluno_id, row in out.iterrows():
        c1, m1 = componente_baixo_engajamento(int(row["presencas_28d"]), cfg)
        c2, m2 = componente_queda_recente(int(row["presencas_14d"]), int(row["presencas_14d_prev"]), cfg)
        c3, m3 = componente_ausencia_consecutiva(int(row["dias_desde_ultima"]), cfg)
        c4, m4 = componente_irregularidade(int(row["dias_unicos_28d"]), cfg)

        score = c1 + c2 + c3 + c4
        score = max(0, min(100, int(round(score))))

        # Motivos principais (top 2 contribuições > 0)
        contribs = [(c1, m1), (c2, m2), (c3, m3), (c4, m4)]
        contribs_sorted = sorted(contribs, key=lambda x: x[0], reverse=True)
        top_motivos = [m for c, m in contribs_sorted if c > 0][:2]
        motivo_txt = "; ".join(top_motivos) if top_motivos else "sem sinais relevantes de risco"

        if score <= 30:
            cls = "baixo"
        elif score <= 60:
            cls = "moderado"
        else:
            cls = "alto"

        scores.append(score)
        motivos.append(motivo_txt)
        classificacoes.append(cls)

    out["score"] = scores
    out["classificacao"] = classificacoes
    out["motivos"] = motivos

    out = out.reset_index()[[
        coluna_aluno,
        "score",
        "classificacao",
        "motivos",
        "presencas_28d",
        "presencas_14d",
        "presencas_14d_prev",
        "dias_desde_ultima",
        "dias_unicos_28d",
    ]].sort_values(by=["score"], ascending=False)

    return out
