"""LLM SIMULADO para demonstração (sem Ollama). Reproduz o exemplo da Fig. 2 do enunciado:
a 1.ª tentativa falha com um nome de coluna errado e a 2.ª corrige-se com o erro.
Só conhece 2 tipos de pergunta: receita por região e algo sobre idade (que recusa)."""
import json
import time


class DemoLLM:
    def __init__(self, delay=1.0):
        self.delay = delay

    def chat(self, system, user, json_mode=False):
        time.sleep(self.delay)
        question = user.split("Pergunta:")[-1].lower() if "Pergunta:" in user else user.lower()
        if "Query Planner" in system:
            if "receita" in question and ("regi" in question):
                return json.dumps({"answerable": True, "reason": "", "plan":
                    'Criar "receita" = "quantidade" * "preco"; agrupar por "regiao"; somar "receita"; escolher o maior.'})
            reason = ("Não existe nenhuma coluna de idade/clientes no CSV." if "idade" in question
                      else "O modo demonstração só conhece a pergunta da receita por região.")
            return json.dumps({"answerable": False, "plan": "", "reason": reason})
        if "Code Writer" in system:
            col = "regiao" if "Erro obtido" in user else "Regiao"   # 1.ª tentativa falha de propósito
            return ("```python\ndf['receita'] = df['quantidade'] * df['preco']\n"
                    f"result = df.groupby('{col}')['receita'].sum().sort_values(ascending=False)\n```")
        return json.dumps({"answer": "(resposta simulada) " + user.split("Resultado/detalhe:")[-1].strip().replace("\n", " | ")
                           + " — o valor depende de como a pergunta foi interpretada."})
