"""Executor em Python puro (NÃO é um modelo).

Corre o código gerado num processo separado, com:
  - limite de tempo (o processo é terminado se exceder);
  - builtins restritos (sem open, import, exec, eval, ...);
  - verificação estática (AST) que bloqueia imports, atributos "dunder" e
    funções de leitura/escrita de ficheiros do pandas.
Nota: é uma proteção "boa o suficiente" para o projeto, não uma sandbox de
segurança de nível produção.
"""
import ast
import builtins
import multiprocessing as mp

TIMEOUT_S = 10
MAX_OUTPUT = 4000

SAFE_BUILTINS = [
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float", "int",
    "isinstance", "len", "list", "map", "max", "min", "range", "reversed",
    "round", "set", "sorted", "str", "sum", "tuple", "zip", "print",
    "True", "False", "None", "Exception", "KeyError", "ValueError", "TypeError",
]
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "input",
                   "globals", "locals", "vars", "getattr", "setattr", "delattr"}
FORBIDDEN_ATTRS = {
    "read_csv", "read_excel", "read_json", "read_sql", "read_pickle",
    "read_parquet", "read_html", "read_table", "read_fwf", "read_clipboard",
    "to_csv", "to_excel", "to_json", "to_pickle", "to_parquet", "to_sql",
    "to_html", "to_clipboard", "to_hdf", "to_feather", "to_latex",
    "load", "save", "loadtxt", "genfromtxt", "fromfile", "tofile",
}


def check_code(code: str):
    """Devolve mensagem de erro (str) se o código for inseguro/inválido, senão None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e.msg} (linha {e.lineno})"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "SecurityError: imports não são permitidos (pd, np e df já estão disponíveis)."
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return f"SecurityError: o nome '{node.id}' não é permitido."
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in FORBIDDEN_ATTRS:
                return f"SecurityError: o atributo '{node.attr}' não é permitido."
    return None


def format_result(value) -> str:
    import pandas as pd
    if isinstance(value, pd.DataFrame):
        text = value.to_string(max_rows=50)
    elif isinstance(value, pd.Series):
        text = value.to_string(max_rows=50)
    else:
        text = str(value)
    return text[:MAX_OUTPUT]


def _worker(code, df, queue):
    try:
        import numpy as np
        import pandas as pd
        safe = {n: getattr(builtins, n) for n in SAFE_BUILTINS}
        env = {"__builtins__": safe, "df": df.copy(), "pd": pd, "np": np}
        exec(compile(code, "<codigo_gerado>", "exec"), env)
        if "result" not in env:
            queue.put(("error", "O código não definiu a variável 'result' com a resposta final."))
            return
        queue.put(("ok", format_result(env["result"])))
    except BaseException as e:  # inclui KeyError, etc. — a mensagem volta ao Code Writer
        msg = f"{type(e).__name__}: {e}"
        if isinstance(e, (KeyError, AttributeError)):
            msg += f"\n(Colunas disponíveis em df: {list(df.columns)})"  # pista, como na Fig. 2
        queue.put(("error", msg))


def execute(code: str, df, timeout: int = TIMEOUT_S):
    """Devolve ("ok", resultado) ou ("error", mensagem)."""
    problem = check_code(code)
    if problem:
        return "error", problem
    queue = mp.Queue()
    proc = mp.Process(target=_worker, args=(code, df, queue))
    proc.start()
    try:
        status, out = queue.get(timeout=timeout)
    except Exception:
        status, out = "error", f"TimeoutError: a execução excedeu {timeout}s."
    proc.join(1)
    if proc.is_alive():
        proc.terminate()
    return status, out
