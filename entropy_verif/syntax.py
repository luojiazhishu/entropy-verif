import logging
import os
import ctypes
from typing import Generator, List
import itertools
import copy

libtamarin = ctypes.CDLL('./build/libtamarin.so')
libtamarin.tamarin_parse.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
libtamarin.tamarin_parse.restype = ctypes.c_int32


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
        outfile = "/tmp/.output.tmp"
        ret = libtamarin.tamarin_parse(infile.encode(), outfile.encode())

        result = None
        if 0 == ret:
            with open(outfile, 'r') as f:
                result = f.read()
            result = result.replace("\n", "\\n")
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
                f"rule {self.attr['name']} [color=#{self.attr['attrs'].attr['color']}]:", indent)
        else:
            code += self.__build_line(
                f"rule {self.attr['name']}:", indent)

        if 'let' in self.attr:
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


class SyntaxExpander:
    def __init__(self, data: SyntaxData) -> None:
        self.data = data
        self.rule_fact_term = {}
        self.terms = {}
        self.expanded_facts = {}

    def rule_iter(self, data: SyntaxData) -> Generator['SyntaxData', None, None]:
        if "rule" == data.type:
            yield data
        else:
            for child in data.children:
                yield from self.rule_iter(child)

    def fact_iter(self, data: SyntaxData) -> Generator['SyntaxData', None, None]:
        if "fact" == data.type:
            yield data
        else:
            for child in data.children:
                yield from self.fact_iter(child)

    def term_iter(self, data: SyntaxData) -> Generator['SyntaxData', None, None]:
        if "term" == data.type and (
            data.attr['op'] == "VarMsg" or
            data.attr['op'] == "VarPub" or
            data.attr['op'] == "VarFresh" or
            data.attr['op'] == "Literal" or
            data.attr['op'] == "LiteralFresh"
        ):
            yield data
        else:
            for child in data.children:
                yield from self.term_iter(child)

    def variable_term_iter(self, data: SyntaxData) -> Generator['SyntaxData', None, None]:
        if "term" == data.type and (
            data.attr['op'] == "VarMsg" or
            data.attr['op'] == "VarFresh"
        ):
            yield data
        else:
            for child in data.children:
                yield from self.variable_term_iter(child)

    def is_basics_term(self, data: SyntaxData) -> bool:
        return "term" == data.type and (
            data.attr['op'] == "VarMsg" or
            data.attr['op'] == "VarPub" or
            data.attr['op'] == "VarFresh" or
            data.attr['op'] == "Literal" or
            data.attr['op'] == "LiteralFresh"
        )

    def equation_iter(self, data: SyntaxData) -> Generator['SyntaxData', None, None]:
        if "equation" == data.type:
            yield data
        else:
            for child in data.children:
                yield from self.equation_iter(child)

    def mark_iter(self, data: SyntaxData) -> Generator['SyntaxData', None, None]:
        if "key_mark" == data.type:
            yield data
        else:
            for child in data.children:
                yield from self.mark_iter(child)

    def get_rule_data(self):
        # structure rules data
        rule_fact_term = {}
        for rule in self.rule_iter(self.data):
            rule_name = rule.attr['name']
            rule_fact_term[rule_name] = {
                "data": rule,
                "promise": {},
                'pfnames': [],
                'ptermnames': [],
                "conclusion": {},
                'cfnames': [],
                'ctermnames': [],
                "equations": {},
                "keymarks": {}
            }

            # promise facts
            for fact in self.fact_iter(rule.children[0]):
                fact_name = fact.attr['name']
                rule_fact_term[rule_name]['pfnames'].append(fact_name)

                fact_names = rule_fact_term[rule_name]['promise']
                same_name = [x for x in fact_names if x.startswith(fact_name)]
                fact_name = f"{fact_name}_{len(same_name)}"
                rule_fact_term[rule_name]['promise'][fact_name] = {
                    'data': fact,
                    'terms': {}
                }

                for term in self.variable_term_iter(fact):
                    term_name = term.attr['val']
                    rule_fact_term[rule_name]['ptermnames'].append(term_name)
                    rule_fact_term[rule_name]['promise'][fact_name]['terms'][term_name] = {
                        'data': term
                    }

            # conclusion facts
            for fact in self.fact_iter(rule.children[2]):
                fact_name = fact.attr['name']
                rule_fact_term[rule_name]['cfnames'].append(fact_name)

                fact_names = rule_fact_term[rule_name]['conclusion']
                same_name = [x for x in fact_names if x.startswith(fact_name)]
                fact_name = f"{fact_name}_{len(same_name)}"

                rule_fact_term[rule_name]['conclusion'][fact_name] = {
                    'data': fact,
                    'terms': {}
                }

                for term in self.variable_term_iter(fact):
                    term_name = term.attr['val']
                    rule_fact_term[rule_name]['ctermnames'].append(term_name)
                    rule_fact_term[rule_name]['conclusion'][fact_name]['terms'][term_name] = {
                        'data': term
                    }

            if 'let' in rule.attr:
                let = rule.attr['let']
                # equations
                for equation in self.equation_iter(let):
                    term_name = equation.children[0].attr['val']
                    rule_fact_term[rule_name]['equations'][term_name] = {
                        'data': equation,
                        'left': equation.children[0],
                        'right': equation.children[1]
                    }

                if 'key' in let.attr:
                    key = let.attr['key']
                    # keymarks
                    for mark in self.mark_iter(key):
                        mark_name = mark.attr['name']
                        term_name = mark.children[0].attr['val']
                        rule_fact_term[rule_name]['keymarks'][term_name] = {
                            'data': mark,
                            'mark': mark_name
                        }

        self.rule_fact_term = rule_fact_term

    def trace_fact_term(self, term: str, fact: SyntaxData, tracing: list) -> list:
        matched = []
        for rule in self.rule_fact_term:
            rule_data = self.rule_fact_term[rule]
            fact_name = fact.attr['name']
            fact_name = fact_name if fact_name != "In" else "Out"
            if fact_name in rule_data['cfnames']:
                matched_fnames = [x for x in rule_data['conclusion']
                                  if x.startswith(fact_name)]
                for m_fname in matched_fnames:
                    fact_data = rule_data['conclusion'][m_fname]['data']
                    if FACT_MATCH(fact, fact_data):
                        matched_term = get_matched_term(term, fact, fact_data)
                        assert matched_term is not None, f"ERROR: term {term} not found"

                        if f"{rule}-{m_fname}-{matched_term.build_code()}" in tracing:
                            continue

                        tracing.append(f"{rule}-{m_fname}-{matched_term.build_code()}")

                        if self.is_basics_term(matched_term):
                            matched_data = self.trace_rule_term(matched_term.attr['val'], rule, tracing)
                        else:
                            matched_data = self.trace_rule_composite_term(matched_term, rule, tracing)

                        if matched_data is not None:
                            matched.append({
                                'equal': matched_term,
                                'terms': [matched_data]
                            })
                        tracing.pop(-1)
        return matched

    def trace_rule_composite_term(self, term: SyntaxData, rule: str, tracing: list) -> dict:
        term_from = []
        term_name = term.build_code()
        if term_name in self.terms:
            return self.terms[term_name]

        for m_term in self.term_iter(term):
            if 'VarFresh' == m_term.attr['op'] or 'VarMsg' == m_term.attr['op']:
                res = self.trace_rule_term(m_term.attr['val'], rule, tracing)
            else:
                res = {
                    'term': m_term.build_code(),
                    'rule': rule,
                    'mark': 'Zero'
                }
            if res is None:
                return None
            term_from.append(res)

        if len(term_from) > 0:
            matched_data = {
                'term': term_name,
                'rule': rule,
                'from': [
                    {
                        'equal': term,
                        'terms': term_from
                    }
                ]
            }
            self.terms[f"{rule}.{term_name}"] = matched_data
            return matched_data
        else:
            return None

    def trace_rule_term(self, term: str, rule: str, tracing: list) -> dict:
        rule_term = f"{rule}.{term}"
        if rule_term in self.terms:
            return self.terms[rule_term]

        if rule_term == 'oracle.LTK':
            pass

        find_in_equations = True
        if term in self.rule_fact_term[rule]['ctermnames'] and \
                term in self.rule_fact_term[rule]['ptermnames']:
            find_in_equations = False

        assert rule in self.rule_fact_term, f"ERROR: rule {rule} not found"
        rule_data = self.rule_fact_term[rule]

        term_data = {
            'term': term,
            'rule': rule,
        }

        if term.startswith("'") and term.endswith("'") or term.startswith('$'):
            term_data['mark'] = 'Zero'
            self.terms[rule_term] = term_data
            return term_data

        if term in rule_data['keymarks']:
            term_data['mark'] = rule_data['keymarks'][term]['mark']

        if find_in_equations and term in rule_data['equations']:
            equa_data = rule_data['equations'][term]

            term_from = {}
            for equa_term in self.term_iter(equa_data['right']):
                e_t_name = equa_term.attr['val']
                if "VarPub" == equa_term.attr['op'] \
                        or "Literal" == equa_term.attr['op'] \
                        or "LiteralFresh" == equa_term.attr['op']:
                    term_from[e_t_name] = [{'term': e_t_name, 'rule': rule, 'mark': 'Zero'}]
                    continue
                for f in rule_data['promise']:
                    if e_t_name in rule_data['promise'][f]['terms']:
                        if not f.startswith('Fr'):
                            f_data = rule_data['promise'][f]['data']
                            term_from[e_t_name] = self.trace_fact_term(e_t_name, f_data, tracing)
                if e_t_name not in term_from:
                    res = self.trace_rule_term(e_t_name, rule, tracing)
                    if res is None:
                        return None
                    term_from[e_t_name] = [res]

            nested_from = [term_from[t] for t in term_from]
            term_data['from'] = [{'terms': list(x), 'equal': equa_data['right']} for x in itertools.product(*nested_from)]
            if len(term_data['from']) == 0:
                return None
            self.terms[rule_term] = term_data
            return term_data

        else:
            for fact in rule_data['promise']:
                if term in rule_data['promise'][fact]['terms']:
                    if fact.startswith('Fr'):
                        # if Fresh isn't marked, then consider it as Chaotic
                        if 'mark' not in term_data:
                            term_data['mark'] = 'Chaotic'
                    else:
                        fact_data = rule_data['promise'][fact]['data']
                        from_data = self.trace_fact_term(term, fact_data, tracing)
                        if len(from_data) == 0:
                            return None
                        term_data['from'] = from_data
                    self.terms[rule_term] = term_data
                    return term_data
            return None

    def trace_terms(self):
        def traverse_terms_in_fact(fact_data: SyntaxData):
            for term in fact_data.children:
                if self.is_basics_term(term):
                    self.trace_rule_term(term.attr['val'], rule, [f"{rule}-{fact}-{term.attr['val']}"])
                else:
                    term_name = term.build_code()
                    self.trace_rule_composite_term(term, rule, [f"{rule}-{fact}-{term_name}"])

        for rule in self.rule_fact_term:
            for fact in self.rule_fact_term[rule]['conclusion']:
                fact_data = self.rule_fact_term[rule]['conclusion'][fact]['data']
                traverse_terms_in_fact(fact_data)
            for fact in self.rule_fact_term[rule]['promise']:
                fact_data = self.rule_fact_term[rule]['promise'][fact]['data']
                traverse_terms_in_fact(fact_data)

    def analyze(self):
        self.get_rule_data()
        self.trace_terms()

    def out_terms(self, rule: str) -> List[SyntaxData]:
        terms: List[SyntaxData] = []  # only appears in the conclusion not in promise
        cterms: List[SyntaxData] = []  # conclusion terms
        pterms: List[SyntaxData] = []  # promise terms

        for fact in self.rule_fact_term[rule]['conclusion']:
            cfact = self.rule_fact_term[rule]['conclusion'][fact]['data']
            cterms += cfact.children

        for fact in self.rule_fact_term[rule]['promise']:
            pfact = self.rule_fact_term[rule]['promise'][fact]['data']
            pterms += pfact.children

        def is_in_promise(t: SyntaxData) -> bool:
            for pt in pterms:
                if TERM_EQUAL(t, pt):
                    return True
            return False

        for ct in cterms:
            if not is_in_promise(ct):
                terms.append(ct)

        return terms

    def term_label(self, term) -> str:
        if type(term) == SyntaxData:
            term_name = term.build_code()
        else:
            term_name = term
        term_name = term_name.replace("'", "")
        term_name = term_name.replace("$", "p")
        term_name = term_name.replace("~", "f")
        term_name = term_name.replace(":", "_")
        term_name = term_name.replace("`", "_")
        term_name = term_name.replace("(", "_")
        term_name = term_name.replace(")", "_")
        term_name = term_name.replace("<", "_")
        term_name = term_name.replace(">", "_")
        term_name = term_name.replace(",", "_")
        term_name = term_name.replace(" ", "")
        if term_name.startswith('_'):
            term_name = 't' + term_name
        return term_name

    def new_entropy_mark_equation(self, term_name: str, mark: str) -> SyntaxData:
        equation = SyntaxData()
        equation.type = 'equation'

        left = SyntaxData()
        left.type = 'term'
        left.attr['op'] = "VarMsg"
        left.attr['val'] = f"H_{term_name}"

        right = SyntaxData()
        right.type = 'term'
        right.attr['op'] = "function"
        right.attr['val'] = mark

        equation.children = [left, right]
        return equation

    def new_entropy_combine_term_val(self, from_terms: List[dict]) -> str:
        if len(from_terms) == 1:
            return f"H_{from_terms[0]}"
        else:
            arg1 = f"H_{from_terms[0]}"
            arg2 = self.new_entropy_combine_term_val(from_terms[1:])
            return f"combine({arg1}, {arg2})"

    def new_entropy_combine_equation(self, term_name: str, from_terms: List[dict]) -> SyntaxData:
        equation = SyntaxData()
        equation.type = 'equation'

        left = SyntaxData()
        left.type = 'term'
        left.attr['op'] = "VarMsg"
        left.attr['val'] = f"H_{term_name}"

        from_labels = [self.term_label(t['term']) for t in from_terms]

        right = SyntaxData()
        right.type = 'term'
        right.attr['op'] = "function"
        right.attr['val'] = self.new_entropy_combine_term_val(from_labels)

        equation.children = [left, right]
        return equation

    def new_term_equation(self, left_term: str, right: SyntaxData) -> SyntaxData:
        equation = SyntaxData()
        equation.type = 'equation'

        left = SyntaxData()
        left.type = 'term'
        left.attr['op'] = "VarMsg"
        left.attr['val'] = left_term

        equation.children = [left, right]
        return equation

    def new_entropy_fact(self, term_id: str, term) -> SyntaxData:
        fact = SyntaxData()
        fact.type = 'fact'
        fact.attr['name'] = 'Entropy'
        fact.attr['is_constant'] = False

        term1 = SyntaxData()
        term1.type = 'term'
        term1.attr['op'] = "Literal"
        term1.attr['val'] = f"'{term_id.replace("'", '')}'"

        if type(term) == SyntaxData:
            term_name = term.build_code()
        else:
            term_name = term
        term_label = self.term_label(term_name)

        term2 = SyntaxData()
        term2.type = 'term'
        term2.attr['op'] = "VarMsg"
        term2.attr['val'] = f"H_{term_label}"

        term3 = SyntaxData()
        term3.type = 'term'
        term3.attr['op'] = "VarMsg"
        term3.attr['val'] = term_name

        fact.children = [term1, term2, term3]
        return fact

    def new_fresh_fact(self, term_id: str, term_name: str) -> SyntaxData:
        fact = SyntaxData()
        fact.type = 'fact'
        fact.attr['name'] = 'Fresh2Ent'
        fact.attr['is_constant'] = True

        term1 = SyntaxData()
        term1.type = 'term'
        term1.attr['op'] = "Literal"
        term1.attr['val'] = f"'{term_id}'"

        term2 = SyntaxData()
        term2.type = 'term'
        term2.attr['op'] = "VarFresh"
        term2.attr['val'] = term_name

        fact.children = [term1, term2]
        return fact

    def expand_rule(self, data: SyntaxData) -> List[SyntaxData]:
        assert "rule" == data.type, "ERROR: data is not rule"
        rule = data.attr['name']
        out_terms = self.out_terms(rule)
        if len(out_terms) == 0:
            return []

        out_term_names = [t.build_code() for t in out_terms]
        out_term_names = list(set(out_term_names))
        out_term_data = {t.build_code(): t for t in out_terms}

        new_rules = []

        fresh_terms = []
        for t in self.variable_term_iter(data.children[0]):
            if t.type == 'term' and t.attr['op'] == "VarFresh":
                tname = t.attr['val']
                if 'mark' in self.terms[f"{rule}.{tname}"]:
                    fresh_terms.append(tname)
        terminal_terms = []
        non_terminal_terms = []
        for t in out_term_names:
            if 'from' not in self.terms[f"{rule}.{t}"]:
                if t not in fresh_terms:
                    terminal_terms.append(t)
            else:
                non_terminal_terms.append(t)
        non_terminal_froms = [self.terms[f"{rule}.{t}"]['from'] for t in non_terminal_terms]

        combinations = list(itertools.product(*non_terminal_froms))
        non_terminal_groups = [dict(zip(non_terminal_terms, combination)) for combination in combinations]

        for index in range(len(non_terminal_groups)):
            new_rule = SyntaxData()
            new_rule.type = 'rule'
            new_rule.attr['name'] = f"entropy_{rule}_{index}"

            new_equations: List[SyntaxData] = []
            new_promises: List[SyntaxData] = []
            new_conclusions: List[SyntaxData] = []

            # process fresh term
            for term in fresh_terms:
                term_id = f"{rule}.{term}"
                term_data = self.terms[term_id]
                if 'mark' in term_data:
                    term_label = self.term_label(term)

                    fresh_fact = self.new_fresh_fact(term_id, term)
                    new_promises.append(fresh_fact)
                    data.children[2].children.append(fresh_fact)

                    entropy_fact = self.new_entropy_fact(term_id, term)
                    new_conclusions.append(entropy_fact)

                    entropy_equa = self.new_entropy_mark_equation(term_label,  term_data['mark'])
                    new_equations.append(entropy_equa)

            # process terminal terms
            for term in terminal_terms:
                term_id = f"{rule}.{term}"
                term_label = self.term_label(term)
                term_data = self.terms[term_id]
                term_syntax_data = out_term_data[term]

                entropy_fact = self.new_entropy_fact(term_id, term_syntax_data)
                new_conclusions.append(entropy_fact)

                entropy_equa = self.new_entropy_mark_equation(term_label, term_data['mark'])
                new_equations.append(entropy_equa)

            # process non-terminal terms
            group = non_terminal_groups[index]
            for term in group:
                term_id = f"{rule}.{term}"
                term_label = self.term_label(term)
                term_data = self.terms[term_id]
                term_syntax_data = out_term_data[term]

                term_name = self.term_label(term_syntax_data)
                from_terms = group[term]['terms']
                equa_data = group[term]['equal']

                new_equations.append(self.new_term_equation(term_name, equa_data))
                if 'mark' in term_data:
                    new_equations.append(self.new_entropy_mark_equation(term_label, term_data['mark']))
                else:
                    new_equations.append(self.new_entropy_combine_equation(term_label, from_terms))
                    for from_t in from_terms:
                        if from_t['rule'] != rule:
                            from_id = f"{from_t['rule']}.{from_t['term']}"
                            new_promises.append(self.new_entropy_fact(from_id, from_t['term']))
                new_conclusions.append(self.new_entropy_fact(term_id, term_name))

            promise_facts = SyntaxData()
            promise_facts.type = 'facts'
            promise_facts.attr['is_action'] = False
            promise_facts.children = new_promises

            conclusion_facts = SyntaxData()
            conclusion_facts.type = 'facts'
            conclusion_facts.attr['is_action'] = False
            conclusion_facts.children = new_conclusions

            action_facts = SyntaxData()
            action_facts.type = 'facts'
            action_facts.attr['is_action'] = True

            let = SyntaxData()
            let.type = 'rule_let'
            let.children = new_equations

            new_rule.attr['let'] = let
            new_rule.children = [promise_facts, action_facts, conclusion_facts]

            new_rules.append(new_rule)

        return new_rules

    def syntax_expand(self, data: SyntaxData = None):
        if None == data:
            data = self.data

        if 'theory' == data.type:
            new_rules = []
            for child in data.children:
                if 'rule' == child.type:
                    new_rules += self.expand_rule(child)
            data.children += new_rules
        else:
            for child in data.children:
                self.syntax_expand(child)


def FACT_MATCH(fact1: SyntaxData, fact2: SyntaxData) -> bool:
    if 'fact' != fact1.type or 'fact' != fact2.type:
        return False

    if fact1.attr['name'] != fact2.attr['name'] and (fact1.attr['name'] != "In" or fact2.attr['name'] != "Out"):
        return False

    if len(fact1.children) != len(fact2.children):
        return False

    for i in range(len(fact1.children)):
        t1 = fact1.children[i]
        t2 = fact2.children[i]
        if not TERM_MATCH(t1, t2):
            return False

    return True


def TERM_MATCH(term1: SyntaxData, term2: SyntaxData) -> bool:
    if 'term' != term1.type or 'term' != term2.type:
        return False

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
                if not TERM_MATCH(term1.children[i], term2.children[i]):
                    return False
            return True


def TERM_EQUAL(term1: SyntaxData, term2: SyntaxData) -> bool:
    if 'term' != term1.type or 'term' != term2.type:
        return False

    if term1.attr['op'] != term2.attr['op'] and term1.attr['val'] != term2.attr['val']:
        return False
    else:
        if len(term1.children) != len(term2.children):
            return False
        else:
            for i in range(len(term1.children)):
                if not TERM_EQUAL(term1.children[i], term2.children[i]):
                    return False
            return True


def get_matched_term(term: str, source: SyntaxData, target: SyntaxData) -> SyntaxData:
    def find_children():
        assert len(source.children) == len(target.children), "ERROR: fact children not match"
        for i in range(len(source.children)):
            mached = get_matched_term(term, source.children[i], target.children[i])
            if mached is not None:
                return mached
        return None

    if 'term' == source.type or 'term' == target.type:
        if term == source.attr['val']:
            return target
        else:
            return find_children()
    elif 'fact' == source.type or 'fact' == target.type:
        return find_children()
    else:
        return None
