"""Dimension values: a number, a parameter name, or an arithmetic expression over parameters.

``60`` → fixed; ``"Box_Width"`` → bound to that parameter; ``"Box_Width - 2*Wall"`` → derived
dimension, evaluated now and bound as FreeCAD expression so it follows parameter changes.

The FreeCAD expression is generated from the syntax tree: numbers that are added to or
subtracted from dimensioned parameters get the parameter's unit (``Height + 2`` →
``<<Parameters>>.Height + 2 mm``), because FreeCAD rejects mixing units with plain numbers.
"""

from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass
from typing import Any

from buddy_core import parameters
from buddy_core.errors import validation

Number = int | float
ValueSpec = Number | str

_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_SYMBOLS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


@dataclass(frozen=True)
class Value:
    number: float
    expression: str | None = None

    def scaled(self, factor: float) -> Value:
        expr = f"({self.expression}) * {factor:g}" if self.expression else None
        return Value(self.number * factor, expr)


def _check(node: ast.AST) -> None:
    for child in ast.walk(node):
        allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Load, ast.Constant)
        if not isinstance(child, allowed) and type(child) not in _BINARY and type(child) not in _UNARY:
            raise validation(
                "An expression may only contain numbers, parameter names, + - * / and parentheses"
            )
        if isinstance(child, ast.BinOp) and type(child.op) not in _BINARY:
            raise validation(
                "An expression may only contain numbers, parameter names, + - * / and parentheses"
            )
        if isinstance(child, ast.UnaryOp) and type(child.op) not in _UNARY:
            raise validation(
                "An expression may only contain numbers, parameter names, + - * / and parentheses"
            )
        if isinstance(child, ast.Constant) and (
            isinstance(child.value, bool) or not isinstance(child.value, int | float)
        ):
            raise validation(
                "An expression may only contain numbers, parameter names, + - * / and parentheses"
            )


def _evaluate(node: ast.AST, doc: Any) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, doc)
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.Name):
        return parameters.numeric_value(doc, node.id)
    if isinstance(node, ast.BinOp):
        left, right = _evaluate(node.left, doc), _evaluate(node.right, doc)
        if isinstance(node.op, ast.Div) and right == 0:
            raise validation("Division by 0 in the expression")
        return _BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp):
        return _UNARY[type(node.op)](_evaluate(node.operand, doc))
    raise validation("Invalid expression")


def _unit(node: ast.AST, doc: Any) -> str | None:
    """Unit of a (sub-)expression: the unit of its dimensioned parameter, if exactly one side has one."""
    if isinstance(node, ast.Expression):
        return _unit(node.body, doc)
    if isinstance(node, ast.Name):
        return parameters.unit_of(doc, node.id)
    if isinstance(node, ast.UnaryOp):
        return _unit(node.operand, doc)
    if isinstance(node, ast.BinOp):
        left, right = _unit(node.left, doc), _unit(node.right, doc)
        if isinstance(node.op, ast.Div) and right is not None:
            return None if left == right else left
        return left or right
    return None


def _emit(node: ast.AST, doc: Any, unit: str | None) -> str:
    if isinstance(node, ast.Expression):
        return _emit(node.body, doc, _unit(node.body, doc))
    if isinstance(node, ast.Constant):
        text = f"{node.value:.12g}" if isinstance(node.value, float) else str(node.value)
        return f"{text} {unit}" if unit else text
    if isinstance(node, ast.Name):
        return parameters.expression(node.id)
    if isinstance(node, ast.UnaryOp):
        return (
            f"-({_emit(node.operand, doc, unit)})"
            if isinstance(node.op, ast.USub)
            else _emit(node.operand, doc, unit)
        )
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Add | ast.Sub):
            context = _unit(node, doc)
            left, right = _emit(node.left, doc, context), _emit(node.right, doc, context)
        else:  # factors stay unitless: 2 * Wall, Width / 2
            left, right = _emit(node.left, doc, None), _emit(node.right, doc, None)
        return f"({left} {_SYMBOLS[type(node.op)]} {right})"
    raise validation("Invalid expression")


def _expression(doc: Any, text: str, what: str) -> Value:
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError:
        raise validation(f"{what}: invalid expression '{text}'") from None
    _check(tree)
    number = _evaluate(tree, doc)
    if not any(isinstance(node, ast.Name) for node in ast.walk(tree)):
        return Value(number)  # plain arithmetic, nothing to bind
    return Value(number, _emit(tree, doc, None))


def resolve(doc: Any, spec: ValueSpec, what: str) -> Value:
    if isinstance(spec, bool):
        raise validation(f"{what}: number, parameter name or expression expected, not {spec!r}")
    if isinstance(spec, int | float):
        return Value(float(spec))
    if isinstance(spec, str):
        text = spec.strip()
        if _NAME.match(text):
            return Value(parameters.numeric_value(doc, text), parameters.expression(text))
        return _expression(doc, text, what)
    raise validation(f"{what}: number, parameter name or expression expected, not {spec!r}")


def number(doc: Any, spec: ValueSpec, what: str) -> float:
    return resolve(doc, spec, what).number


def apply(obj: Any, prop: str, value: Value, unit: str = "mm") -> None:
    """Set a property to the value and bind it to the parameter expression if there is one."""
    if value.expression:
        obj.setExpression(prop, value.expression)
    else:
        obj.setExpression(prop, None)
        setattr(obj, prop, f"{value.number} {unit}" if unit else value.number)
