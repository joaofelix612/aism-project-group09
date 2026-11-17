"""Interface web. Correr com:  streamlit run app.py"""
import os

import pandas as pd
import streamlit as st

from demo_llm import DemoLLM
from llm import DEFAULT_MODEL, LLM
from pipeline import Logger, answer_question, schema_text

st.set_page_config(page_title="Data Analyst · Self-Correcting Loop", page_icon="🧠", layout="wide")

AGENTS = {  # remetente -> (avatar, cor)
    "Utilizador": "🙋", "Planner": "🧭", "Code Writer": "✍️", "Executor": "⚙️", "Explainer": "💬",
}
EXAMPLES = [
    "Qual a região com maior receita total? (receita = quantidade * preco)",
    "Qual o produto com maior quantidade total vendida?",
    "Quantas vendas existem por região?",
    "Qual a idade média dos clientes?",
]


def render(container, sender, receiver, kind, content):
    """Desenha uma mensagem entre agentes."""
    with container.chat_message(sender, avatar=AGENTS.get(sender, "🤖")):
        st.caption(f"**{sender}** → {receiver} · _{kind}_")
        if kind == "pergunta":
            st.text("Esquema enviado ao Planner (só nomes e tipos):\n" + content["schema"])
        elif kind == "plano":
            if content["answerable"]:
                st.info("📋 " + content["plan"])
            else:
                st.warning("🚫 **Não respondível** — " + content["reason"])
        elif kind.startswith("código"):
            st.code(content, language="python")
        elif kind == "erro":
            st.error(content)
        elif kind == "resultado":
            st.success("✅ Resultado do Executor")
            st.code(content)
        else:  # resposta
            st.markdown(content)


class StLogger(Logger):
    """Logger que, além de gravar o JSONL, desenha cada mensagem na página em tempo real."""

    def __init__(self, container):
        super().__init__("logs/mensagens.jsonl", verbose=False)
        self.container, self.events = container, []

    def msg(self, sender, receiver, kind, content):
        super().msg(sender, receiver, kind, content)
        self.events.append((sender, receiver, kind, content))
        render(self.container, sender, receiver, kind, content)


@st.cache_data
def load_default():
    if not os.path.exists("vendas.csv"):
        import make_data  # noqa: F401  (gera vendas.csv)
    return pd.read_csv("vendas.csv")


# ---------------------------------------------------------------- barra lateral
with st.sidebar:
    st.header("⚙️ Configuração")
    demo = st.checkbox("Modo demonstração (simulado, sem Ollama)", value=False,
                       help="Usa um modelo simulado que reproduz a Fig. 2: falha na 1.ª tentativa e autocorrige-se.")
    model = st.text_input("Modelo Ollama", DEFAULT_MODEL, disabled=demo)
    use_cache = st.checkbox("Cache das respostas do modelo", value=True, disabled=demo)
    up = st.file_uploader("CSV (opcional)", type="csv")
    st.markdown("---")
    st.caption("Planner → Code Writer ⇄ Executor (máx. 3 tentativas) → Explainer")

df = pd.read_csv(up) if up else load_default()

# ---------------------------------------------------------------- cabeçalho
st.title("🧠 The Data Analyst with a Self-Correcting Loop")
st.caption("Faz uma pergunta em linguagem natural. Vê os agentes a planear, escrever código, falhar e autocorrigir-se.")
if demo:
    st.warning("🎭 **Modo demonstração:** as respostas dos agentes são SIMULADAS (nenhum modelo está a correr).")

c1, c2 = st.columns([2, 1])
with c1:
    with st.expander(f"📄 Dados ({len(df)} linhas)", expanded=False):
        st.dataframe(df.head(20), width="stretch")
with c2:
    with st.expander("🔎 Esquema que o Planner vê", expanded=False):
        st.text(schema_text(df))

st.write("**Exemplos:**")
cols = st.columns(len(EXAMPLES))
for i, ex in enumerate(EXAMPLES):
    if cols[i].button(ex, key=f"ex{i}", width="stretch"):
        st.session_state["question"] = ex

question = st.text_input("Pergunta", key="question", placeholder="Ex.: Qual a região com maior receita total?")
go = st.button("🚀 Perguntar", type="primary", disabled=not question.strip())

# ---------------------------------------------------------------- execução
if "history" not in st.session_state:
    st.session_state.history = []

if go:
    st.subheader("🗨️ Conversa entre agentes")
    log_box = st.container()
    logger = StLogger(log_box)
    llm = DemoLLM() if demo else LLM(model, use_cache=use_cache)
    try:
        with st.spinner("Os agentes estão a trabalhar…"):
            r = answer_question(question.strip(), df, llm, logger)
    except Exception as e:  # ex.: Ollama desligado
        st.error(f"❌ {e}")
        st.stop()

    st.subheader("📣 Resposta final")
    badge = {"ok": "✅ Respondido", "unanswerable": "🚫 Recusado (dados insuficientes)", "failed": "❌ Falhou após 3 tentativas"}[r["status"]]
    m1, m2 = st.columns(2)
    m1.metric("Estado", badge)
    m2.metric("Tentativas do Code Writer", r["attempts"])
    if r["status"] == "ok" and r["attempts"] > 1:
        st.success(f"🔁 Autocorreção em ação: o código só funcionou à tentativa {r['attempts']}, depois de ver o erro.")
    (st.success if r["status"] == "ok" else st.warning)(r["answer"])
    st.session_state.history.append({"q": question.strip(), "r": r, "events": logger.events})

# ---------------------------------------------------------------- histórico
past = st.session_state.history[:-1] if go else st.session_state.history
if past:
    st.markdown("---")
    st.subheader("🕘 Perguntas anteriores")
    for h in reversed(past):
        with st.expander(f"{h['q']}  —  {h['r']['status']} · {h['r']['attempts']} tentativa(s)"):
            for ev in h["events"]:
                render(st.container(), *ev)
