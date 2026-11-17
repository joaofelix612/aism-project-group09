"""Gera vendas.csv (dados sintéticos, reprodutíveis). Nota: não tem coluna de idade/clientes."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 300
df = pd.DataFrame({
    "regiao": rng.choice(["Norte", "Centro", "Sul", "Lisboa"], n),
    "produto": rng.choice(["Teclado", "Rato", "Monitor", "Portátil"], n),
    "quantidade": rng.integers(1, 10, n),
    "preco": rng.choice([25.0, 15.0, 180.0, 650.0], n),
    "data": pd.to_datetime("2023-01-01") + pd.to_timedelta(rng.integers(0, 730, n), unit="D"),
})
df["data"] = df["data"].dt.strftime("%Y-%m-%d")
df.to_csv("vendas.csv", index=False)
print(df.head(), f"\n{len(df)} linhas -> vendas.csv")
