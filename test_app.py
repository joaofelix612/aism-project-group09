"""Testa a interface sem browser (Streamlit AppTest) em modo demonstração."""
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=60).run()
assert not at.exception, at.exception
at.sidebar.checkbox[0].check().run()                     # modo demonstração
at.text_input(key="question").set_value("Qual a região com maior receita total?").run()
at.button[-1].click().run()                              # "Perguntar"
assert not at.exception, at.exception
text = " ".join(e.value for e in at.error) + " ".join(e.value for e in at.success)
print("erros mostrados:", [e.value[:40] for e in at.error])
assert any("KeyError" in e.value for e in at.error), "devia mostrar o erro da 1.ª tentativa"
assert any("autocorreção" in s.value.lower() for s in at.success), "devia mostrar autocorreção"
# caso de recusa
at.text_input(key="question").set_value("Qual a idade média dos clientes?").run()
at.button[-1].click().run()
assert not at.exception, at.exception
assert any("Não respondível" in w.value for w in at.warning)
print("APP OK")
