"""Os três agentes baseados em LLM. Cada um só vê o que o Quadro 1 permite."""
import json
import re

PLANNER_SYSTEM = """És o Query Planner de um analista de dados.
Recebes uma pergunta e o esquema de um CSV (nomes e tipos das colunas).
Decide se a pergunta PODE ser respondida usando APENAS as colunas existentes.
- Se faltar uma coluna necessária, NÃO uses uma coluna parecida nem aproximada: é não respondível.
- Se for respondível, descreve em palavras simples o que calcular (colunas, filtros, agregações).
- No plano, escreve SEMPRE os nomes das colunas exatamente como aparecem no esquema, entre aspas
  (mesmas letras, sem acentos nem traduções; ex.: "regiao", não região). O Code Writer não vê o esquema.
- Totais = somar (não o máximo de linhas individuais). Exemplo de plano bom:
  'Criar "receita" = "quantidade" * "preco"; agrupar por "regiao"; somar "receita"; escolher a regiao com a maior soma.'
Responde só com JSON: {"answerable": true|false, "plan": "...", "reason": "..."}
('plan' preenchido se respondível; 'reason' preenchido se não respondível.)"""

WRITER_SYSTEM = """És o Code Writer. Traduzes um plano em código Python (pandas).
Regras:
- O DataFrame já existe na variável `df`; `pd` e `np` já estão importados. NÃO uses import nem ficheiros.
- Usa exatamente os nomes de colunas do plano, sem traduzir nem acentuar. Se o erro listar as colunas disponíveis, usa esses nomes.
- Guarda a resposta final na variável `result`.
- Responde apenas com um bloco ```python ... ```, sem explicações.
Se receberes código anterior e uma mensagem de erro, corrige o erro e devolve o código completo."""

EXPLAINER_SYSTEM = """És o Explainer. Respondes ao utilizador em português europeu, em linguagem simples e curta.
Recebes a pergunta e o resultado (ou a falha). Nunca vês o código.
- Usa APENAS o resultado fornecido; não inventes valores.
- Acrescenta uma breve ressalva: o valor depende de como a pergunta foi interpretada.
- Se a pergunta não é respondível ou o cálculo falhou, diz-o com honestidade e explica o motivo.
Responde só com JSON: {"answer": "..."}"""


def parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return {}


def extract_code(raw: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", raw, re.S)
    return (m.group(1) if m else raw).strip()


class Planner:
    def __init__(self, llm):
        self.llm = llm

    def run(self, question: str, schema: str) -> dict:
        raw = self.llm.chat(PLANNER_SYSTEM, f"Esquema:\n{schema}\n\nPergunta: {question}", json_mode=True)
        d = parse_json(raw)
        ans = d.get("answerable")
        if isinstance(ans, str):
            ans = ans.strip().lower() in ("true", "sim", "yes")
        plan = str(d.get("plan") or "").strip()
        # Plano vazio = recusa (falha segura, nunca inventar)
        return {"answerable": bool(ans) and bool(plan), "plan": plan,
                "reason": "" if (bool(ans) and bool(plan)) else str(d.get("reason") or "O planner não conseguiu produzir um plano.")}


class CodeWriter:
    def __init__(self, llm):
        self.llm = llm

    def run(self, plan: str, history=None) -> str:
        """history: lista de (código, erro) das tentativas falhadas. Inclui todas para
        o prompt mudar a cada tentativa e o modelo não repetir o mesmo código."""
        user = f"Plano: {plan}"
        if history:
            user += "\n\nTentativas anteriores que FALHARAM (não repitas o mesmo código):"
            for i, (c, e) in enumerate(history, 1):
                user += f"\n\n--- Tentativa {i} ---\n```python\n{c}\n```\nErro obtido:\n{e}"
            user += f"\n\nEscreve a tentativa {len(history) + 1}: corrigida e DIFERENTE das anteriores."
        return extract_code(self.llm.chat(WRITER_SYSTEM, user))


class Explainer:
    def __init__(self, llm):
        self.llm = llm

    def run(self, question: str, status: str, detail: str) -> str:
        user = f"Pergunta: {question}\nEstado: {status}\nResultado/detalhe:\n{detail}"
        raw = self.llm.chat(EXPLAINER_SYSTEM, user, json_mode=True)
        d = parse_json(raw)
        return str(d.get("answer") or raw).strip()
