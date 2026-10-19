from __future__ import annotations
import os
import copy
import ctypes
from typing import Set, List, Dict, Tuple
from config import PASER_LIB

libtamarin = ctypes.CDLL(PASER_LIB)
libtamarin.tamarin_parse.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
libtamarin.tamarin_parse.restype = ctypes.c_int32


CONST_FUNCTIONS = []


class SyntaxData:
    def __init__(self, raw={}, file="",  indent=4) -> None:
        self.prefix = ""
        self.suffix = ""
        self.type = ""
        self.attr = {}
        self.children: List[SyntaxData] = []
        self.indent = indent * " "
        if "" != file:
            self.parse_from_file(file)
        elif raw != {}:
            self.parse_from_dict(raw)

    def parse_from_file(self, infile: str) -> None:
        outfile = f"/tmp/.{os.getpid()}_output.tmp"
        ret = libtamarin.tamarin_parse(infile.encode(), outfile.encode())

        result = None
        if 0 == ret:
            with open(outfile, 'r') as f:
                result = f.read()
            result = result.replace("\n", "\\n")
            result = result.replace(r"\(", r"\\(")
            result = result.replace(r"\)", r"\\)")
            result = result.replace(r"\s", r"\\s")
            result = result.replace(r"\d", r"\\d")
            result = result.replace(r"\.", r"\\.")
            result = result.replace(r"\^", r"\\^")
            result = result.replace(r"\*", r"\\*")

            result = eval(result)
            os.remove(outfile)
            self.parse_from_dict(result)
        else:
            print(f"ERROR: failed to parse {infile}")

    def parse_from_dict(self, raw: dict) -> None:
        self.extract_data(raw)

        if 'children' not in raw:
            return

        results = []
        for child in raw['children']:
            if child['type'] == 'reserve':
                results.append(child['str'])
            else:
                results.append(SyntaxData(child))

        reserve = ""
        for r in results:
            if type(r) == str:
                reserve += r
            else:
                r.prefix = reserve
                self.children.append(r)
                reserve = ""

        if len(self.children) > 0:
            self.children[-1].suffix = reserve
        elif "" != reserve:
            print("ERROR: reserve is not empty")

    def extract_data(self, raw: dict) -> None:
        self.type = raw['type']
        if "theory" == self.type:
            self.attr['name'] = raw['name']
        elif "builtin_func" == self.type:
            self.attr['name'] = raw['str']
        elif "function" == self.type:
            self.attr['name'] = raw['name']
            self.attr['arity'] = raw['arity']
            self.attr['is_private'] = raw['is_private']
        elif "macro" == self.type:
            self.attr['name'] = raw['name']
            self.attr['param'] = []
            if 'param' in raw:
                for p in raw['param']:
                    self.attr['param'].append(SyntaxData(p))
        elif "macro_param" == self.type:
            self.attr['name'] = raw['str']
        elif "rule" == self.type:
            self.attr['name'] = raw['name']
            if 'attrs' in raw:
                self.attr['attrs'] = SyntaxData(raw['attrs'])
            if 'let' in raw:
                self.attr['let'] = SyntaxData(raw['let'])
            if 'modulo' in raw:
                self.attr['modulo'] = SyntaxData(raw['modulo'])
        elif "rule_attr" == self.type:
            self.attr['color'] = raw['color']
        elif "rule_modulo" == self.type:
            self.attr['name'] = raw['name']
        elif "rule_let" == self.type:
            if "key" in raw:
                self.attr['key'] = SyntaxData(raw['key'])
        elif "key_mark" == self.type:
            self.attr['name'] = raw['key']
        elif "facts" == self.type:
            self.attr['is_action'] = raw['is_action']
        elif "fact" == self.type:
            self.attr['name'] = raw['name']
            self.attr['is_constant'] = raw['is_constant']
        elif "fact_annote" == self.type:
            self.attr['name'] = raw['str']
        elif "term" == self.type:
            self.attr['op'] = raw['op']
            self.attr['val'] = (raw['val'] == "(null)") if None else raw['val']

    def __build_line(self, code: str, indent: int) -> str:
        return f"{self.indent * indent}{code}\n"

    def __build_indent(self, indent: int) -> str:
        return self.indent * indent

    def __build_theory(self, indent: int) -> str:
        code = self.__build_line(f"theory {self.attr['name']}", indent)
        code += self.__build_line("begin", indent)
        for child in self.children:
            code += child.build_code(indent + 1)
        code += self.__build_line("end", indent)
        return code

    def __build_rule(self, indent: int) -> str:
        code = ""
        if 'modulo' in self.attr and 'attrs' in self.attr:
            code += self.__build_line(
                f"rule (modulo {self.attr['modulo'].attr['name']}) {self.attr['name']} [color=#{self.attr['attrs'].attr['color']}]:", indent)
        elif 'modulo' in self.attr:
            code += self.__build_line(
                f"rule (modulo {self.attr['modulo'].attr['name']}) {self.attr['name']}:", indent)
        elif 'attrs' in self.attr:
            code += self.__build_line(
                f"rule {self.attr['name']} [color={self.attr['attrs'].attr['color']}]:", indent)
        else:
            code += self.__build_line(
                f"rule {self.attr['name']}:", indent)

        if 'let' in self.attr and len(self.attr['let'].children) > 0:
            code += self.__build_line("let", indent + 1)
            for child in self.attr['let'].children:
                code += child.build_code(indent + 2) + '\n'
            code += self.__build_line("in", indent + 1)

        for child in self.children:
            code += child.build_code(indent + 1)

        code += '\n'
        return code

    def __build_facts(self, indent: int) -> str:
        code = ""
        if 0 == len(self.children):
            if self.attr['is_action']:
                code += self.__build_line("-->", indent)
            else:
                code += self.__build_line("[]", indent)
        else:
            if self.attr['is_action']:
                code += self.__build_line("--[", indent)
            else:
                code += self.__build_line("[", indent)
            for i in range(len(self.children)):
                code += self.children[i].build_code(indent + 1)
                if i != len(self.children) - 1:
                    code += ",\n"
            code += "\n"
            if self.attr['is_action']:
                code += self.__build_line("]->", indent)
            else:
                code += self.__build_line("]", indent)
        return code

    def __build_fact(self, indent: int) -> str:
        code = self.__build_indent(indent)
        if self.attr['is_constant']:
            code += f"!{self.attr['name']}("
        else:
            code += f"{self.attr['name']}("
        for i in range(len(self.children)):
            code += self.children[i].build_code(0)
            if i != len(self.children) - 1:
                code += ", "
        code += ")"

        if 'annote' in self.attr:
            code += "["
            for i in range(len(self.attr['annote'])):
                code += self.attr['annote'][i].attr['name']
                if i != len(self.attr['annote']) - 1:
                    code += ", "
            code += "]"

        return code

    def __build_functions(self, indent: int) -> str:
        code = f"{self.__build_indent(indent)}functions: "
        for i in range(len(self.children)):
            code += self.children[i].build_code(0)
            if i != len(self.children) - 1:
                code += ", "
        code += "\n\n"
        return code

    def __build_function(self) -> str:
        return f"{self.attr['name']}/{self.attr['arity']}"

    def __build_builtin(self, indent: int) -> str:
        code = f"{self.__build_indent(indent)}builtins: "
        for i in range(len(self.children)):
            code += self.children[i].build_code(0)
            if i != len(self.children) - 1:
                code += ", "
        code += "\n\n"
        return code

    def __build_builtin_func(self) -> str:
        return self.attr['name']

    def __build_macros(self, indent: int) -> str:
        code = self.__build_line("macros:", indent)
        for i in range(len(self.children)):
            code += self.children[i].build_code(indent + 1)
            if i != len(self.children) - 1:
                code += ",\n"
        code += "\n\n"
        return code

    def __build_macro(self) -> str:
        code = f"{self.attr['name']}("
        for i in range(len(self.attr['param'])):
            code += self.attr['param'][i].attr['name']
            if i != len(self.attr['param']) - 1:
                code += ", "
        code += ") = "
        for i in range(len(self.children)):
            code += self.children[i].build_code(0)
        return code

    def __build_equations(self, indent: int) -> str:
        code = self.__build_line("equations:", indent)
        for i in range(len(self.children)):
            code += self.children[i].build_code(indent + 1)
            if i != len(self.children) - 1:
                code += ",\n"
        code += "\n\n"
        return code

    def __build_equation(self, indent: int) -> str:
        code = self.__build_indent(indent)
        for i in range(len(self.children)):
            code += self.children[i].build_code(0)
            if i != len(self.children) - 1:
                code += " = "
        return code

    def __build_term(self) -> str:
        code = ""
        op = self.attr['op']
        if op == "VarMsg":
            code += self.attr['val']
        elif op == "VarPub":
            code += self.attr['val']
        elif op == "VarFresh":
            code += self.attr['val']
        elif op == "Literal":
            code += self.attr['val']
        elif op == "LiteralFresh":
            code += self.attr['val']
        elif op == "^":
            code += f"({self.children[0].build_code(0)})"
            code += " ^ "
            code += f"({self.children[1].build_code(0)})"
        elif op == "*":
            code += f"({self.children[0].build_code(0)})"
            code += " * "
            code += f"({self.children[1].build_code(0)})"
        elif op == "XOR":
            code += f"({self.children[0].build_code(0)})"
            code += " XOR "
            code += f"({self.children[1].build_code(0)})"
        elif op == "%+":
            code += f"({self.children[0].build_code(0)})"
            code += " %+ "
            code += f"({self.children[1].build_code(0)})"
        elif op == "++":
            code += f"({self.children[0].build_code(0)})"
            code += " ++ "
            code += f"({self.children[1].build_code(0)})"
        elif op == "tuple":
            code += "<"
            for i in range(len(self.children)):
                code += self.children[i].build_code(0)
                if i != len(self.children) - 1:
                    code += ", "
            code += ">"
        elif op == "function":
            if 0 != len(self.children):
                code += f"{self.attr['val']}("
                for i in range(len(self.children)):
                    code += self.children[i].build_code(0)
                    if i != len(self.children) - 1:
                        code += ", "
                code += ")"
            else:
                code += self.attr['val']
        else:
            code += f"Unknown({self.attr['val']})"
        return code

    def build_code(self, indent: int = 0) -> str:
        code = ""
        if self.prefix:
            code = self.prefix + "\n"
        if "theory" == self.type:
            code += self.__build_theory(indent)
        elif "rule" == self.type:
            code += self.__build_rule(indent)
        elif "facts" == self.type:
            code += self.__build_facts(indent)
        elif "fact" == self.type:
            code += self.__build_fact(indent)
        elif "functions" == self.type:
            code += self.__build_functions(indent)
        elif "function" == self.type:
            code += self.__build_function()
        elif "builtins" == self.type:
            code += self.__build_builtin(indent)
        elif "builtin_func" == self.type:
            code += self.__build_builtin_func()
        elif "macros" == self.type:
            code += self.__build_macros(indent)
        elif "macro" == self.type:
            code += self.__build_macro()
        elif "equations" == self.type:
            code += self.__build_equations(indent)
        elif "equation" == self.type:
            code += self.__build_equation(indent)
        elif "term" == self.type:
            code += self.__build_term()
        else:
            for child in self.children:
                code += child.build_code(indent)
        if self.suffix:
            code += self.suffix + "\n"

        return code

    def __str__(self) -> str:
        return self.build_code()

    def build_dict(self) -> dict:
        attr = copy.deepcopy(self.attr)
        for key in attr:
            if type(attr[key]) == SyntaxData:
                attr[key] = attr[key].build_dict()

        data = {
            "type": self.type,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "attr": attr,
            "children": []
        }
        for child in self.children:
            data['children'].append(child.build_dict())
        return data

    def expand_expr(self, term_equations: Dict[str, SyntaxData]) -> Tuple[bool, SyntaxData]:
        assert self.type == "term", "Invalid term data"
        if self.attr['op'] == "VarMsg":
            name = self.attr['val']
            if name in term_equations:
                return True, term_equations[name]
        return False, self

        # expanded = False
        # for i in range(len(self.children)):
        #     child_expanded, self.children[i] = self.children[i].expand_expr(
        #         term_equations)
        #     expanded = expanded or child_expanded
        # return expanded, self

    def term_match(self, value: SyntaxData) -> bool:
        term1 = self
        term2 = value

        assert term1.type == "term", "Invalid term data"
        assert term2.type == "term", "Invalid term data"

        if 'VarMsg' == term1.attr['op']:
            return True
        elif 'VarPub' == term1.attr['op'] or 'VarFresh' == term1.attr['op']:
            return term1.attr['op'] == term2.attr['op']
        elif 'Literal' == term1.attr['op'] or 'LiteralFresh' == term1.attr['op']:
            return term1.attr['op'] == term2.attr['op'] and term1.attr['val'] == term2.attr['val']
        else:
            if term1.attr['op'] != term2.attr['op'] or term1.attr['val'] != term2.attr['val']:
                return False
            elif len(term1.children) != len(term2.children):
                return False
            else:
                for i in range(len(term1.children)):
                    if not term1.children[i].term_match(term2.children[i]):
                        return False
                return True

    def term_eq(self, term: SyntaxData) -> bool:
        assert self.type == "term", "Invalid term data"
        assert term.type == "term", "Invalid term data"

        if term.attr['op'] == self.attr['op'] and term.attr['val'] == self.attr['val']:
            if 'VarMsg' == term.attr['op'] or 'VarPub' == term.attr['op'] or 'VarFresh' == term.attr['op'] \
                    or 'Literal' == term.attr['op'] or 'LiteralFresh' == term.attr['op']:
                return True
            else:
                if len(self.children) != len(term.children):
                    return False
                for i in range(len(term.children)):
                    if not self.children[i].term_eq(term.children[i]):
                        return False
                return True
        return False

    def term_contains(self, term: SyntaxData) -> bool:
        assert self.type == "term", "Invalid term data"
        assert term.type == "term", "Invalid term data"

        if self.term_eq(term):
            return True
        else:
            for child in self.children:
                if child.term_contains(term):
                    return True
        return False

    def merge_theory(self, theory: SyntaxData) -> None:
        def get_theory_functions(data: SyntaxData):
            functions = []
            if data.type == "function":
                functions.append(data)
            else:
                for child in data.children:
                    functions.extend(get_theory_functions(child))
            return functions

        def get_theory_equations(data: SyntaxData):
            equations = []
            if data.type == "equation":
                equations.append(data)
            else:
                for child in data.children:
                    equations.extend(get_theory_equations(child))
            return equations

        def get_theory_rules(data: SyntaxData):
            rules = []
            if data.type == "rule":
                rules.append(data)
            else:
                for child in data.children:
                    rules.extend(get_theory_rules(child))
            return rules

        if "theory" == self.type:
            rules = get_theory_rules(theory)
            self.children.extend(rules)
        
        if "functions" == self.type:
            functions = get_theory_functions(theory)
            self.children.extend(functions)
        
        if "equations" == self.type:
            equations = get_theory_equations(theory)
            self.children.extend(equations)
        
        for child in self.children:
            child.merge_theory(theory)


class TermData:
    def __init__(self, data: SyntaxData) -> None:
        self.raw_data: SyntaxData = data
        self.name: str = ""
        self.term_type: str = ""  # "variable" / "const" / "fresh"
        self.src_expr: SyntaxData = copy.deepcopy(data)
        self.__parse__()

    def __parse__(self):
        assert self.src_expr.type == "term", "Invalid term data"
        self.term_type = ""

        if self.src_expr.attr['op'] == "VarMsg":
            if self.src_expr.attr['val'] in CONST_FUNCTIONS:
                self.term_type = "const"
            else:
                self.term_type = "var"
        elif self.src_expr.attr['op'] == "VarPub":
            self.term_type = "const"
        elif self.src_expr.attr['op'] == "VarFresh":
            self.term_type = "fresh"
        elif self.src_expr.attr['op'] == "Literal":
            self.term_type = "const"
        elif self.src_expr.attr['op'] == "LiteralFresh":
            self.term_type = "fresh"

        if self.term_type == "":
            if self.src_expr.attr['op'] == "function" and len(self.src_expr.children) == 0:
                self.term_type = "const"
            else:
                self.term_type = "composite"
        else:
            self.name = self.src_expr.attr['val']

    def __eq__(self, value: TermData) -> bool:
        return self.src_expr.term_eq(value.src_expr)

    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)

    def __hash__(self) -> int:
        if self.name:
            return hash(self.name)
        else:
            return hash(self.src_expr.build_code())

    def __str__(self) -> str:
        return self.src_expr.build_code()

    def match(self, value: TermData) -> bool:
        return self.src_expr.term_match(value.src_expr)

    def contains(self, term: TermData) -> bool:
        return self.src_expr.term_contains(term.src_expr)

    def expand_expr(self, term_equations: Dict[str, SyntaxData]):
        expanded, src_expr = self.src_expr.expand_expr(term_equations)
        if expanded:
            orginal_name = self.name
            self.src_expr = src_expr
            self.__parse__()  # re-parse the term data
            self.name = orginal_name

    def atomic_terms(self) -> Set[TermData]:
        terms = set()
        if self.term_type != "composite":
            terms.add(self)
        else:
            for term in self.src_expr.children:
                terms = terms | TermData(term).atomic_terms()
        return terms


class FactData:
    def __init__(self, data: SyntaxData, term_equations: Dict[str, SyntaxData]) -> None:
        self.raw_data: SyntaxData = data
        self.name: str = ""
        self.terms: List[TermData] = []
        self.is_constant: bool = False
        self.term_equations = term_equations
        self.__parse__()

    def __parse__(self):
        assert self.raw_data.type == "fact", "Invalid fact data"
        self.name = self.raw_data.attr['name']
        self.is_constant = self.raw_data.attr['is_constant']
        for child in self.raw_data.children:
            term = TermData(child)
            # term.expand_expr(self.term_equations)
            self.terms.append(term)

    def __eq__(self, value: FactData) -> bool:
        if self.name != value.name and \
            not (self.name == 'In' and value.name == 'Out'
                 or self.name == 'Out' and value.name == 'In'):
            return False

        if len(self.terms) != len(value.terms):
            return False

        for i in range(len(self.terms)):
            if not self.terms[i].match(value.terms[i]):
                return False

        return True

    def atomic_terms(self) -> Set[TermData]:
        atomic_terms = set()
        for term in self.terms:
            atomic_terms = atomic_terms | term.atomic_terms()
        return atomic_terms


class RuleData:
    def __init__(self, data: SyntaxData) -> None:
        self.raw_data = data
        self.name: str = ""
        # { term_name -> (entropy, term) }
        self.marks: Dict[str, Tuple[str, SyntaxData]] = {}
        self.equations: Dict[str, SyntaxData] = {}
        self.promises: List[FactData] = []
        self.conclusions: List[FactData] = []
        self.__parse__()

    def __parse__(self):
        assert self.raw_data.type == "rule", "Invalid rule data"
        self.name = self.raw_data.attr['name']
        self.__parse_marks__()
        self.__parse_equations__()
        self.__parse_promises__()
        self.__parse_conclusions__()

    def __parse_marks__(self):
        if 'let' in self.raw_data.attr:
            let = self.raw_data.attr['let']
            if 'key' in let.attr:
                key = let.attr['key']
                for mark in key.children:
                    term = TermData(mark.children[0])
                    entropy = mark.attr['name']
                    self.marks[term.name] = (entropy, mark.children[0])

    def __parse_equations__(self):
        if 'let' in self.raw_data.attr:
            let = self.raw_data.attr['let']

            for equa in let.children:
                left = TermData(equa.children[0])
                right = equa.children[1]
                self.equations[left.name] = right

            # expanded = True
            # while expanded:
            #     expanded = False
            #     for left in self.equations:
            #         term_expanded, self.equations[left] = self.equations[left].expand_expr(self.equations)
            #         expanded = expanded or term_expanded

    def __parse_promises__(self):
        promise_facts = self.raw_data.children[0]
        for fact in promise_facts.children:
            fact_data = FactData(fact, self.equations)
            self.promises.append(fact_data)

    def __parse_conclusions__(self):
        conclusion_facts = self.raw_data.children[2]
        for fact in conclusion_facts.children:
            fact_data = FactData(fact, self.equations)
            self.conclusions.append(fact_data)

    def atomic_terms(self) -> Set[TermData]:
        atomic_terms = set()
        for fact in self.promises:
            atomic_terms = atomic_terms | fact.atomic_terms()
        for fact in self.conclusions:
            atomic_terms = atomic_terms | fact.atomic_terms()
        return atomic_terms


class SyntaxAnalyser:
    def __init__(self, data: SyntaxData) -> None:
        self.raw_data = data

        self.__parse_functions__(self.raw_data)

        self.rules: Dict[str, RuleData] = {}
        self.__parse_rules__(self.raw_data)

        # # { rule_name -> { fact_name -> [(src_rule, src_fact_index), ...] } }
        # self.rule_in_source: Dict[str, Dict[List[Tuple[str, int]]]] = {}
        # self.__analyse_promise_source__()  # analyse the source of promises

        # # { rule_name -> { fact_name -> { term_name -> (src_fact_index, src_term_index) } } }
        # self.rule_out_terms: Dict[str,
        #                           Dict[str, Dict[str, Tuple[int, int]]]] = {}
        # # analyse the terms in conclusions from which promise fact in this rule
        # self.__analyse_conclusion_terms__()

        # # { (rule_name, fact_index, term_index) -> { atomic_name -> [(src_rule, src_fact_index, src_term_index), ...] } }
        # self.term_src_trace: Dict[Tuple[str, int, int],
        #                           Dict[str, List[Tuple[str, int, int]]]] = {}
        # self.__analyse_term_source__()

    def __parse_functions__(self, data: SyntaxData):
        if data.type == "function":
            if data.attr['arity'] == 0:
                CONST_FUNCTIONS.append(data.attr['name'])
        else:
            for child in data.children:
                self.__parse_functions__(child)

    def __parse_rules__(self, data: SyntaxData):
        if data.type == "rule":
            rule = RuleData(data)
            self.rules[rule.name] = rule
        else:
            for child in data.children:
                self.__parse_rules__(child)

    def __analyse_promise_source__(self):
        for rule1_name in self.rules:
            rule1 = self.rules[rule1_name]
            fact_src_map = {}
            for prom_fact in rule1.promises:
                fact_src = []
                for rule2_name in self.rules:
                    rule2 = self.rules[rule2_name]
                    for i in range(len(rule2.conclusions)):
                        if prom_fact == rule2.conclusions[i]:
                            fact_src.append((rule2_name, i))
                fact_src_map[prom_fact.name] = fact_src
            self.rule_in_source[rule1_name] = fact_src_map

    def __analyse_conclusion_terms__(self):
        for rule_name in self.rules:
            rule = self.rules[rule_name]
            fact_map = {}
            for fact_index in range(len(rule.conclusions)):
                fact = rule.conclusions[fact_index]
                term_map = {}
                for term in fact.terms:
                    for atomic_term in term.atomic_terms():
                        if atomic_term.name in term_map:
                            continue
                        if atomic_term.term_type == "const":
                            continue

                        for promise in rule.promises:
                            for term_index in range(len(promise.terms)):
                                promise_term = promise.terms[term_index]
                                if promise_term.contains(atomic_term):
                                    term_map[atomic_term.name] = (
                                        fact_index, term_index)
                                    break
                        assert atomic_term.name in term_map, "Term not found in promises"
                fact_map[fact.name] = term_map
            self.rule_out_terms[rule_name] = fact_map

    def __analyse_term_source__(self):
        for rule_name in self.rules:
            rule = self.rules[rule_name]
            for conclusion_index, conclusion_fact in enumerate(rule.conclusions):
                for term_index, term in enumerate(conclusion_fact.terms):
                    term_label = (rule_name, conclusion_index, term_index)
                    term_source = {}
                    for atomic_term in term.atomic_terms():
                        if atomic_term.term_type == "const":
                            continue

                        atomic_source = []
                        source_in_rule = self.rule_out_terms[rule_name][conclusion_fact.name][atomic_term.name]
                        source_fact = rule.promises[source_in_rule[0]]
                        source_term_index = source_in_rule[1]
                        if source_fact.name == 'Fr':
                            continue

                        source_between_rules = self.rule_in_source[rule_name][source_fact.name]
                        for src_rule, src_fact_index in source_between_rules:
                            src_label = (src_rule, src_fact_index,
                                         source_term_index)
                            atomic_source.append(src_label)

                        term_source[atomic_term.name] = atomic_source
                    self.term_src_trace[term_label] = term_source

    def generate_entropy_theory(self, util_models) -> SyntaxData:
        def new_terms_combine(terms: List[SyntaxData]) -> SyntaxData:
            if len(terms) == 1:
                return terms[0]
            else:
                term_combined = SyntaxData()
                term_combined.type = "term"
                term_combined.attr['op'] = "function"
                term_combined.attr['val'] = "combine"
                term_combined.children.append(terms[0])
                term_combined.children.append(new_terms_combine(terms[1:]))
                return term_combined

        def new_fact(fact_name: str, terms: List[SyntaxData] = [], constant: bool = False) -> SyntaxData:
            fact = SyntaxData()
            fact.type = "fact"
            fact.attr['name'] = fact_name
            fact.attr['is_constant'] = constant
            fact.children = terms
            return fact

        def do_facts_contain_term(facts: List[FactData], term: TermData) -> bool:
            def do_fact_contain_term(fact: FactData, term: TermData) -> bool:
                for fact_term in fact.terms:
                    if fact_term.contains(term):
                        return True
                    elif fact_term.raw_data.term_contains(term.raw_data):
                        return True
                return False

            for fact in facts:
                if do_fact_contain_term(fact, term):
                    return True
            return False

        def get_derived_terms(rule: RuleData, origin_terms: List[TermData], seen=None) -> List[Tuple[List[TermData], TermData]]:
            if seen is None:
                seen = set()
            terms: List[TermData] = []
            for t in origin_terms:
                if t.term_type == "composite" and t.src_expr.attr['op'] == "tuple":
                    for child in t.src_expr.children:
                        term = TermData(child)
                        terms.append(term)
                else:
                    terms.append(t)

            cleand_terms: List[TermData] = []
            for term in terms:
                if term.term_type == "const":
                    continue
                elif do_facts_contain_term(rule.promises, term):
                    continue
                elif term.term_type == "composite":
                    cleand_terms.append(term)
                else:
                    if term.name in rule.equations:
                        t = copy.deepcopy(term)
                        t.expand_expr(rule.equations)
                        cleand_terms.append(t)

            derived_terms: List[Tuple[List[TermData], TermData]] = []
            for term in cleand_terms:
                key = term.src_expr.build_code()
                if key in seen:
                    continue
                seen.add(key)
                atomic_terms = term.atomic_terms()
                atomic_terms = [t for t in atomic_terms if t.term_type != "const"]
                derived_terms.append((atomic_terms, term))
                derived_terms.extend(get_derived_terms(rule, atomic_terms, seen))

            # remove duplicate terms
            derived_terms_names = set([term.name for _, term in derived_terms])
            derived_terms = [term for term in derived_terms if term[1].name in derived_terms_names]

            return derived_terms

        theory_data = copy.deepcopy(self.raw_data)
        rule_data = [
            raw for raw in theory_data.children[0].children if raw.type == "rule"]

        for raw in rule_data:
            raw_conclusions = raw.children[2]
            rule_name = raw.attr['name']
            rule = self.rules[rule_name]

            # for raw_conclusion in raw_conclusions.children:
            #     if raw_conclusion.attr['name'] == 'Out':
            #         new_crack = new_fact("Crack", raw_conclusion.children, True)
            #         raw_conclusions.children.append(new_crack)

            derived_terms: List[Tuple[List[TermData], TermData]] = []
            for concl in rule.conclusions:
                derived_terms.extend(get_derived_terms(rule, concl.terms))

            # remove duplicate terms
            derived_terms_names = set([term.name for _, term in derived_terms])
            derived_terms = [term for term in derived_terms if term[1].name in derived_terms_names]
            for derived in derived_terms:
                atomic_terms, term = derived
                if len(atomic_terms) == 1:
                    derive_fact = new_fact("MDerive0", [atomic_terms[0].raw_data, term.raw_data], True)
                    raw_conclusions.children.append(derive_fact)
                elif len(atomic_terms) > 1:
                    atomic_terms = [t.raw_data for t in atomic_terms]
                    derive_fact = new_fact("MDerive0", [new_terms_combine(atomic_terms), term.raw_data], True)
                    raw_conclusions.children.append(derive_fact)

            for term_name in rule.marks:
                entropy, term = rule.marks[term_name]
                entropy_fact = new_fact(f"Entropy{entropy}", [term], True)
                raw_conclusions.children.append(entropy_fact)

        for model in util_models:
            model_data = SyntaxData(file=model)
            theory_data.merge_theory(model_data)

        return theory_data
