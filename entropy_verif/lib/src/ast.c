#include "ast.h"
#include "global.h"
#include "utils.h"
#include <stdarg.h>
#include <string.h>

extern void* DEBUG_NODES[];
extern int DEBUG_NODES_CNT;
/****************************************************************
 *  Abstract Syntax Tree Operation Functions
 ****************************************************************/

/**
 * @description: New an AST node
 * @return {AstNode*}
 */
AstNode* ast_node_new(BlockType type)
{
    AstNode* node = (AstNode*)calloc(1, sizeof(AstNode));
    node->type = type;
    return node;
}

/**
 * @description: Free an AST node
 * @param {AstNode*} node
 * @return {*}
 */
void ast_node_free(AstNode* node)
{
    free(node);
}

/**
 * @description: Add a sibling to the node
 * @param {AstNode*} node
 * @param {AstNode*} sibling
 * @return {*}
 */
void ast_node_add_sibling(AstNode* node, AstNode* sibling)
{
    if (node == NULL) {
        return;
    }

    while (node->sibling != NULL) {
        node = node->sibling;
    }

    node->sibling = sibling;
}

void ast_node_insert_sibling(AstNode* node, AstNode* sibling)
{
    if (node == NULL) {
        return;
    }

    sibling->sibling = node->sibling;
    node->sibling = sibling;
}

AstNode* ast_tree_copy(AstNode* node)
{
    if (node == NULL) {
        return NULL;
    }

    AstNode* new = ast_node_new(node->type);

    AstNode* child = node->children;
    while (child) {
        ast_node_add_child(new, ast_tree_copy(child));
        child = child->sibling;
    }

    new->attr = node->attr;
    switch (node->type) {
    case BLK_Reserve:
    case BLK_Theory:
    case BLK_BuiltInFunc:
    case BLK_Function:
    case BLK_Term:
    case BLK_MacroParam:
    case BLK_RuleFactAnnote:
    case BLK_RuleModulo:
        if (node->attr.reserve.str) {
            new->attr.reserve.str = copy_string(node->attr.reserve.str);
        }
        break;
    case BLK_Macro:
    case BLK_RuleFact:
        if (node->attr.macro.name) {
            new->attr.macro.name = copy_string(node->attr.macro.name);
        }
        if (node->attr.macro.param) {
            new->attr.macro.param = ast_tree_siblings_copy(node->attr.macro.param);
        }
        break;
    case BLK_Rule:
        if (node->attr.rule.name) {
            new->attr.rule.name = copy_string(node->attr.rule.name);
        }
        if (node->attr.rule.let) {
            new->attr.rule.let = ast_tree_copy(node->attr.rule.let);
        }
        if (node->attr.rule.modulo) {
            new->attr.rule.modulo = ast_tree_copy(node->attr.rule.modulo);
        }
        if (node->attr.rule.attrs) {
            new->attr.rule.attrs = ast_tree_copy(node->attr.rule.attrs);
        }
    case BLK_RuleLet:
        if (node->attr.rule_let.key) {
            new->attr.rule_let.key = ast_tree_copy(node->attr.rule_let.key);
        }
        break;
    default:
        break;
    }

    return new;
}

AstNode* ast_tree_siblings_copy(AstNode* node)
{
    if (node == NULL) {
        return NULL;
    }

    AstNode* new = ast_tree_copy(node);
    AstNode* silbing = node->sibling;
    new->sibling = NULL;

    while (silbing) {
        ast_node_add_sibling(new, ast_tree_copy(silbing));
        silbing = silbing->sibling;
    }

    return new;
}

void ast_tree_destory(AstNode* node)
{
    if (node == NULL) {
        return;
    }

    AstNode* next;
    AstNode* child = node->children;
    while (child) {
        next = child->sibling;
        ast_tree_destory(child);
        child = next;
    }

    switch (node->type) {
    case BLK_Reserve:
    case BLK_Theory:
    case BLK_BuiltInFunc:
    case BLK_Function:
    case BLK_Term:
    case BLK_MacroParam:
    case BLK_RuleFactAnnote:
    case BLK_RuleModulo:
        if (node->attr.reserve.str) {
            free(node->attr.reserve.str);
        }
        break;
    case BLK_Macro:
    case BLK_RuleFact:
        if (node->attr.macro.name) {
            free(node->attr.macro.name);
        }
        if (node->attr.macro.param) {
            child = node->attr.macro.param;
            while (child) {
                next = child->sibling;
                ast_tree_destory(child);
                child = next;
            }
        }
        break;
    case BLK_Rule:
        if (node->attr.rule.name) {
            free(node->attr.rule.name);
        }
        if (node->attr.rule.let) {
            ast_tree_destory(node->attr.rule.let);
        }
        if (node->attr.rule.modulo) {
            ast_tree_destory(node->attr.rule.modulo);
        }
        if (node->attr.rule.attrs) {
            ast_tree_destory(node->attr.rule.attrs);
        }
        break;
    case BLK_RuleLet:
        if (node->attr.rule_let.key) {
            ast_tree_destory(node->attr.rule_let.key);
        }
        break;
    default:
        break;
    }

    free(node);
}

/**
 * @description: Add a child to the node
 * @param {AstNode*} node
 * @param {AstNode*} child
 * @return {*}
 */
void ast_node_add_child(AstNode* node, AstNode* child)
{
    if (node == NULL) {
        return;
    }

    if (node->children == NULL) {
        node->children = child;
    } else {
        ast_node_add_sibling(node->children, child);
    }
}

/****************************************************************
 *  AST Tree Print Functions
 ****************************************************************/
void _print_tree(AstNode* root, int depth, bool is_last, char* prefix, FILE* file);

void _print_tree(AstNode* root, int depth, bool is_last, char* prefix, FILE* file)
{
    if (root == NULL) {
        return;
    }

    for (int i = 0; i < depth; i++) {
        if (i == depth - 1) {
            if (is_last) {
                fprintf(file, "└── ");
            } else {
                fprintf(file, "├── ");
            }
        } else {
            if (prefix[i]) {
                fprintf(file, "│   ");
            } else {
                fprintf(file, "    ");
            }
        }
    }

    (root->type) == BLK_Root                 ? fprintf(file, "Root\n")
        : (root->type) == BLK_Reserve        ? fprintf(file, "Reserve[%lu bytes]\n", strlen(root->attr.reserve.str))
        : (root->type) == BLK_Theory         ? fprintf(file, "Theory[%s]\n", root->attr.theory.name)
        : (root->type) == BLK_Rule           ? fprintf(file, "Rule[%s]\n", root->attr.rule.name)
        : (root->type) == BLK_Functions      ? fprintf(file, "Functions\n")
        : (root->type) == BLK_Equations      ? fprintf(file, "Equations\n")
        : (root->type) == BLK_BuiltIn        ? fprintf(file, "BuiltIn\n")
        : (root->type) == BLK_Macros         ? fprintf(file, "Macros\n")
        : (root->type) == BLK_Function       ? fprintf(file, "Function[%s/%d]\n", root->attr.func.name, root->attr.func.arity)
        : (root->type) == BLK_Equation       ? fprintf(file, "Equation\n")
        : (root->type) == BLK_Term           ? fprintf(file, "Term[%s:%s]\n", TERM_TYPE_NAME(root->attr.term.type), root->attr.term.val)
        : (root->type) == BLK_BuiltInFunc    ? fprintf(file, "BuiltInFunc[%s]\n", root->attr.builtin.str)
        : (root->type) == BLK_Macro          ? fprintf(file, "Macro[%s]\n", root->attr.macro.name)
        : (root->type) == BLK_MacroParam     ? fprintf(file, "MacroParam[%s]\n", root->attr.macro_param.str)
        : (root->type) == BLK_RuleFacts      ? fprintf(file, "RuleFacts[action:%s]\n", root->attr.facts_block.is_action ? "true" : "false")
        : (root->type) == BLK_RuleFact       ? fprintf(file, "RuleFact[%s:%s]\n", root->attr.fact.is_constant ? "constant" : "consumable", root->attr.fact.name)
        : (root->type) == BLK_RuleFactAnnote ? fprintf(file, "RuleFactAnnote[%s]\n", root->attr.fact_annote.str)
        : (root->type) == BLK_RuleModulo     ? fprintf(file, "RuleModulo[%s]\n", root->attr.rule_modulo.name)
        : (root->type) == BLK_RuleAttr       ? fprintf(file, "RuleAttr[#%06X]\n", root->attr.rule_attr.color)
        : (root->type) == BLK_RuleLet        ? fprintf(file, "RuleLet\n")
        : (root->type) == BLK_KeyBlock       ? fprintf(file, "Key\n")
        : (root->type) == BLK_KeyMark        ? fprintf(file, "KeyMark[%s]\n", ENT_TO_NAME(root->attr.key_mark.type))
                                             : fprintf(file, "Unknown\n");

    if (root->type == BLK_Rule) {
        prefix[depth] = 1;
        _print_tree(root->attr.rule.modulo, depth + 1, false, prefix, file);
        _print_tree(root->attr.rule.attrs, depth + 1, false, prefix, file);
        _print_tree(root->attr.rule.let, depth + 1, false, prefix, file);
    }

    if (root->type == BLK_RuleFact) {
        prefix[depth] = 1;
        _print_tree(root->attr.fact.annote, depth + 1, false, prefix, file);
    }

    if (root->type == BLK_Macro) {
        prefix[depth] = 1;
        _print_tree(root->attr.macro.param, depth + 1, false, prefix, file);
    }

    if (root->type == BLK_RuleLet) {
        prefix[depth] = 1;
        _print_tree(root->attr.rule_let.key, depth + 1, false, prefix, file);
    }

    AstNode* child = root->children;
    while (child) {
        if (child->sibling != NULL) {
            prefix[depth] = 1;
            _print_tree(child, depth + 1, false, prefix, file);
            child = child->sibling;
        } else {
            prefix[depth] = 0;
            _print_tree(child, depth + 1, true, prefix, file);
            break;
        }
    }
}

void print_ast_tree(AstNode* root, FILE* file)
{
    static char prefix[4096];
    memset(prefix, 0, sizeof(prefix));

    _print_tree(root, 0, true, prefix, file);
}

/****************************************************************
 *  AST Code Print Functions
 ****************************************************************/
void _print_code(AstNode* root, int indent, FILE* file);

void _print_children_code(AstNode* root, int indent, FILE* file, const char* separator)
{
    AstNode* child = root->children;
    while (child) {
        if (child->sibling != NULL) {
            _print_code(child, indent, file);
            if (separator) {
                fprintf(file, "%s", separator);
            }
            child = child->sibling;
        } else {
            _print_code(child, indent, file);
            break;
        }
    }
}

void _ident_print(int indent, FILE* file, const char* format, ...)
{
    for (int i = 0; i < indent; i++) {
        fprintf(file, "    ");
    }
    va_list args;
    va_start(args, format);
    vfprintf(file, format, args);
    va_end(args);
}

void _ident_println(int indent, FILE* file, const char* format, ...)
{
    for (int i = 0; i < indent; i++) {
        fprintf(file, "    ");
    }
    va_list args;
    va_start(args, format);
    vfprintf(file, format, args);
    va_end(args);
    fprintf(file, "\n");
}

void _print_rule(AstNode* root, int indent, FILE* file)
{

    // print rule header
    if (root->attr.rule.modulo && root->attr.rule.attrs) {
        _ident_println(indent, file, "rule (modulo %s) %s [color=#%06X]:",
            root->attr.rule.modulo->attr.rule_modulo.name,
            root->attr.rule.name,
            root->attr.rule.attrs->attr.rule_attr.color);
    } else if (root->attr.rule.modulo && !root->attr.rule.attrs) {
        _ident_println(indent, file, "rule (modulo %s) %s:",
            root->attr.rule.modulo->attr.rule_modulo.name,
            root->attr.rule.name);
    } else if (!root->attr.rule.modulo && root->attr.rule.attrs) {
        _ident_println(indent, file, "rule %s [color=#%06X]:",
            root->attr.rule.name,
            root->attr.rule.attrs->attr.rule_attr.color);
    } else {
        _ident_println(indent, file, "rule %s:", root->attr.rule.name);
    }
    // print rule let block
    if (root->attr.rule.let) {
        AstNode* let = root->attr.rule.let;
        _ident_println(indent + 1, file, "let");
        _print_children_code(let, indent + 2, file, "\n");
        fputc('\n', file);
        _ident_println(indent + 1, file, "in");
    }
    // print rule facts
    _print_children_code(root, indent + 1, file, NULL);

    fputc('\n', file);
}

void _print_rule_facts(AstNode* root, int indent, FILE* file)
{
    if (!root->children) {
        if (root->attr.facts_block.is_action) {
            _ident_println(indent, file, "-->");
        } else {
            _ident_println(indent, file, "[]");
        }
    } else {
        if (root->attr.facts_block.is_action) {
            _ident_println(indent, file, "--[");
        } else {
            _ident_println(indent, file, "[");
        }
        _print_children_code(root, indent + 1, file, ",\n");
        fputc('\n', file);
        if (root->attr.facts_block.is_action) {
            _ident_println(indent, file, "]->");
        } else {
            _ident_println(indent, file, "]");
        }
    }
}

void _print_rule_fact(AstNode* root, int indent, FILE* file)
{
    if (root->attr.fact.is_constant) {
        _ident_print(indent, file, "!%s(", root->attr.fact.name);
    } else {
        _ident_print(indent, file, "%s(", root->attr.fact.name);
    }
    _print_children_code(root, 0, file, ", ");
    fprintf(file, ")");

    if (root->attr.fact.annote) {
        AstNode temp;
        temp.children = root->attr.fact.annote;
        fprintf(file, "[");
        _print_children_code(&temp, 0, file, ", ");
        fprintf(file, "]");
    }
}

void _print_macro(AstNode* root, int indent, FILE* file)
{
    AstNode temp;
    _ident_print(indent, file, "%s(", root->attr.macro.name);
    temp.children = root->attr.macro.param;
    _print_children_code(&temp, 0, file, ", ");
    fprintf(file, ") = ");
    _print_children_code(root, 0, file, NULL);
}

void _print_term(AstNode* root, FILE* file)
{
    AstNode* child = root->children;
    TermType type = root->attr.term.type;

#define binary_op(OP)                  \
    fprintf(file, "(");                \
    _print_term(child, file);          \
    fprintf(file, ") " OP " (");       \
    _print_term(child->sibling, file); \
    fprintf(file, ")");

    if (type == TERM_VarMsg) {
        fprintf(file, "%s", root->attr.term.val);
    } else if (type == TERM_VarPub) {
        fprintf(file, "%s", root->attr.term.val);
    } else if (type == TERM_VarFresh) {
        fprintf(file, "%s", root->attr.term.val);
    } else if (type == TERM_Literal) {
        fprintf(file, "%s", root->attr.term.val);
    } else if (type == TERM_LiteralFresh) {
        fprintf(file, "%s", root->attr.term.val);
    } else if (type == TERM_OpExp) {
        binary_op("^")
    } else if (type == TERM_OpMul) {
        binary_op("*")
    } else if (type == TERM_OpXor) {
        binary_op("XOR")
    } else if (type == TERM_OpPlus) {
        binary_op("%%+")
    } else if (type == TERM_OpUnion) {
        binary_op("++")
    } else if (type == TERM_OpTuple) {
        fprintf(file, "<");
        _print_children_code(root, 0, file, ", ");
        fprintf(file, ">");
    } else if (type == TERM_OpFuncion) {
        if (root->children) {
            fprintf(file, "%s(", root->attr.term.val);
            _print_children_code(root, 0, file, ", ");
            fprintf(file, ")");
        } else {
            fprintf(file, "%s", root->attr.term.val);
        }
    } else {
        fprintf(file, "Unknown(%s)", root->attr.term.val);
    }
}

void _print_code(AstNode* root, int indent, FILE* file)
{
    if (root == NULL) {
        return;
    }

    if (root->type == BLK_Theory) {
        _ident_println(indent, file, "theory %s", root->attr.theory.name);
        _ident_println(indent, file, "begin");
        _print_children_code(root, indent + 1, file, NULL);
        _ident_println(indent, file, "end");
    } else if (root->type == BLK_Rule) {
        _print_rule(root, indent, file);
    } else if (root->type == BLK_RuleFacts) {
        _print_rule_facts(root, indent, file);
    } else if (root->type == BLK_RuleFact) {
        _print_rule_fact(root, indent, file);
    } else if (root->type == BLK_RuleFactAnnote) {
        fprintf(file, "%s", root->attr.fact_annote.str);
    } else if (root->type == BLK_Functions) {
        _ident_print(indent, file, "functions: ");
        _print_children_code(root, 0, file, ", ");
        fputs("\n\n", file);
    } else if (root->type == BLK_Function) {
        fprintf(file, "%s/%d", root->attr.func.name, root->attr.func.arity);
    } else if (root->type == BLK_Equations) {
        _ident_println(indent, file, "equations:");
        _print_children_code(root, indent + 1, file, ",\n");
        fputs("\n\n", file);
    } else if (root->type == BLK_Equation) {
        _ident_print(indent, file, "");
        _print_children_code(root, 0, file, " = ");
    } else if (root->type == BLK_BuiltIn) {
        _ident_print(indent, file, "builtins: ");
        _print_children_code(root, 0, file, ", ");
        fputs("\n\n", file);
    } else if (root->type == BLK_BuiltInFunc) {
        fprintf(file, "%s", root->attr.builtin.str);
    } else if (root->type == BLK_Macros) {
        _ident_println(indent, file, "macros: ");
        _print_children_code(root, indent + 1, file, ",\n");
        fputs("\n\n", file);
    } else if (root->type == BLK_Macro) {
        _print_macro(root, indent, file);
    } else if (root->type == BLK_MacroParam) {
        fprintf(file, "%s", root->attr.macro_param.str);
    } else if (root->type == BLK_Term) {
        _print_term(root, file);
    } else if (root->type == BLK_Reserve) {
        fprintf(file, "%s", root->attr.reserve.str);
        fputs("\n\n", file);
    } else if (root->type == BLK_Root) {
        _print_children_code(root, indent, file, NULL);
    } else {
        printf("ERROR in _print_code: unknown node type %d\n", root->type);
    }
}

void print_ast_code(AstNode* root, FILE* file)
{
    _print_code(root, 0, file);
}

void ast2python(AstNode* root, FILE* file)
{
    if (root == NULL) {
        return;
    }

#define ast2python_children(c, file)                          \
    for (AstNode* child = c; child; child = child->sibling) { \
        ast2python(child, file);                              \
    }

    if (root->type == BLK_Theory) {
        fprintf(file, "{'type': 'theory', ");
        fprintf(file, "'name':'%s',", root->attr.theory.name);
        fprintf(file, "'children':[");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_Rule) {
        fprintf(file, "{'type': 'rule',");
        fprintf(file, "'name': '%s',", root->attr.rule.name);
        if (root->attr.rule.let) {
            fprintf(file, "'let': ");
            ast2python(root->attr.rule.let, file);
        }
        if (root->attr.rule.modulo) {
            fprintf(file, "'modulo': ");
            ast2python(root->attr.rule.modulo, file);
        }
        if (root->attr.rule.attrs) {
            fprintf(file, "'attrs': ");
            ast2python(root->attr.rule.attrs, file);
        }
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_RuleFacts) {
        fprintf(file, "{'type': 'facts',");
        fprintf(file, "'is_action': %s,", root->attr.facts_block.is_action ? "True" : "False");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_RuleFact) {
        fprintf(file, "{'type': 'fact',");
        fprintf(file, "'name': '%s',", root->attr.fact.name);
        if (root->attr.fact.annote) {
            fprintf(file, "'annote': [");
            ast2python_children(root->attr.fact.annote, file);
            fprintf(file, "],");
        }
        fprintf(file, "'is_constant': %s,", root->attr.fact.is_constant ? "True" : "False");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_RuleFactAnnote) {
        fprintf(file, "{'type': 'fact_annote',");
        fprintf(file, "'str': '%s'},", root->attr.fact_annote.str);
    } else if (root->type == BLK_Functions) {
        fprintf(file, "{'type': 'functions',");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_Function) {
        fprintf(file, "{'type': 'function',");
        fprintf(file, "'name': '%s',", root->attr.func.name);
        fprintf(file, "'arity': %d,", root->attr.func.arity);
        fprintf(file, "'is_private': %s,", root->attr.func.is_private ? "True" : "False");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_Equations) {
        fprintf(file, "{'type': 'equations',");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_Equation) {
        fprintf(file, "{'type': 'equation',");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_BuiltIn) {
        fprintf(file, "{'type': 'builtins',");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_BuiltInFunc) {
        fprintf(file, "{'type': 'builtin_func',");
        fprintf(file, "'str': '%s'},", root->attr.builtin.str);
    } else if (root->type == BLK_Macros) {
        fprintf(file, "{'type': 'macros',");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_Macro) {
        fprintf(file, "{'type': 'macro',");
        fprintf(file, "'name': '%s',", root->attr.macro.name);
        fprintf(file, "'param': [");
        ast2python_children(root->attr.macro.param, file);
        fprintf(file, "],");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_MacroParam) {
        fprintf(file, "{'type': 'macro_param',");
        fprintf(file, "'str': '%s'},", root->attr.macro_param.str);
    } else if (root->type == BLK_Term) {
        fprintf(file, "{'type': 'term',");
        fprintf(file, "'op': '%s',", TERM_TYPE_NAME(root->attr.term.type));
        if (TERM_Literal == root->attr.term.type) {
            fprintf(file, "'val': \"%s\",", root->attr.term.val);
        } else {
            fprintf(file, "'val': '%s',", root->attr.term.val);
        }
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_RuleAttr) {
        fprintf(file, "{'type': 'rule_attr',");
        fprintf(file, "'color': '#%06X'},", root->attr.rule_attr.color);
    } else if (root->type == BLK_RuleModulo) {
        fprintf(file, "{'type': 'rule_modulo',");
        fprintf(file, "'name': '%s'},", root->attr.rule_modulo.name);
    } else if (root->type == BLK_RuleLet) {
        fprintf(file, "{'type': 'rule_let',");
        if (root->attr.rule_let.key) {
            fprintf(file, "'key': ");
            ast2python(root->attr.rule_let.key, file);
        }
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_KeyBlock) {
        fprintf(file, "{'type': 'key_block',");
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_KeyMark) {
        fprintf(file, "{'type': 'key_mark',");
        fprintf(file, "'key': '%s',", ENT_TO_NAME(root->attr.key_mark.type));
        fprintf(file, "'children': [");
        ast2python_children(root->children, file);
        fprintf(file, "]},");
    } else if (root->type == BLK_Reserve) {
        fprintf(file, "{'type': 'reserve',");
        fprintf(file, "'str': '");
        for(char* p = root->attr.reserve.str; *p; p++) {
            if (*p == '\'') {
                fprintf(file, "\\'");
            } else {
                fputc(*p, file);
            }
        }
        fprintf(file, "'},");
    } else if (root->type == BLK_Root) {
        fprintf(file, "{'type': 'root',");
        fprintf(file, "'children':[");
        ast2python_children(root->children, file);
        fprintf(file, "]}");
    } else {
        printf("ERROR in _print_code: unknown node type %d\n", root->type);
    }
}
