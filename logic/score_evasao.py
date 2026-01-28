from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

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
        return cfg.peso_baixo_engajamento, "engajamento muito baixo (0–1 presença/28d)"
    if presencas_28d <= 3:
        return round(cfg.peso_baixo_engajamento * 0.7), "engajamento baixo (2–3 presenças/28d)"
    if presencas_28d <= 5:
        return round(cfg.peso_baixo_engajamento * 0.4), "engajamento moderado (4–5 presenças/28d)"
    return 0, "engajamento bom (6+ presenças/28d)"


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
        return 0, "sem base para queda (14d anteriores = 0)"

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
        return 0, "ausência curta (<=3 dias)"
    if dias_desde_ultima <= 7:
        return round(cfg.peso_ausencia_consecutiva * 0.4), "ausência relevante (4–7 dias)"
    if dias_desde_ultima <= 14:
        return round(cfg.peso_ausencia_consecutiva * 0.7), "ausência alta (8–14 dias)"
    return cfg.peso_ausencia_consecutiva, "ausência crítica (15+ dias)"


def componente_irregularidade(dias_com_presenca_28d: int, cfg: ScoreConfig) -> Tuple[int, str]:
    """
    Irregularidade (proxy simples): quantos 'dias únicos' a pessoa apareceu na janela.
    Quem aparece em poucos dias únicos tende a ter rotina fraca.
    - 1 dia: 100% do peso
    - 2 dias: 70%
    - 3 dias: 40%
    - 4+ dias: 0
    """
    if dias_com_presenca_28d <= 1:
        return cfg.peso_irregularidade, "padrão muito irregular (1 dia único/28_
