# PULSE

**PULSE** é um aplicativo B2B leve para ajudar academias a acompanhar a frequência dos alunos e identificar **sinais precoces de risco de evasão**.

O foco é **engajamento e retenção**, oferecendo indicadores simples e explicáveis para que gestores e professores ajam antes que o aluno abandone a rotina.

---

## 🎯 Objetivo

A evasão de alunos é um dos principais desafios das academias.  
A PULSE transforma **dados de presença** em **insights acionáveis**.

A PULSE **não prescreve treino**, **não faz diagnóstico** e **não substitui** acompanhamento profissional.

---

## 🚀 Funcionalidades

- Acompanhamento de presença semanal  
- Detecção de queda de frequência  
- Score de risco de evasão (0–100)  
- Alertas visuais para alunos em risco  
- Entrada simples por arquivo CSV  
- Lógica baseada em regras (explicável)

---

## 📊 Como funciona

A PULSE analisa padrões de presença com regras transparentes:

- Média de presenças por semana  
- Queda recente na frequência  
- Ausências consecutivas  
- Irregularidade do padrão de presença  

Esses fatores são combinados em um **Score de Risco de Evasão**, permitindo priorizar ações de retenção.

---

## 🧠 Score de Risco de Evasão

| Faixa | Interpretação |
|------:|---------------|
| 0–30  | Baixo risco   |
| 31–60 | Risco moderado|
| 61–100| Alto risco    |

O score é **interpretável** e voltado à **gestão de engajamento**, não a “previsão médica”.

---

## 📂 Entrada de dados

No momento, a PULSE aceita um CSV no formato:

```csv
aluno_id,data
001,2025-01-02
001,2025-01-05
002,2025-01-03
