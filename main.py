from datetime import datetime

from biblioteca import Biblioteca, ErroBiblioteca, ErroValidacao


def fmt_data(dt):
    return dt.strftime("%d/%m/%Y") if dt else "-"


def fmt_moeda(v):
    return f"R$ {v:.2f}".replace(".", ",")


def ler_float(msg, obrigatorio=True):
    while True:
        txt = input(msg).strip().replace(",", ".")
        if not txt and not obrigatorio:
            return None
        try:
            return float(txt)
        except ValueError:
            print("Valor inválido.")


def ler_int(msg):
    while True:
        try:
            return int(input(msg).strip())
        except ValueError:
            print("Número inválido.")


def ler_data(msg):
    while True:
        txt = input(msg).strip()
        if not txt:
            return None
        try:
            return datetime.strptime(txt, "%d/%m/%Y").date()
        except ValueError:
            print("Data inválida (use DD/MM/AAAA).")


def mostrar_livros(livros):
    if not livros:
        print("Nenhum livro encontrado.")
        return
    for l in livros:
        print(
            f"{l['isbn']} | {l['titulo']} | {l['autor']} | {l['categoria']} | "
            f"{fmt_moeda(l['valor_mercado'])} | {l['status']} | fila: {len(l['fila_reservas'])}"
        )


def mostrar_usuarios(usuarios):
    if not usuarios:
        print("Nenhum usuário encontrado.")
        return
    for u in usuarios:
        print(f"{u['matricula']} | {u['nome']} | {u['categoria']}")


def mostrar_emprestimos(emps):
    if not emps:
        print("Nenhum empréstimo encontrado.")
        return
    for e in emps:
        taxas = e["multa"] + e["indenizacao"]
        extra = f" | pagar: {fmt_moeda(taxas)}" if taxas > 0 else ""
        print(
            f"#{e['id']} | {e['matricula']} | {e['isbn']} | "
            f"{fmt_data(e['data_emprestimo'])} -> {fmt_data(e['data_prevista'])} | "
            f"dev: {fmt_data(e['data_devolucao'])} | renov: {e['renovacoes']}/2 | {e['status']}{extra}"
        )


def menu_livros(bib):
    while True:
        print("\n[LIVROS] 1-Cadastrar 2-Listar 3-Disponíveis 4-Buscar 5-Atualizar 6-Excluir/Baixar 0-Voltar")
        op = input("> ").strip()
        try:
            if op == "1":
                bib.cadastrar_livro(
                    input("ISBN: "),
                    input("Título: "),
                    input("Autor: "),
                    input("Categoria: "),
                    ler_float("Valor de mercado: "),
                )
                print("Livro cadastrado.")

            elif op == "2":
                mostrar_livros(bib.listar_livros())

            elif op == "3":
                mostrar_livros(bib.buscar_livros(status="disponivel"))

            elif op == "4":
                res = bib.buscar_livros(
                    titulo=input("Título (Enter=ignorar): ").strip() or None,
                    autor=input("Autor (Enter=ignorar): ").strip() or None,
                    isbn=input("ISBN (Enter=ignorar): ").strip() or None,
                    categoria=input("Categoria (Enter=ignorar): ").strip() or None,
                    status=input("Status (Enter=ignorar): ").strip() or None,
                )
                mostrar_livros(res)

            elif op == "5":
                isbn = input("ISBN: ")
                bib.obter_livro(isbn)
                bib.atualizar_livro(
                    isbn,
                    titulo=input("Novo título (Enter=manter): ").strip() or None,
                    autor=input("Novo autor (Enter=manter): ").strip() or None,
                    categoria=input("Nova categoria (Enter=manter): ").strip() or None,
                    valor_mercado=ler_float("Novo valor (Enter=manter): ", obrigatorio=False),
                )
                print("Livro atualizado.")

            elif op == "6":
                isbn = input("ISBN: ")
                tipo = input("B-Baixar ou E-Excluir: ").strip().upper()
                if tipo not in ("B", "E"):
                    raise ErroValidacao("Opção inválida.")
                bib.excluir_livro(isbn, baixa=(tipo == "B"))
                print("Livro baixado." if tipo == "B" else "Livro excluído.")

            elif op == "0":
                break
            else:
                print("Opção inválida.")
        except ErroBiblioteca as e:
            print(f"Erro: {e}")


def menu_usuarios(bib):
    while True:
        print("\n[USUÁRIOS] 1-Cadastrar 2-Listar 3-Buscar 4-Atualizar 5-Excluir 0-Voltar")
        op = input("> ").strip()
        try:
            if op == "1":
                bib.cadastrar_usuario(
                    input("Matrícula: "),
                    input("Nome: "),
                    input("Categoria (aluno/professor/funcionario): "),
                )
                print("Usuário cadastrado.")

            elif op == "2":
                mostrar_usuarios(bib.listar_usuarios())

            elif op == "3":
                res = bib.buscar_usuarios(
                    nome=input("Nome (Enter=ignorar): ").strip() or None,
                    matricula=input("Matrícula (Enter=ignorar): ").strip() or None,
                    categoria=input("Categoria (Enter=ignorar): ").strip() or None,
                )
                mostrar_usuarios(res)

            elif op == "4":
                mat = input("Matrícula: ")
                bib.obter_usuario(mat)
                bib.atualizar_usuario(
                    mat,
                    nome=input("Novo nome (Enter=manter): ").strip() or None,
                    categoria=input("Nova categoria (Enter=manter): ").strip() or None,
                )
                print("Usuário atualizado.")

            elif op == "5":
                bib.excluir_usuario(input("Matrícula: "))
                print("Usuário excluído.")

            elif op == "0":
                break
            else:
                print("Opção inválida.")
        except ErroBiblioteca as e:
            print(f"Erro: {e}")


def menu_emprestimos(bib):
    while True:
        print("\n[EMPRÉSTIMOS] 1-Emprestar 2-Renovar 3-Devolver 4-Ativos 5-Atrasados 6-Histórico 0-Voltar")
        op = input("> ").strip()
        try:
            if op == "1":
                mat = input("Matrícula: ")
                qtd = ler_int("Quantidade de livros (1 a 3): ")
                if not 1 <= qtd <= 3:
                    raise ErroValidacao("Informe de 1 a 3.")
                isbns = [input(f"ISBN {i}: ") for i in range(1, qtd + 1)]
                dt = ler_data("Data (DD/MM/AAAA ou Enter=hoje): ")
                criados = bib.emprestar(mat, isbns, data_atual=dt)
                for e in criados:
                    print(f"Empréstimo #{e['id']} | {e['isbn']} | devolver até {fmt_data(e['data_prevista'])}")

            elif op == "2":
                mostrar_emprestimos(bib.listar_emprestimos_ativos())
                emp = bib.renovar(
                    ler_int("ID do empréstimo: "),
                    data_atual=ler_data("Data atual (DD/MM/AAAA ou Enter=hoje): "),
                )
                print(f"Renovado ({emp['renovacoes']}/2). Nova data: {fmt_data(emp['data_prevista'])}")

            elif op == "3":
                mostrar_emprestimos(bib.listar_emprestimos_ativos())
                id_emp = ler_int("ID do empréstimo: ")
                cond = input("Condição (integro/danificado/perdido): ")
                dt = ler_data("Data devolução (DD/MM/AAAA ou Enter=hoje): ")
                res = bib.devolver(id_emp, condicao=cond, data_dev=dt)
                print("Devolução registrada.")
                if res["dias_atraso"] > 0:
                    print(f"Atraso: {res['dias_atraso']} dia(s) | Multa: {fmt_moeda(res['multa'])}")
                if res["indenizacao"] > 0:
                    print(f"Indenização (valor de mercado): {fmt_moeda(res['indenizacao'])}")
                if res["total"] > 0:
                    print(f"Total a pagar: {fmt_moeda(res['total'])}")
                if res["proximo_fila"]:
                    print(f"Reservado para próximo da fila: {res['proximo_fila']}")

            elif op == "4":
                mostrar_emprestimos(bib.listar_emprestimos_ativos())

            elif op == "5":
                dt = ler_data("Data referência (DD/MM/AAAA ou Enter=hoje): ")
                atrasados = bib.listar_atrasados(data_ref=dt)
                if not atrasados:
                    print("Nenhum empréstimo atrasado.")
                for item in atrasados:
                    e = item["emprestimo"]
                    print(
                        f"#{e['id']} | {e['matricula']} | {e['isbn']} | "
                        f"{item['dias']} dia(s) atraso | multa: {fmt_moeda(item['multa'])}"
                    )

            elif op == "6":
                mostrar_emprestimos(bib.emprestimos)

            elif op == "0":
                break
            else:
                print("Opção inválida.")
        except ErroBiblioteca as e:
            print(f"Erro: {e}")


def menu_reservas(bib):
    while True:
        print("\n[RESERVAS] 1-Reservar 2-Ver filas 3-Cancelar 0-Voltar")
        op = input("> ").strip()
        try:
            if op == "1":
                pos = bib.reservar(input("Matrícula: "), input("ISBN: "))
                print(f"Reservado. Posição na fila: {pos}º")

            elif op == "2":
                achou = False
                for l in bib.listar_livros():
                    if l["fila_reservas"]:
                        achou = True
                        print(f"{l['isbn']} - {l['titulo']} ({l['status']}):")
                        for i, r in enumerate(l["fila_reservas"], 1):
                            print(f"  {i}º {r['matricula']} ({r['data'].strftime('%d/%m/%Y %H:%M:%S')})")
                if not achou:
                    print("Nenhuma reserva.")

            elif op == "3":
                bib.cancelar_reserva(input("Matrícula: "), input("ISBN: "))
                print("Reserva cancelada.")

            elif op == "0":
                break
            else:
                print("Opção inválida.")
        except ErroBiblioteca as e:
            print(f"Erro: {e}")


def main():
    bib = Biblioteca()
    while True:
        print("\n[BIBLIOTECA] 1-Livros 2-Usuários 3-Empréstimos 4-Reservas 0-Sair")
        try:
            op = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if op == "1":
            menu_livros(bib)
        elif op == "2":
            menu_usuarios(bib)
        elif op == "3":
            menu_emprestimos(bib)
        elif op == "4":
            menu_reservas(bib)
        elif op == "0":
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
