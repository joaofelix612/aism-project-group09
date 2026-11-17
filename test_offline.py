"""Teste sem Ollama: LLM simulado que reproduz a Fig. 2 (1.ª tentativa falha, 2.ª corrige)."""
import json
import pandas as pd
from pipeline import Logger, answer_question


class FakeLLM:
    def chat(self, system, user, json_mode=False):
        if "Query Planner" in system:
            if "idade média" in user:
                return json.dumps({"answerable": False, "plan": "", "reason": "Não existe coluna de idade."})
            return json.dumps({"answerable": True, "plan": "Receita = quantidade*preco; somar por regiao; maior.", "reason": ""})
        if "Code Writer" in system:
            if "Erro obtido" in user:
                return "```python\ndf['receita']=df['quantidade']*df['preco']\nresult=df.groupby('regiao')['receita'].sum().idxmax()\n```"
            return "```python\ndf['receita']=df['quantidade']*df['preco']\nresult=df.groupby('Regiao')['receita'].sum().idxmax()\n```"
        return json.dumps({"answer": "Resposta simulada: " + user.splitlines()[-1]})


if __name__ == "__main__":
    df = pd.read_csv("vendas.csv")
    lg = Logger("logs/teste.jsonl", verbose=False)
    r1 = answer_question("Qual a região com maior receita total?", df, FakeLLM(), lg)
    r2 = answer_question("Qual a idade média dos clientes?", df, FakeLLM(), lg)
    r3 = answer_question("x", df, type("L", (), {"chat": lambda s, sy, u, json_mode=False:
        json.dumps({"answerable": True, "plan": "p"}) if "Planner" in sy else
        ("```python\nimport os\nresult=1\n```" if "Code Writer" in sy else json.dumps({"answer": "falhou"}))})(), lg)
    print(r1["status"], r1["attempts"], r1["result"])
    print(r2["status"], r2["attempts"])
    print(r3["status"], r3["attempts"])
    assert (r1["status"], r1["attempts"]) == ("ok", 2)
    assert (r2["status"], r2["attempts"]) == ("unanswerable", 0)
    assert (r3["status"], r3["attempts"]) == ("failed", 3)
    print("TESTES OK")
