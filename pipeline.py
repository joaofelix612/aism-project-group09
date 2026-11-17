"""Orquestração: Planner -> Code Writer <-> Executor (máx. 3 tentativas) -> Explainer."""
import json
import time

from agents import CodeWriter, Explainer, Planner
from executor import execute

MAX_ATTEMPTS = 3


def schema_text(df) -> str:
    """Só nomes e tipos das colunas — nunca o ficheiro inteiro."""
    return "\n".join(f"- {c}: {t}" for c, t in df.dtypes.astype(str).items())


class Logger:
    def __init__(self, path="logs/mensagens.jsonl", verbose=True):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path, self.verbose = path, verbose

    def msg(self, sender, receiver, kind, content):
        rec = {"ts": time.strftime("%H:%M:%S"), "from": sender, "to": receiver,
               "type": kind, "content": content}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if self.verbose:
            text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            print(f"[{rec['ts']}] {sender} -> {receiver} ({kind})\n    " + text.replace("\n", "\n    "))


def answer_question(question, df, llm, logger, max_attempts=MAX_ATTEMPTS) -> dict:
    planner, writer, explainer = Planner(llm), CodeWriter(llm), Explainer(llm)
    logger.msg("Utilizador", "Planner", "pergunta", {"question": question, "schema": schema_text(df)})

    plan = planner.run(question, schema_text(df))
    logger.msg("Planner", "Code Writer" if plan["answerable"] else "Explainer", "plano", plan)

    if not plan["answerable"]:  # barreira 1: recusa
        final = explainer.run(question, "NÃO RESPONDÍVEL", plan["reason"])
        logger.msg("Explainer", "Utilizador", "resposta", final)
        return {"status": "unanswerable", "attempts": 0, "result": None, "code": None, "answer": final}

    code, history = None, []
    status, out, attempts = "error", "", 0
    for attempts in range(1, max_attempts + 1):  # barreira 2: máx. 3 tentativas
        code = writer.run(plan["plan"], history)
        logger.msg("Code Writer", "Executor", f"código (tentativa {attempts})", code)
        status, out = execute(code, df)
        logger.msg("Executor", "Code Writer" if status == "error" else "Explainer",
                   "resultado" if status == "ok" else "erro", out)
        if status == "ok":
            break
        history.append((code, out))

    if status == "ok":
        final = explainer.run(question, "OK", out)
    else:
        final = explainer.run(question, f"FALHOU após {attempts} tentativas", f"Último erro: {out}")
    logger.msg("Explainer", "Utilizador", "resposta", final)
    return {"status": "ok" if status == "ok" else "failed", "attempts": attempts,
            "result": out if status == "ok" else None, "code": code, "answer": final}
