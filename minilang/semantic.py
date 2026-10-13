"""Analisador semântico da MiniLang (Marco 3).

Percorre a AST produzida pelo parser (M2) e verifica:

* declaração prévia e unicidade de identificadores por escopo;
* compatibilidade de tipos em atribuições, expressões e condições;
* (Extensão Opção A) declaração e chamada de procedimentos sem retorno,
  com parâmetros por valor: existência, número e tipo dos argumentos.

Os erros são acumulados (não interrompem a análise) e reportados com linha e
coluna, no mesmo estilo dos analisadores léxico e sintático.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from minilang.ast import (
    ASTNode,
    AssignStmtNode,
    BinaryOpNode,
    CallStmtNode,
    IfStmtNode,
    LiteralNode,
    ProcedureDeclNode,
    ProgramNode,
    ReadStmtNode,
    UnaryOpNode,
    VarAccessNode,
    VarDeclNode,
    WhileStmtNode,
    WriteStmtNode,
)

INTEIRO = "inteiro"
BOOLEANO = "booleano"

CAT_VARIAVEL = "variável"
CAT_PARAMETRO = "parâmetro"
CAT_PROCEDIMENTO = "procedimento"

# Sinônimos aceitos para os operadores (o parser pode emitir o lexema original).
_ALIAS_OPERADORES = {"&&": "e", "||": "ou", "!": "não", "nao": "não"}

_OP_ARITMETICOS = {"+", "-", "*", "/", "%"}
_OP_ORDEM = {"<", "<=", ">", ">="}
_OP_IGUALDADE = {"==", "!="}
_OP_LOGICOS = {"e", "ou"}


# ---------------------------------------------------------------------------
# Erros
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ErroSemantico:
    linha: int
    coluna: int
    mensagem: str

    def __str__(self) -> str:
        return f"Erro semântico [linha {self.linha}, coluna {self.coluna}]: {self.mensagem}"


# ---------------------------------------------------------------------------
# Tabela de símbolos
# ---------------------------------------------------------------------------

@dataclass
class Simbolo:
    nome: str
    categoria: str
    tipo: Optional[str]  # None para procedimentos
    linha: int
    coluna: int
    parametros: List[Tuple[str, str]] = field(default_factory=list)  # (nome, tipo)


@dataclass
class Escopo:
    nome: str
    simbolos: Dict[str, Simbolo] = field(default_factory=dict)


class TabelaSimbolos:
    """Pilha de escopos (global -> procedimento) com histórico para exibição."""

    def __init__(self) -> None:
        self._pilha: List[Escopo] = []
        self.historico: List[Escopo] = []

    def entrar_escopo(self, nome: str) -> None:
        escopo = Escopo(nome)
        self._pilha.append(escopo)
        self.historico.append(escopo)

    def sair_escopo(self) -> None:
        self._pilha.pop()

    def declarar(self, simbolo: Simbolo) -> Optional[Simbolo]:
        """Declara no escopo atual. Devolve o símbolo já existente se houver duplicata."""
        atual = self._pilha[-1]
        existente = atual.simbolos.get(simbolo.nome)
        if existente is not None:
            return existente
        atual.simbolos[simbolo.nome] = simbolo
        return None

    def buscar(self, nome: str) -> Optional[Simbolo]:
        """Busca do escopo mais interno para o mais externo."""
        for escopo in reversed(self._pilha):
            if nome in escopo.simbolos:
                return escopo.simbolos[nome]
        return None


def formatar_tabela_simbolos(tabela: TabelaSimbolos) -> str:
    linhas: List[str] = []
    for escopo in tabela.historico:
        linhas.append(f"Escopo: {escopo.nome}")
        linhas.append(f"  {'Nome':<20}{'Categoria':<15}{'Tipo':<11}{'Declarado em':<15}Detalhe")
        linhas.append("  " + "-" * 75)
        if not escopo.simbolos:
            linhas.append("  (vazio)")
        for s in escopo.simbolos.values():
            tipo = s.tipo if s.tipo else "—"
            detalhe = ""
            if s.categoria == CAT_PROCEDIMENTO:
                params = ", ".join(f"{n}: {t}" for n, t in s.parametros)
                detalhe = f"({params})"
            posicao = f"{s.linha}:{s.coluna}"
            linhas.append(f"  {s.nome:<20}{s.categoria:<15}{tipo:<11}{posicao:<15}{detalhe}")
        linhas.append("")
    return "\n".join(linhas).rstrip()


# ---------------------------------------------------------------------------
# Analisador
# ---------------------------------------------------------------------------

class AnalisadorSemantico:
    def __init__(self) -> None:
        self.tabela = TabelaSimbolos()
        self.erros: List[ErroSemantico] = []

    @property
    def tem_erros(self) -> bool:
        return bool(self.erros)

    # -- utilidades ---------------------------------------------------------

    def _erro(self, no: ASTNode, mensagem: str) -> None:
        self.erros.append(ErroSemantico(no.linha, no.coluna, mensagem))

    # -- ponto de entrada ---------------------------------------------------

    def analisar(self, programa: ProgramNode) -> List[ErroSemantico]:
        self.tabela.entrar_escopo("global")

        # Passo 1: coleta as declarações globais (permite recursão e chamadas
        # entre procedimentos independentemente da ordem de declaração).
        for decl in programa.declaracoes:
            if isinstance(decl, VarDeclNode):
                self._declarar(decl, decl.nome, CAT_VARIAVEL, decl.tipo)
            elif isinstance(decl, ProcedureDeclNode):
                self._declarar_procedimento(decl)

        # Passo 2: corpo dos procedimentos e comandos do programa principal.
        for decl in programa.declaracoes:
            if isinstance(decl, ProcedureDeclNode):
                self._analisar_procedimento(decl)

        self._comandos(programa.comandos)
        self.tabela.sair_escopo()
        return self.erros

    # -- declarações --------------------------------------------------------

    def _declarar(self, no: ASTNode, nome: str, categoria: str, tipo: Optional[str],
                  parametros: Optional[List[Tuple[str, str]]] = None) -> None:
        simbolo = Simbolo(nome, categoria, tipo, no.linha, no.coluna, parametros or [])
        existente = self.tabela.declarar(simbolo)
        if existente is not None:
            self._erro(
                no,
                f"identificador '{nome}' já declarado neste escopo "
                f"(primeira declaração na linha {existente.linha}, coluna {existente.coluna})",
            )

    def _declarar_procedimento(self, proc: ProcedureDeclNode) -> None:
        assinatura = [(p.nome, p.tipo) for p in proc.parametros]
        self._declarar(proc, proc.nome, CAT_PROCEDIMENTO, None, assinatura)

    def _analisar_procedimento(self, proc: ProcedureDeclNode) -> None:
        self.tabela.entrar_escopo(f"procedimento {proc.nome}")
        for param in proc.parametros:
            self._declarar(param, param.nome, CAT_PARAMETRO, param.tipo)
        for var in proc.declaracoes:
            self._declarar(var, var.nome, CAT_VARIAVEL, var.tipo)
        self._comandos(proc.comandos)
        self.tabela.sair_escopo()

    # -- comandos -----------------------------------------------------------

    def _comandos(self, comandos: List[ASTNode]) -> None:
        for cmd in comandos:
            self._comando(cmd)

    def _comando(self, no: ASTNode) -> None:
        if isinstance(no, AssignStmtNode):
            simbolo = self._resolver_variavel(no.identificador, no)
            tipo_expr = self._expressao(no.expressao)
            if simbolo is not None and tipo_expr is not None and simbolo.tipo != tipo_expr:
                self._erro(
                    no.expressao,
                    f"tipos incompatíveis na atribuição: '{no.identificador}' é "
                    f"{simbolo.tipo}, mas a expressão é {tipo_expr}",
                )

        elif isinstance(no, CallStmtNode):
            self._chamada(no)

        elif isinstance(no, IfStmtNode):
            self._condicao(no.condicao, "se")
            self._comandos(no.entao_comandos)
            if no.senao_comandos is not None:
                self._comandos(no.senao_comandos)

        elif isinstance(no, WhileStmtNode):
            self._condicao(no.condicao, "enquanto")
            self._comandos(no.comandos)

        elif isinstance(no, ReadStmtNode):
            self._resolver_variavel(no.identificador, no)

        elif isinstance(no, WriteStmtNode):
            self._expressao(no.expressao)

    def _condicao(self, expressao: ASTNode, comando: str) -> None:
        tipo = self._expressao(expressao)
        if tipo is not None and tipo != BOOLEANO:
            self._erro(
                expressao,
                f"a condição do '{comando}' deve ser booleano, mas a expressão é {tipo}",
            )

    def _chamada(self, no: CallStmtNode) -> None:
        # Sempre analisa os argumentos, para reportar erros dentro deles.
        tipos_args = [self._expressao(arg) for arg in no.argumentos]

        simbolo = self.tabela.buscar(no.identificador)
        if simbolo is None:
            self._erro(no, f"procedimento '{no.identificador}' não declarado")
            return
        if simbolo.categoria != CAT_PROCEDIMENTO:
            self._erro(no, f"'{no.identificador}' é {simbolo.categoria} e não pode ser chamado como procedimento")
            return

        esperados = len(simbolo.parametros)
        recebidos = len(no.argumentos)
        if esperados != recebidos:
            self._erro(
                no,
                f"procedimento '{no.identificador}' espera {esperados} argumento(s), "
                f"mas recebeu {recebidos}",
            )
            return

        for i, ((nome_param, tipo_param), tipo_arg, arg) in enumerate(
            zip(simbolo.parametros, tipos_args, no.argumentos), start=1
        ):
            if tipo_arg is not None and tipo_arg != tipo_param:
                self._erro(
                    arg,
                    f"argumento {i} da chamada de '{no.identificador}': o parâmetro "
                    f"'{nome_param}' é {tipo_param}, mas o argumento é {tipo_arg}",
                )

    def _resolver_variavel(self, nome: str, no: ASTNode) -> Optional[Simbolo]:
        simbolo = self.tabela.buscar(nome)
        if simbolo is None:
            self._erro(no, f"variável '{nome}' não declarada")
            return None
        if simbolo.categoria == CAT_PROCEDIMENTO:
            self._erro(no, f"'{nome}' é um procedimento e não pode ser usado como variável")
            return None
        return simbolo

    # -- expressões (devolvem o tipo, ou None se já houve erro) --------------

    def _expressao(self, no: ASTNode) -> Optional[str]:
        if isinstance(no, LiteralNode):
            tipo = _tipo_literal(no)
            if tipo is None:
                self._erro(no, f"literal {no.valor!r} com tipo desconhecido ({no.tipo})")
            return tipo

        if isinstance(no, VarAccessNode):
            simbolo = self._resolver_variavel(no.nome, no)
            return simbolo.tipo if simbolo is not None else None

        if isinstance(no, UnaryOpNode):
            return self._unaria(no)

        if isinstance(no, BinaryOpNode):
            return self._binaria(no)

        self._erro(no, f"expressão inválida ({type(no).__name__})")
        return None

    def _unaria(self, no: UnaryOpNode) -> Optional[str]:
        op = _ALIAS_OPERADORES.get(no.operador, no.operador)
        tipo = self._expressao(no.operando)

        if op == "não":
            if tipo is not None and tipo != BOOLEANO:
                self._erro(no, f"o operador 'não' exige operando booleano, mas recebeu {tipo}")
            return BOOLEANO
        if op == "-":
            if tipo is not None and tipo != INTEIRO:
                self._erro(no, f"o operador unário '-' exige operando inteiro, mas recebeu {tipo}")
            return INTEIRO

        self._erro(no, f"operador unário desconhecido '{no.operador}'")
        return None

    def _binaria(self, no: BinaryOpNode) -> Optional[str]:
        op = _ALIAS_OPERADORES.get(no.operador, no.operador)
        esq = self._expressao(no.esquerda)
        dir_ = self._expressao(no.direita)

        if op in _OP_ARITMETICOS:
            self._exigir(no, op, esq, dir_, INTEIRO)
            if op in ("/", "%") and _e_zero_literal(no.direita):
                self._erro(no.direita, f"divisão por zero no operador '{op}'")
            return INTEIRO

        if op in _OP_ORDEM:
            self._exigir(no, op, esq, dir_, INTEIRO)
            return BOOLEANO

        if op in _OP_LOGICOS:
            self._exigir(no, op, esq, dir_, BOOLEANO)
            return BOOLEANO

        if op in _OP_IGUALDADE:
            if esq is not None and dir_ is not None and esq != dir_:
                self._erro(
                    no,
                    f"o operador '{op}' exige operandos do mesmo tipo, "
                    f"mas recebeu {esq} e {dir_}",
                )
            return BOOLEANO

        self._erro(no, f"operador binário desconhecido '{no.operador}'")
        return None

    def _exigir(self, no: ASTNode, op: str, esq: Optional[str], dir_: Optional[str], esperado: str) -> None:
        for lado, tipo in (("esquerdo", esq), ("direito", dir_)):
            if tipo is not None and tipo != esperado:
                self._erro(
                    no,
                    f"o operador '{op}' exige operandos {esperado}, mas o operando {lado} é {tipo}",
                )


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def _tipo_literal(no: LiteralNode) -> Optional[str]:
    valor = no.valor
    if isinstance(valor, bool):  # bool é subclasse de int: testar primeiro
        return BOOLEANO
    if isinstance(valor, int):
        return INTEIRO

    tipo = str(no.tipo).lower()
    if tipo in ("inteiro", "int", "integer", "numero", "número"):
        return INTEIRO
    if tipo in ("booleano", "bool", "boolean"):
        return BOOLEANO

    if isinstance(valor, str):
        if valor.lower() in ("verdadeiro", "falso"):
            return BOOLEANO
        if valor.lstrip("-").isdigit():
            return INTEIRO
    return None


def _e_zero_literal(no: ASTNode) -> bool:
    if not isinstance(no, LiteralNode) or _tipo_literal(no) != INTEIRO:
        return False
    try:
        return int(no.valor) == 0
    except (TypeError, ValueError):
        return False


def analisar_semantica(programa: ProgramNode) -> AnalisadorSemantico:
    """Atalho: roda a análise e devolve o analisador (com .erros e .tabela)."""
    analisador = AnalisadorSemantico()
    analisador.analisar(programa)
    return analisador
