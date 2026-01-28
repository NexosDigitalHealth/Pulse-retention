import streamlit as st
import pandas as pd

from logic.score_evasao import calcular_score_evasao


# =========================
# Configuração da página
# =========================
st.set_page_config(page_title="PULSE", page_icon="📈", layout="centered")

st.title("📈 PULSE — Risco de Evasão (v1)")
st.caption("Acompanhamento de frequência e sinais precoces de evasão para academias (foco em gestão e engajamento).")

with st.expander("⚠️ Aviso de uso", expanded=False):
    st.write(
        "A PULSE é uma ferramenta de **apoio à gestão e engajamento**. "
        "Não fornece diagnóstico, não prescreve exercícios e não substitui acompanhamento profissional."
    )

st.divider()

# =========================
# Upload do CSV
# =========================
st.subheader("1) Enviar arquivo de presenças (CSV)")

st.write("Formato esperado:")
st.code("aluno_id,data\n001,2025-01-02\n001,2025-01-05\n002,2025-01-03", language="csv")

arquivo = st.file_uploader("Selecione o CSV", type=["csv"])

usar_exemplo = st.checkbox("Usar arquivo de exemplo (data/exemplo_presencas.csv) — apenas para demonstração", value=False)

df = None
if arquivo is not None:
    try:
        df = pd.read_csv(arquivo)
    except Exception as e:
        st.error(f"Não foi possível ler o CSV: {e}")

elif usar_exemplo:
    # Para rodar local depois, esse caminho funciona.
    # No GitHub (sem executar), fica como referência.
    try:
        df = pd.read_csv("data/exemplo_presencas.csv")
    except Exception:
        st.warning("Exemplo não disponível no ambiente atual. Use upload de CSV quando rodar localmente.")

if df is None:
    st.info("Envie um CSV para calcular o score.")
    st.stop()

st.subheader("2) Pré-visualização dos dados")
st.dataframe(df.head(20), use_container_width=True)

st.divider()

# =========================
# Configurações do usuário
# =========================
st.subheader("3) Configurações")

col_aluno = st.text_input("Nome da coluna do aluno", value="aluno_id")
col_data = st.text_input("Nome da coluna de data", value="data")

st.caption("Dica: datas devem estar em formato como 2025-01-02 (YYYY-MM-DD).")

if st.button("Calcular score", type="primary"):
    try:
        resultado = calcular_score_evasao(df, coluna_aluno=col_aluno, coluna_data=col_data)
    except Exception as e:
        st.error(f"Erro ao calcular o score: {e}")
        st.stop()

    st.success("Score calculado com sucesso!")
    st.subheader("4) Resultado")

    # Filtros
    st.markdown("### Filtros")
    filtro = st.selectbox("Mostrar", ["Todos", "Apenas alto risco", "Apenas risco moderado", "Apenas baixo risco"])

    if filtro == "Apenas alto risco":
        view = resultado[resultado["classificacao"] == "alto"]
    elif filtro == "Apenas risco moderado":
        view = resultado[resultado["classificacao"] == "moderado"]
    elif filtro == "Apenas baixo risco":
        view = resultado[resultado["classificacao"] == "baixo"]
    else:
        view = resultado

    st.dataframe(view, use_container_width=True)

    # Download
    csv_out = resultado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Baixar resultado (CSV)",
        data=csv_out,
        file_name="pulse_resultado_score.csv",
        mime="text/csv",
    )

    st.divider()

    st.subheader("5) Como usar na prática (ação rápida)")
    st.markdown(
        "- **Alto risco:** contato ativo + convite para retorno + ajuste de rotina/horário\n"
        "- **Moderado:** reforço de engajamento + acompanhamento semanal\n"
        "- **Baixo:** manter consistência + reforçar metas e progresso"
    )
