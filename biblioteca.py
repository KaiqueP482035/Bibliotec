import unicodedata
from datetime import date, datetime, timedelta

CATEGORIAS = {"aluno", "professor", "funcionario"}
STATUS_LIVRO = {"disponivel", "emprestado", "reservado", "baixado"}
CONDICOES = {"integro", "danificado", "perdido"}

PRAZO_DIAS = 7
MAX_LIVROS_SEMANA = 3
MAX_RENOVACOES = 2
MULTA_DIA = 2.00


class ErroBiblioteca(Exception):
    pass


class ErroValidacao(ErroBiblioteca):
    pass


class ErroNaoEncontrado(ErroBiblioteca):
    pass


class ErroRegra(ErroBiblioteca):
    pass


def normalizar(texto):
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto).strip())
        if not unicodedata.combining(c)
    )
    return sem_acento.lower()


def validar_texto(valor, campo):
    if not valor or not str(valor).strip():
        raise ErroValidacao(f"{campo} obrigatório.")
    return str(valor).strip()


def validar_categoria(categoria):
    cat = normalizar(validar_texto(categoria, "Categoria"))
    if cat not in CATEGORIAS:
        raise ErroValidacao("Categoria inválida (use: aluno, professor ou funcionario).")
    return cat


def validar_valor(valor):
    try:
        num = float(valor)
    except (TypeError, ValueError):
        raise ErroValidacao("Valor de mercado inválido.")
    if num <= 0:
        raise ErroValidacao("Valor de mercado deve ser maior que zero.")
    return round(num, 2)


class Biblioteca:
    def __init__(self):
        self.livros = {}
        self.usuarios = {}
        self.emprestimos = []
        self._prox_id = 1




    def cadastrar_livro(self, isbn, titulo, autor, categoria, valor_mercado):
        isbn = validar_texto(isbn, "ISBN").upper()
        if isbn in self.livros:
            raise ErroRegra("ISBN já cadastrado.")

        livro = {
            "isbn": isbn,
            "titulo": validar_texto(titulo, "Título"),
            "autor": validar_texto(autor, "Autor"),
            "categoria": validar_texto(categoria, "Categoria"),
            "valor_mercado": validar_valor(valor_mercado),
            "status": "disponivel",
            "fila_reservas": [],
        }
        self.livros[isbn] = livro
        return livro

    def obter_livro(self, isbn):
        isbn = validar_texto(isbn, "ISBN").upper()
        if isbn not in self.livros:
            raise ErroNaoEncontrado("Livro não encontrado.")
        return self.livros[isbn]

    def listar_livros(self):
        return sorted(self.livros.values(), key=lambda x: normalizar(x["titulo"]))

    def atualizar_livro(self, isbn, titulo=None, autor=None, categoria=None, valor_mercado=None):
        livro = self.obter_livro(isbn)
        if titulo:
            livro["titulo"] = validar_texto(titulo, "Título")
        if autor:
            livro["autor"] = validar_texto(autor, "Autor")
        if categoria:
            livro["categoria"] = validar_texto(categoria, "Categoria")
        if valor_mercado is not None:
            livro["valor_mercado"] = validar_valor(valor_mercado)
        return livro

    def excluir_livro(self, isbn, baixa=False):
        livro = self.obter_livro(isbn)
        if livro["status"] == "emprestado":
            raise ErroRegra("Livro emprestado não pode ser excluído/baixado.")
        livro["fila_reservas"].clear()
        if baixa:
            livro["status"] = "baixado"
            return livro
        return self.livros.pop(livro["isbn"])





    def cadastrar_usuario(self, matricula, nome, categoria):
        matricula = validar_texto(matricula, "Matrícula").upper()
        if matricula in self.usuarios:
            raise ErroRegra("Matrícula já cadastrada.")

        usuario = {
            "matricula": matricula,
            "nome": validar_texto(nome, "Nome"),
            "categoria": validar_categoria(categoria),
        }
        self.usuarios[matricula] = usuario
        return usuario

    def obter_usuario(self, matricula):
        matricula = validar_texto(matricula, "Matrícula").upper()
        if matricula not in self.usuarios:
            raise ErroNaoEncontrado("Usuário não cadastrado.")
        return self.usuarios[matricula]

    def listar_usuarios(self):
        return sorted(self.usuarios.values(), key=lambda x: normalizar(x["nome"]))

    def atualizar_usuario(self, matricula, nome=None, categoria=None):
        usuario = self.obter_usuario(matricula)
        if nome:
            usuario["nome"] = validar_texto(nome, "Nome")
        if categoria:
            usuario["categoria"] = validar_categoria(categoria)
        return usuario

    def excluir_usuario(self, matricula):
        usuario = self.obter_usuario(matricula)
        mat = usuario["matricula"]
        if self._ativos_usuario(mat):
            raise ErroRegra("Usuário possui empréstimos pendentes.")

        for livro in self.livros.values():
            livro["fila_reservas"] = [r for r in livro["fila_reservas"] if r["matricula"] != mat]
            if livro["status"] == "reservado" and not livro["fila_reservas"]:
                livro["status"] = "disponivel"

        return self.usuarios.pop(mat)





    def buscar_livros(self, titulo=None, autor=None, isbn=None, categoria=None, status=None):
        if status:
            status = normalizar(status)
            if status not in STATUS_LIVRO:
                raise ErroValidacao("Status inválido (disponivel, emprestado, reservado, baixado).")

        res = []
        for l in self.listar_livros():
            if titulo and normalizar(titulo) not in normalizar(l["titulo"]):
                continue
            if autor and normalizar(autor) not in normalizar(l["autor"]):
                continue
            if isbn and normalizar(isbn) not in normalizar(l["isbn"]):
                continue
            if categoria and normalizar(categoria) not in normalizar(l["categoria"]):
                continue
            if status and l["status"] != status:
                continue
            res.append(l)
        return res

    def buscar_usuarios(self, nome=None, matricula=None, categoria=None):
        cat = validar_categoria(categoria) if categoria else None
        res = []
        for u in self.listar_usuarios():
            if nome and normalizar(nome) not in normalizar(u["nome"]):
                continue
            if matricula and normalizar(matricula) not in normalizar(u["matricula"]):
                continue
            if cat and u["categoria"] != cat:
                continue
            res.append(u)
        return res

    def listar_emprestimos_ativos(self):
        return [e for e in self.emprestimos if e["status"] == "ativo"]

    def listar_atrasados(self, data_ref=None):
        hoje = data_ref or date.today()
        atrasados = []
        for e in self.listar_emprestimos_ativos():
            dias = (hoje - e["data_prevista"]).days
            if dias > 0:
                atrasados.append({
                    "emprestimo": e,
                    "dias": dias,
                    "multa": round(dias * MULTA_DIA, 2),
                })
        return atrasados





    def _ativos_usuario(self, matricula):
        return [e for e in self.emprestimos if e["matricula"] == matricula and e["status"] == "ativo"]

    def _emprestimos_semana(self, matricula, hoje):
        inicio = hoje - timedelta(days=PRAZO_DIAS - 1)
        return sum(1 for e in self.emprestimos if e["matricula"] == matricula and inicio <= e["data_emprestimo"] <= hoje)

    def obter_emprestimo(self, id_emp):
        try:
            id_emp = int(id_emp)
        except (TypeError, ValueError):
            raise ErroValidacao("ID inválido.")
        for e in self.emprestimos:
            if e["id"] == id_emp:
                return e
        raise ErroNaoEncontrado("Empréstimo não encontrado.")

    def emprestar(self, matricula, isbns, data_atual=None):
        hoje = data_atual or date.today()
        usuario = self.obter_usuario(matricula)
        mat = usuario["matricula"]

        if not isbns or len(isbns) > MAX_LIVROS_SEMANA:
            raise ErroRegra(f"Alugue entre 1 e {MAX_LIVROS_SEMANA} livros.")

        codigos = [validar_texto(c, "ISBN").upper() for c in isbns]
        if len(set(codigos)) != len(codigos):
            raise ErroValidacao("ISBNs repetidos.")

        if self._ativos_usuario(mat):
            raise ErroRegra("Devolva os livros pendentes antes de alugar novos.")

        usados = self._emprestimos_semana(mat, hoje)
        if usados + len(codigos) > MAX_LIVROS_SEMANA:
            raise ErroRegra(f"Limite semanal excedido ({usados}/{MAX_LIVROS_SEMANA} usados).")

        livros_ok = []
        for codigo in codigos:
            livro = self.obter_livro(codigo)
            if livro["status"] == "baixado":
                raise ErroRegra(f"Livro {codigo} baixado.")
            if livro["status"] == "emprestado":
                raise ErroRegra(f"Livro {codigo} já emprestado.")
            if livro["status"] == "reservado":
                if livro["fila_reservas"][0]["matricula"] != mat:
                    raise ErroRegra(f"Livro {codigo} reservado para {livro['fila_reservas'][0]['matricula']}.")
            livros_ok.append(livro)

        criados = []
        prazo = hoje + timedelta(days=PRAZO_DIAS)
        for livro in livros_ok:
            if livro["status"] == "reservado":
                livro["fila_reservas"].pop(0)
            livro["status"] = "emprestado"
            emp = {
                "id": self._prox_id,
                "matricula": mat,
                "isbn": livro["isbn"],
                "data_emprestimo": hoje,
                "data_prevista": prazo,
                "data_devolucao": None,
                "renovacoes": 0,
                "status": "ativo",
                "multa": 0.0,
                "indenizacao": 0.0,
            }
            self._prox_id += 1
            self.emprestimos.append(emp)
            criados.append(emp)

        return criados

    def renovar(self, id_emp, data_atual=None):
        hoje = data_atual or date.today()
        emp = self.obter_emprestimo(id_emp)

        if emp["status"] != "ativo":
            raise ErroRegra("Empréstimo encerrado.")
        if hoje > emp["data_prevista"]:
            raise ErroRegra("Empréstimo atrasado não pode ser renovado.")
        if emp["renovacoes"] >= MAX_RENOVACOES:
            raise ErroRegra(f"Limite de {MAX_RENOVACOES} renovações atingido.")

        livro = self.obter_livro(emp["isbn"])
        if livro["fila_reservas"]:
            raise ErroRegra("Livro possui fila de reserva.")

        emp["renovacoes"] += 1
        emp["data_prevista"] += timedelta(days=PRAZO_DIAS)
        return emp

    def devolver(self, id_emp, condicao="integro", data_dev=None):
        emp = self.obter_emprestimo(id_emp)
        if emp["status"] != "ativo":
            raise ErroRegra("Empréstimo já encerrado.")

        cond = normalizar(condicao)
        if cond not in CONDICOES:
            raise ErroValidacao("Condição inválida (integro, danificado ou perdido).")

        dt = data_dev or date.today()
        if dt < emp["data_emprestimo"]:
            raise ErroValidacao("Data de devolução anterior ao empréstimo.")

        livro = self.obter_livro(emp["isbn"])
        dias_atraso = max(0, (dt - emp["data_prevista"]).days)
        multa = round(dias_atraso * MULTA_DIA, 2)
        indenizacao = 0.0
        proximo = None

        if cond in ("danificado", "perdido"):
            indenizacao = livro["valor_mercado"]
            emp["status"] = cond
            livro["status"] = "baixado"
            livro["fila_reservas"].clear()
        else:
            emp["status"] = "devolvido"
            if livro["fila_reservas"]:
                livro["status"] = "reservado"
                proximo = livro["fila_reservas"][0]["matricula"]
            else:
                livro["status"] = "disponivel"

        emp["data_devolucao"] = dt
        emp["multa"] = multa
        emp["indenizacao"] = indenizacao

        return {
            "dias_atraso": dias_atraso,
            "multa": multa,
            "indenizacao": indenizacao,
            "total": round(multa + indenizacao, 2),
            "proximo_fila": proximo,
        }

    def reservar(self, matricula, isbn):
        usuario = self.obter_usuario(matricula)
        livro = self.obter_livro(isbn)
        mat = usuario["matricula"]

        if livro["status"] == "disponivel":
            raise ErroRegra("Livro disponível, faça empréstimo direto.")
        if livro["status"] == "baixado":
            raise ErroRegra("Livro baixado.")

        for e in self.listar_emprestimos_ativos():
            if e["isbn"] == livro["isbn"] and e["matricula"] == mat:
                raise ErroRegra("Usuário já está com este livro.")

        if any(r["matricula"] == mat for r in livro["fila_reservas"]):
            raise ErroRegra("Usuário já está na fila deste livro.")

        item = {"matricula": mat, "data": datetime.now()}
        livro["fila_reservas"].append(item)
        livro["fila_reservas"].sort(key=lambda r: r["data"])
        return len(livro["fila_reservas"])

    def cancelar_reserva(self, matricula, isbn):
        mat = self.obter_usuario(matricula)["matricula"]
        livro = self.obter_livro(isbn)
        antes = len(livro["fila_reservas"])
        livro["fila_reservas"] = [r for r in livro["fila_reservas"] if r["matricula"] != mat]
        if len(livro["fila_reservas"]) == antes:
            raise ErroNaoEncontrado("Reserva não encontrada.")
        if livro["status"] == "reservado" and not livro["fila_reservas"]:
            livro["status"] = "disponivel"
