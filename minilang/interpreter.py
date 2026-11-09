import os
import re
import sys

_minilang_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_minilang_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
while _minilang_dir in sys.path:
    sys.path.remove(_minilang_dir)

from typing import Any, Callable, Dict, List, Optional

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

LIMITE_PASSOS_PADRAO = 1_000_000
LIMITE_PILHA_PADRAO = 100

_ALIAS_OPERADORES = {"nao": "não"}


class ErroExecucao(Exception):
    def __init__(self, mensagem: str, linha: int, coluna: int) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna

    def __str__(self) -> str:
        return f"Erro de execução [linha {self.linha}, coluna {self.coluna}]: {self.mensagem}"


def normalizar_operador(operador: str) -> str:
    return _ALIAS_OPERADORES.get(operador, operador)


def valor_padrao(tipo: str) -> Any:
    return False if tipo == BOOLEANO else 0


def formatar_valor(valor: Any) -> str:
    if isinstance(valor, bool):
        return "verdadeiro" if valor else "falso"
    return str(valor)


def dividir(dividendo: int, divisor: int) -> int:
    if divisor == 0:
        raise ZeroDivisionError("divisão por zero")
    quociente = abs(dividendo) // abs(divisor)
    return -quociente if (dividendo < 0) != (divisor < 0) else quociente


def resto(dividendo: int, divisor: int) -> int:
    return dividendo - divisor * dividir(dividendo, divisor)


def aplicar_unaria(operador: str, valor: Any) -> Any:
    operador = normalizar_operador(operador)
    if operador == "não":
        return not valor
    if operador == "-":
        return -valor
    raise ValueError(f"operador unário desconhecido '{operador}'")


def aplicar_binaria(operador: str, esquerda: Any, direita: Any) -> Any:
    operador = normalizar_operador(operador)
    if operador == "+":
        return esquerda + direita
    if operador == "-":
        return esquerda - direita
    if operador == "*":
        return esquerda * direita
    if operador == "/":
        return dividir(esquerda, direita)
    if operador == "%":
        return resto(esquerda, direita)
    if operador == "<":
        return esquerda < direita
    if operador == "<=":
        return esquerda <= direita
    if operador == ">":
        return esquerda > direita
    if operador == ">=":
        return esquerda >= direita
    if operador == "==":
        return esquerda == direita
    if operador == "!=":
        return esquerda != direita
    if operador == "e":
        return esquerda and direita
    if operador == "ou":
        return esquerda or direita
    raise ValueError(f"operador binário desconhecido '{operador}'")


class Quadro:
    def __init__(self, nome: str) -> None:
        self.nome = nome
        self.valores: Dict[str, Any] = {}
        self.tipos: Dict[str, str] = {}

    def definir(self, nome: str, tipo: str, valor: Any = None) -> None:
        self.tipos[nome] = tipo
        self.valores[nome] = valor_padrao(tipo) if valor is None else valor


def entrada_padrao(nome: str) -> str:
    if sys.stdin.isatty():
        return input(f"{nome}? ")
    linha = sys.stdin.readline()
    if linha == "":
        raise EOFError
    return linha


class Interpretador:
    def __init__(
        self,
        entrada: Optional[Callable[[str], str]] = None,
        saida: Optional[Callable[[str], None]] = None,
        limite_passos: int = LIMITE_PASSOS_PADRAO,
        limite_pilha: int = LIMITE_PILHA_PADRAO,
    ) -> None:
        self.entrada = entrada or entrada_padrao
        self.saida = saida or print
        self.limite_passos = limite_passos
        self.limite_pilha = limite_pilha
        self.procedimentos: Dict[str, ProcedureDeclNode] = {}
        self.pilha: List[Quadro] = []
        self.passos = 0
        self.chamadas = 0
        self.profundidade_maxima = 0

    def executar(self, programa: ProgramNode) -> None:
        self.procedimentos = {}
        self.pilha = [Quadro("global")]
        self.passos = 0
        self.chamadas = 0
        self.profundidade_maxima = 0

        for decl in programa.declaracoes:
            if isinstance(decl, VarDeclNode):
                self.pilha[0].definir(decl.nome, decl.tipo)
            elif isinstance(decl, ProcedureDeclNode):
                self.procedimentos[decl.nome] = decl

        try:
            self._comandos(programa.comandos)
        except RecursionError:
            raise ErroExecucao(
                "estouro da pilha de execução do interpretador", programa.linha, programa.coluna
            ) from None

    def _resolver(self, nome: str, no: ASTNode) -> Quadro:
        local = self.pilha[-1]
        if nome in local.valores:
            return local
        global_ = self.pilha[0]
        if nome in global_.valores:
            return global_
        raise ErroExecucao(f"variável '{nome}' não declarada", no.linha, no.coluna)

    def _contar_passo(self, no: ASTNode) -> None:
        self.passos += 1
        if self.passos > self.limite_passos:
            raise ErroExecucao(
                f"limite de {self.limite_passos} passos excedido (possível laço infinito)",
                no.linha,
                no.coluna,
            )

    def _comandos(self, comandos: List[ASTNode]) -> None:
        for comando in comandos:
            self._comando(comando)

    def _comando(self, no: ASTNode) -> None:
        self._contar_passo(no)

        if isinstance(no, AssignStmtNode):
            valor = self._avaliar(no.expressao)
            self._resolver(no.identificador, no).valores[no.identificador] = valor

        elif isinstance(no, CallStmtNode):
            self._chamar(no)

        elif isinstance(no, IfStmtNode):
            if self._avaliar(no.condicao):
                self._comandos(no.entao_comandos)
            elif no.senao_comandos is not None:
                self._comandos(no.senao_comandos)

        elif isinstance(no, WhileStmtNode):
            while self._avaliar(no.condicao):
                self._contar_passo(no)
                self._comandos(no.comandos)

        elif isinstance(no, ReadStmtNode):
            self._ler(no)

        elif isinstance(no, WriteStmtNode):
            self.saida(formatar_valor(self._avaliar(no.expressao)))

        else:
            raise ErroExecucao(f"comando inválido ({type(no).__name__})", no.linha, no.coluna)

    def _ler(self, no: ReadStmtNode) -> None:
        quadro = self._resolver(no.identificador, no)
        tipo = quadro.tipos[no.identificador]
        try:
            texto = self.entrada(no.identificador).strip()
        except EOFError:
            raise ErroExecucao(
                f"fim da entrada: não há valor disponível para 'leia({no.identificador})'",
                no.linha,
                no.coluna,
            ) from None

        if tipo == BOOLEANO:
            if texto not in ("verdadeiro", "falso"):
                raise ErroExecucao(
                    f"entrada inválida para '{no.identificador}': esperado 'verdadeiro' ou "
                    f"'falso', mas recebeu '{texto}'",
                    no.linha,
                    no.coluna,
                )
            quadro.valores[no.identificador] = texto == "verdadeiro"
            return

        if re.fullmatch(r"-?[0-9]+", texto) is None:
            raise ErroExecucao(
                f"entrada inválida para '{no.identificador}': esperado inteiro, "
                f"mas recebeu '{texto}'",
                no.linha,
                no.coluna,
            )
        quadro.valores[no.identificador] = int(texto)

    def _chamar(self, no: CallStmtNode) -> None:
        procedimento = self.procedimentos.get(no.identificador)
        if procedimento is None:
            raise ErroExecucao(f"procedimento '{no.identificador}' não declarado", no.linha, no.coluna)

        argumentos = [self._avaliar(argumento) for argumento in no.argumentos]
        if len(argumentos) != len(procedimento.parametros):
            raise ErroExecucao(
                f"procedimento '{no.identificador}' espera {len(procedimento.parametros)} "
                f"argumento(s), mas recebeu {len(argumentos)}",
                no.linha,
                no.coluna,
            )

        if len(self.pilha) - 1 >= self.limite_pilha:
            raise ErroExecucao(
                f"estouro da pilha de ativação: profundidade máxima de {self.limite_pilha} "
                f"chamadas excedida em '{no.identificador}'",
                no.linha,
                no.coluna,
            )

        quadro = Quadro(f"procedimento {procedimento.nome}")
        for parametro, valor in zip(procedimento.parametros, argumentos):
            quadro.definir(parametro.nome, parametro.tipo, valor)
        for variavel in procedimento.declaracoes:
            quadro.definir(variavel.nome, variavel.tipo)

        self.pilha.append(quadro)
        self.chamadas += 1
        self.profundidade_maxima = max(self.profundidade_maxima, len(self.pilha) - 1)
        try:
            self._comandos(procedimento.comandos)
        finally:
            self.pilha.pop()

    def _avaliar(self, no: ASTNode) -> Any:
        if isinstance(no, LiteralNode):
            return no.valor

        if isinstance(no, VarAccessNode):
            return self._resolver(no.nome, no).valores[no.nome]

        if isinstance(no, UnaryOpNode):
            return aplicar_unaria(no.operador, self._avaliar(no.operando))

        if isinstance(no, BinaryOpNode):
            operador = normalizar_operador(no.operador)
            esquerda = self._avaliar(no.esquerda)
            if operador == "e":
                return esquerda and self._avaliar(no.direita)
            if operador == "ou":
                return esquerda or self._avaliar(no.direita)
            direita = self._avaliar(no.direita)
            try:
                return aplicar_binaria(operador, esquerda, direita)
            except ZeroDivisionError:
                mensagem = "divisão por zero" if operador == "/" else "resto da divisão por zero"
                raise ErroExecucao(mensagem, no.linha, no.coluna) from None

        raise ErroExecucao(f"expressão inválida ({type(no).__name__})", no.linha, no.coluna)


def executar_programa(programa: ProgramNode, **opcoes: Any) -> Interpretador:
    interpretador = Interpretador(**opcoes)
    interpretador.executar(programa)
    return interpretador
