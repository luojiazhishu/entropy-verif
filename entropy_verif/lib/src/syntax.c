#include "syntax.h"
#include "log.h"
#include "utils.h"
#include <string.h>

#define ENT_FACT_NAME "Entropy"
#define ENT_FR_FACT_NAME "EntropyFresh"

#define ENT_ZERO_FUNCNAME "ZERO"
#define ENT_LOW_FUNCNAME "LOW"
#define ENT_HIGH_FUNCNAME "HIGH"
#define ENT_CHAOTIC_FUNCNAME "CHAOTIC"

#define ENT_COMBINE_FUNCNAME "entropy_combine"

#define ENT_TO_FUNC(x)                              \
    (x == ENT_Zero)          ? ENT_ZERO_FUNCNAME    \
        : (x == ENT_Low)     ? ENT_LOW_FUNCNAME     \
        : (x == ENT_High)    ? ENT_HIGH_FUNCNAME    \
        : (x == ENT_Chaotic) ? ENT_CHAOTIC_FUNCNAME \
                             : "UNKNOWN"
#define EQUATION_PIROR(x) (                                                            \
    (0 == strcmp(x->children->sibling->attr.term.val, ENT_COMBINE_FUNCNAME))       ? 0 \
        : (0 == strcmp(x->children->sibling->attr.term.val, ENT_CHAOTIC_FUNCNAME)) ? 1 \
        : (0 == strcmp(x->children->sibling->attr.term.val, ENT_HIGH_FUNCNAME))    ? 2 \
        : (0 == strcmp(x->children->sibling->attr.term.val, ENT_LOW_FUNCNAME))     ? 3 \
        : (0 == strcmp(x->children->sibling->attr.term.val, ENT_ZERO_FUNCNAME))    ? 4 \
                                                                                   : 5)

#define FACT_PIROR(x) (                                       \
    (0 == strcmp(x->attr.fact.name, ENT_FR_FACT_NAME))    ? 0 \
        : (0 == strcmp(x->attr.fact.name, ENT_FACT_NAME)) ? 1 \
                                                          : 2)

typedef struct {
    char* func;
    int argc;
} Function;

const Function ENT_FUNCTIONS[] = {
    { ENT_ZERO_FUNCNAME, 0 },
    { ENT_LOW_FUNCNAME, 0 },
    { ENT_HIGH_FUNCNAME, 0 },
    { ENT_CHAOTIC_FUNCNAME, 0 },
    { ENT_COMBINE_FUNCNAME, 2 },
};

typedef struct {
    char* left;
    char* right;
} Equation;

const Equation ENT_EQUATIONS_COMPLETENESS[] = {
    { ENT_COMBINE_FUNCNAME "(" ENT_ZERO_FUNCNAME ", x)", "x" },
    { ENT_COMBINE_FUNCNAME "(x, " ENT_ZERO_FUNCNAME ")", "x" },
    { ENT_COMBINE_FUNCNAME "(" ENT_LOW_FUNCNAME ", " ENT_LOW_FUNCNAME ")", ENT_LOW_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(" ENT_LOW_FUNCNAME ", " ENT_HIGH_FUNCNAME ")", ENT_HIGH_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(" ENT_HIGH_FUNCNAME ", " ENT_LOW_FUNCNAME ")", ENT_HIGH_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(" ENT_HIGH_FUNCNAME ", " ENT_HIGH_FUNCNAME ")", ENT_HIGH_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(" ENT_CHAOTIC_FUNCNAME ", x)", ENT_CHAOTIC_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(x, " ENT_CHAOTIC_FUNCNAME ")", ENT_CHAOTIC_FUNCNAME },
};

const Equation ENT_EQUATIONS_SOUNDNESS[] = {
    { ENT_COMBINE_FUNCNAME "(" ENT_ZERO_FUNCNAME ", x)", "x" },
    { ENT_COMBINE_FUNCNAME "(x, " ENT_ZERO_FUNCNAME ")", "x" },
    { ENT_COMBINE_FUNCNAME "(" ENT_LOW_FUNCNAME ", " ENT_LOW_FUNCNAME ")", ENT_HIGH_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(" ENT_LOW_FUNCNAME ", " ENT_HIGH_FUNCNAME ")", ENT_HIGH_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(" ENT_HIGH_FUNCNAME ", " ENT_LOW_FUNCNAME ")", ENT_HIGH_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(" ENT_HIGH_FUNCNAME ", " ENT_HIGH_FUNCNAME ")", ENT_HIGH_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(" ENT_CHAOTIC_FUNCNAME ", x)", ENT_CHAOTIC_FUNCNAME },
    { ENT_COMBINE_FUNCNAME "(x, " ENT_CHAOTIC_FUNCNAME ")", ENT_CHAOTIC_FUNCNAME },
};

#define LIST_APPEND(list, a) list ? ast_node_add_sibling(list, a) : (list = a)
#define LIST_DISTORY(list)                            \
    for (AstNode* _t_ = list, *_n_; _t_; _t_ = _n_) { \
        _n_ = _t_->sibling;                           \
        ast_tree_destory(_t_);                        \
    }

#define TERM_EQUAL(a, b) (                    \
    BLK_Term == a->type                       \
    && BLK_Term == b->type                    \
    && a->attr.term.type == b->attr.term.type \
    && !strcmp(a->attr.term.val, b->attr.term.val))

void sanitize_name(char* str);
char* create_key_label(const char* keyname);
char* create_entropy_label(const char* keyname);
AstNode* create_entropy_fact(char* keyname, EntropyType ent);
AstNode* create_entropy_equation(char* keyname, EntropyType ent);
AstNode* create_combine_term_list(AstNode* terms);
AstNode* create_combine_term(AstNode* term);
AstNode* create_combine_equation(char* keyname, AstNode* term);

void sanitize_name(char* str)
{
    char* p = str;
    while (*p) {
        if ('$' == *p) {
            *p = 'p';
        } else if ('~' == *p) {
            *p = 'f';
        } else if (':' == *p || '`' == *p) {
            *p = '_';
        }
        p++;
    }
    return;
}

char* create_key_label(const char* keyname)
{
    int len = strlen(keyname);
    char* label = malloc((len + 3) * sizeof(char));
    memcpy(label + 1, keyname, len);
    label[0] = '\'';
    label[len + 1] = '\'';
    label[len + 2] = '\0';
    sanitize_name(label);
    return label;
}

char* create_entropy_label(const char* keyname)
{
    char* label = concat_string(2, "ent_", keyname);
    sanitize_name(label);
    return label;
}

AstNode* create_entropy_fact(char* keyname, EntropyType ent)
{
    AstNode* fact = ast_node_new(BLK_RuleFact);
    fact->attr.fact.is_constant = true;
    fact->attr.fact.name = copy_string(ENT_FACT_NAME);

    AstNode* key_label = ast_node_new(BLK_Term);
    key_label->attr.term.type = TERM_Literal;
    key_label->attr.term.val = create_key_label(keyname);
    ast_node_add_child(fact, key_label);

    AstNode* key = ast_node_new(BLK_Term);
    key->attr.term.type = TERM_VarMsg;
    key->attr.term.val = copy_string(keyname);
    ast_node_add_child(fact, key);

    AstNode* key_ent = ast_node_new(BLK_Term);
    if (ENT_Trace == ent) {
        key_ent->attr.term.type = TERM_VarMsg;
        key_ent->attr.term.val = create_entropy_label(keyname);
    } else {
        key_ent->attr.term.type = TERM_OpFuncion;
        key_ent->attr.term.val = copy_string(ENT_TO_FUNC(ent));
    }
    ast_node_add_child(fact, key_ent);

    return fact;
}

AstNode* create_entropy_fr_fact(char* keyname)
{
    AstNode* fact = ast_node_new(BLK_RuleFact);
    fact->attr.fact.is_constant = false;
    fact->attr.fact.name = copy_string(ENT_FR_FACT_NAME);

    AstNode* key_label = ast_node_new(BLK_Term);
    key_label->attr.term.type = TERM_Literal;
    key_label->attr.term.val = create_key_label(keyname);
    ast_node_add_child(fact, key_label);

    AstNode* key = ast_node_new(BLK_Term);
    key->attr.term.type = TERM_VarMsg;
    key->attr.term.val = copy_string(keyname);
    ast_node_add_child(fact, key);

    return fact;
}

AstNode* create_entropy_equation(char* keyname, EntropyType ent)
{
    AstNode* equation = ast_node_new(BLK_Equation);

    AstNode* left = ast_node_new(BLK_Term);
    left->attr.term.type = TERM_VarMsg;
    left->attr.term.val = create_entropy_label(keyname);
    ast_node_add_child(equation, left);

    AstNode* right = ast_node_new(BLK_Term);
    right->attr.term.type = TERM_OpFuncion;
    right->attr.term.val = copy_string(ENT_TO_FUNC(ent));
    ast_node_add_child(equation, right);

    return equation;
}

AstNode* create_combine_term_list(AstNode* terms)
{
    AstNode* node = NULL;
    if (!terms) {
        return NULL;
    }

    if (!terms->sibling) {
        // 1-arg function: just ignore the function and keep the argument
        node = create_combine_term(terms);
    } else {
        // n-args function
        node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpFuncion;
        node->attr.term.val = copy_string(ENT_COMBINE_FUNCNAME);
        ast_node_add_child(node, create_combine_term(terms));
        ast_node_add_child(node, create_combine_term_list(terms->sibling));
    }

    return node;
}

AstNode* create_combine_term(AstNode* term)
{
    AstNode* node = NULL;

    switch (term->attr.term.type) {
    // variable
    case TERM_VarMsg:
    case TERM_VarFresh: {
        node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_VarMsg;
        node->attr.term.val = create_entropy_label(term->attr.term.val);
        break;
    }

    // constant
    case TERM_VarPub:
    case TERM_Literal:
    case TERM_LiteralFresh: {
        node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpFuncion;
        node->attr.term.val = copy_string(ENT_TO_FUNC(ENT_Zero));
        break;
    }

    // function
    case TERM_OpExp:
    case TERM_OpMul:
    case TERM_OpXor:
    case TERM_OpPlus:
    case TERM_OpUnion:
    case TERM_OpTuple:
    case TERM_OpFuncion: {
        if (!term->children) {
            // 0-args function: considered as a constant
            node = ast_node_new(BLK_Term);
            node->attr.term.type = TERM_OpFuncion;
            node->attr.term.val = copy_string(ENT_TO_FUNC(ENT_Zero));
        } else {
            // n-args function
            node = create_combine_term_list(term->children);
        }
        break;
    }
    default:
        break;
    }

    return node;
}

AstNode* create_combine_equation(char* keyname, AstNode* term)
{
    AstNode* equation = ast_node_new(BLK_Equation);

    AstNode* left = ast_node_new(BLK_Term);
    left->attr.term.type = TERM_VarMsg;
    left->attr.term.val = create_entropy_label(keyname);
    ast_node_add_child(equation, left);

    AstNode* right = create_combine_term(term);
    ast_node_add_child(equation, right);

    return equation;
}

void find_variable_terms(AstNode* term, AstNode** list_ptr)
{
    if (!term) {
        return;
    }

    AstNode* node = NULL;
    switch (term->attr.term.type) {
    case TERM_VarMsg:
    case TERM_VarFresh:
        node = ast_node_new(BLK_Term);
        node->attr.term.type = term->attr.term.type;
        node->attr.term.val = copy_string(term->attr.term.val);
        LIST_APPEND(*list_ptr, node);
        break;
    default:
        break;
    }

    AstNode* child = term->children;
    while (child) {
        find_variable_terms(child, list_ptr);
        child = child->sibling;
    }
}

bool does_contain_term(AstNode* term_list, AstNode* term)
{
    while (term_list) {
        if (TERM_EQUAL(term_list, term)) {
            return true;
        }
        term_list = term_list->sibling;
    }
    return false;
}

bool does_contain_fact(AstNode* fact_list, AstNode* fact)
{
    while (fact_list) {
        if (BLK_RuleFact == fact_list->type
            && BLK_RuleFact == fact->type
            && !strcmp(fact_list->attr.fact.name, fact->attr.fact.name)) {
            return true;
        }
        fact_list = fact_list->sibling;
    }
    return false;
}

AstNode* extend_rule(AstNode* rule)
{
    // plist = [] (terms remained to process)
    // tlist = [] (all the terms)

    // new_rule
    // new_equations
    // new_promises
    // new_conclusions

    // using terms in cloclusion initialize plist and tlist

    // for term in plist:
    //     if term defined in keymark:
    //          add ent_enquation enquation to new_equations
    //          add ent_fact to new_conclusions
    //
    //     if term defined in equation:
    //          for term in equation_right_terms:
    //              if term not in tlist:
    //                  add term to tlist, plist
    //          add equation to new_equations
    //          add ent_enquation to new_equations
    //          add ent_fact to new_conclusions
    //
    //     if term defined in promise:
    //
    //          if promise is Fr:
    //              add ent_fr_promise in new_promises
    //              add ent_fr_colclusion in original rule conclusions
    //          else:
    //              for term in promise:
    //                  if term not in tlist:
    //                      add term to tlist, plist
    //              add ent_promise to new_promises

    AstNode* promises = rule->children;
    AstNode* conclusions = rule->children->sibling->sibling;
    AstNode* equations = NULL;
    if (rule->attr.rule.let) {
        equations = rule->attr.rule.let->children;
    }
    AstNode* keymarks = NULL;
    if (rule->attr.rule.let && rule->attr.rule.let->attr.rule_let.key) {
        keymarks = rule->attr.rule.let->attr.rule_let.key->children;
    }

    AstNode* new_promises = NULL;
    AstNode* new_conclusions = NULL;
    AstNode* new_equations = NULL;

    AstNode* term_list = NULL;
    AstNode* marked_list = NULL;
    AstNode* equation_expand = NULL;

    // using variable terms in cloclusion facts to initialize term_list
    for (AstNode* fact = conclusions->children; fact; fact = fact->sibling) {
        for (AstNode* term = fact->children; term; term = term->sibling) {
            find_variable_terms(term, &term_list);
        }
    }

    // process all the terms in term_list
    for (AstNode* term_cur = term_list; term_cur; term_cur = term_cur->sibling) {
        bool processed = false;
        bool is_marked = does_contain_term(marked_list, term_cur);

        // term defined in keymark
        for (AstNode* keymark = keymarks; keymark && !is_marked; keymark = keymark->sibling) {
            if (TERM_EQUAL(term_cur, keymark->children)) {
                AstNode* ent_equa = create_entropy_equation(term_cur->attr.term.val, keymark->attr.key_mark.type);
                LIST_APPEND(new_equations, ent_equa);
                AstNode* fact = create_entropy_fact(term_cur->attr.term.val, ENT_Trace);
                LIST_APPEND(new_conclusions, fact);
                AstNode* term_copy = ast_tree_copy(term_cur);
                term_copy->sibling = NULL;
                LIST_APPEND(marked_list, term_copy);
                is_marked = true;
                break;
            }
        }

        // term defined in equation
        for (AstNode* equa = equations; equa && !processed; equa = equa->sibling) {
            if (TERM_EQUAL(term_cur, equa->children)) {
                // add all the terms in the right of the equation to term_list
                AstNode *rterms = NULL, *rterm, *next;
                find_variable_terms(equa->children->sibling, &rterms);
                rterm = rterms;
                while (rterm) {
                    next = rterm->sibling;
                    if (!does_contain_term(equation_expand, rterm)) {
                        rterm->sibling = NULL;
                        LIST_APPEND(equation_expand, ast_tree_copy(rterm));
                    }
                    if (!does_contain_term(term_list, rterm)) {
                        rterm->sibling = NULL;
                        LIST_APPEND(term_list, rterm);
                    } else {
                        ast_tree_destory(rterm);
                    }
                    rterm = next;
                }

                // add equation to new_equations
                LIST_APPEND(new_equations, ast_tree_copy(equa));
                // add ent_enquation to new_equations
                AstNode* ent_equa = create_combine_equation(term_cur->attr.term.val, equa->children->sibling);
                LIST_APPEND(new_equations, ent_equa);
                // add ent_fact to new_conclusions
                AstNode* fact = create_entropy_fact(term_cur->attr.term.val, ENT_Trace);
                if (does_contain_fact(new_conclusions, fact)) {
                    ast_tree_destory(fact);
                } else {
                    LIST_APPEND(new_conclusions, fact);
                }
                processed = true;
                break;
            }
        }

        // term defined in promise
        if (TERM_VarFresh == term_cur->attr.term.type) {
            // find the fact contains the fresh var
            AstNode* found_fact = NULL;
            for (AstNode* fact = promises->children; fact && !found_fact; fact = fact->sibling) {
                AstNode* fact_terms = NULL;
                // get all varialbe terms in fact
                for (AstNode* term = fact->children; term; term = term->sibling) {
                    find_variable_terms(term, &fact_terms);
                }
                // find the same term
                for (AstNode* term = fact_terms; term; term = term->sibling) {
                    if (TERM_EQUAL(term_cur, term)) {
                        found_fact = fact;
                        break;
                    }
                }
                LIST_DISTORY(fact_terms);
            }

            if (found_fact) {
                AstNode* new_fact = create_entropy_fr_fact(term_cur->attr.term.val);
                if (0 == strcmp(found_fact->attr.fact.name, "Fr")) {
                    ast_node_add_child(conclusions, ast_tree_copy(new_fact));
                }
                LIST_APPEND(new_promises, new_fact);
            } else {
                ERROR("Fresh variable %s not found in promises facts.", term_cur->attr.term.val);
            }
        } else if (!is_marked && !processed && does_contain_term(equation_expand, term_cur)) {
            AstNode* new_prom = create_entropy_fact(term_cur->attr.term.val, ENT_Trace);
            LIST_APPEND(new_promises, new_prom);
        }
    }

    LIST_DISTORY(term_list);
    LIST_DISTORY(marked_list);
    LIST_DISTORY(equation_expand);

    // sort new_equations
    for (AstNode* i = new_equations; i; i = i->sibling) {
        for (AstNode* j = i->sibling; j; j = j->sibling) {
            if (EQUATION_PIROR(i) < EQUATION_PIROR(j)) {
                AstNode tmp = *j;
                j->attr = i->attr;
                j->type = i->type;
                j->children = i->children;
                i->attr = tmp.attr;
                i->type = tmp.type;
                i->children = tmp.children;
            }
        }
    }
    AstNode* new_let = ast_node_new(BLK_RuleLet);
    ast_node_add_child(new_let, new_equations);

    // sort new_promises
    for (AstNode* i = new_promises; i; i = i->sibling) {
        for (AstNode* j = i->sibling; j; j = j->sibling) {
            if (FACT_PIROR(i) < FACT_PIROR(j)) {
                AstNode tmp = *j;
                j->attr = i->attr;
                j->type = i->type;
                j->children = i->children;
                i->attr = tmp.attr;
                i->type = tmp.type;
                i->children = tmp.children;
            }
        }
    }
    AstNode* promise_rule_facts = ast_node_new(BLK_RuleFacts);
    ast_node_add_child(promise_rule_facts, new_promises);

    AstNode* action_rule_facts = ast_node_new(BLK_RuleFacts);
    action_rule_facts->attr.facts_block.is_action = true;

    AstNode* conclusion_rule_facts = ast_node_new(BLK_RuleFacts);
    ast_node_add_child(conclusion_rule_facts, new_conclusions);

    AstNode* new_rule = ast_node_new(BLK_Rule);
    new_rule->attr.rule.name = concat_string(2, "entropy_", rule->attr.rule.name);
    new_rule->attr.rule.let = new_let;
    ast_node_add_child(new_rule, promise_rule_facts);
    ast_node_add_child(new_rule, action_rule_facts);
    ast_node_add_child(new_rule, conclusion_rule_facts);

    return new_rule;
}

AstNode* syntax_extend_recursion(AstNode* node)
{
    if (node == NULL) {
        return NULL;
    }

    AstNode* new_list = NULL;
    AstNode* new_node = NULL;
    if (BLK_Rule == node->type && node->attr.rule.let) {
        new_node = extend_rule(node);
        LIST_APPEND(new_list, new_node);
    }

    AstNode* child = node->children;
    while (child) {
        new_node = syntax_extend_recursion(child);
        LIST_APPEND(new_list, new_node);
        child = child->sibling;
    }

    return new_list;
}

void syntax_tree_sort(AstNode* theory)
{
    // builtins functions macros equatinon rules reserves
    AstNode **pre, *child, *head = NULL;
    BlockType TheorySubBlocks[] = { BLK_BuiltIn, BLK_Functions, BLK_Macros, BLK_Equations, BLK_Rule, BLK_Reserve };
    BlockType now_block;

    for (int i = 0; i < sizeof(TheorySubBlocks) / sizeof(BlockType); i++) {
        now_block = TheorySubBlocks[i];
        child = theory->children;
        pre = &theory->children;

        while (child) {
            if (now_block == child->type) {
                LIST_APPEND(head, child);
                *pre = child->sibling;
                child->sibling = NULL;
            } else {
                pre = &child->sibling;
            }
            child = *pre;
        }
    }

    LIST_APPEND(head, theory->children);
    theory->children = head;
}

void add_extention_functions(AstNode* theory, const Function* functions, int num)
{
    AstNode* func_blk = theory->children;
    while (func_blk && BLK_Functions != func_blk->type) {
        func_blk = func_blk->sibling;
    }
    if (!func_blk) {
        func_blk = ast_node_new(BLK_Functions);
        ast_node_add_child(theory, func_blk);
    }

    for (int i = 0; i < num; i++) {
        AstNode* func = ast_node_new(BLK_Function);
        func->attr.func.name = copy_string(functions[i].func);
        func->attr.func.arity = functions[i].argc;
        func->attr.func.is_private = false;
        ast_node_add_child(func_blk, func);
    }
}

void add_extention_equations(AstNode* theory, const Equation* equations, int num)
{
    AstNode* equa_blk = theory->children;
    while (equa_blk && BLK_Equations != equa_blk->type) {
        equa_blk = equa_blk->sibling;
    }
    if (!equa_blk) {
        equa_blk = ast_node_new(BLK_Equations);
        ast_node_add_child(theory, equa_blk);
    }

    for (int i = 0; i < num; i++) {
        AstNode* left = ast_node_new(BLK_Term);
        left->attr.term.type = TERM_VarMsg;
        left->attr.term.val = copy_string(equations[i].left);

        AstNode* right = ast_node_new(BLK_Term);
        right->attr.term.type = TERM_VarMsg;
        right->attr.term.val = copy_string(equations[i].right);

        AstNode* equa = ast_node_new(BLK_Equation);
        ast_node_add_child(equa, left);
        ast_node_add_child(equa, right);

        ast_node_add_child(equa_blk, equa);
    }
}

void syntax_extend(AstNode* node)
{

    AstNode* theory = node->children;
    while (theory && BLK_Theory != theory->type) {
        theory = theory->sibling;
    }

    if (!theory) {
        ERROR("No theory block found.");
        return;
    }

    AstNode* new = syntax_extend_recursion(theory);
    ast_node_add_child(theory, new);

    add_extention_functions(theory, ENT_FUNCTIONS, sizeof(ENT_FUNCTIONS) / sizeof(Function));
    add_extention_equations(theory, ENT_EQUATIONS_COMPLETENESS, sizeof(ENT_EQUATIONS_COMPLETENESS) / sizeof(Equation));

    syntax_tree_sort(theory);
}
