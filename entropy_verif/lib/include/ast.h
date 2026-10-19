#ifndef AST_H
#define AST_H

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

/****************************************************************
 *  Syntax Types
 ****************************************************************/
typedef enum {
    BLK_Root,
    BLK_Theory,
    BLK_Term,

    BLK_BuiltIn,
    BLK_BuiltInFunc,

    BLK_Functions,
    BLK_Function,

    BLK_Macros,
    BLK_Macro,
    BLK_MacroParam,
    
    BLK_Equations,
    BLK_Equation,

    BLK_Rule,
    BLK_RuleFacts,
    BLK_RuleFact,
    BLK_RuleFactAnnote,
    BLK_RuleModulo,
    BLK_RuleAttr,
    BLK_RuleLet,
    BLK_KeyBlock,
    BLK_KeyMark,
    
    BLK_Reserve,
} BlockType;

typedef enum {
    TERM_VarMsg,
    TERM_VarPub,
    TERM_VarFresh,
    TERM_Literal,
    TERM_LiteralFresh,

    TERM_OpExp,
    TERM_OpMul,
    TERM_OpXor,
    TERM_OpPlus,
    TERM_OpUnion,
    TERM_OpTuple,
    TERM_OpFuncion,
} TermType;

#define TERM_TYPE_NAME(type)                           \
    (type == TERM_VarMsg)             ? "VarMsg"       \
        : (type == TERM_VarPub)       ? "VarPub"       \
        : (type == TERM_VarFresh)     ? "VarFresh"     \
        : (type == TERM_Literal)      ? "Literal"      \
        : (type == TERM_LiteralFresh) ? "LiteralFresh" \
        : (type == TERM_OpExp)        ? "^"            \
        : (type == TERM_OpMul)        ? "*"            \
        : (type == TERM_OpXor)        ? "XOR"          \
        : (type == TERM_OpPlus)       ? "%%+"          \
        : (type == TERM_OpUnion)      ? "++"           \
        : (type == TERM_OpTuple)      ? "tuple"        \
        : (type == TERM_OpFuncion)    ? "function"     \
                                      : "Unknown"

typedef enum {
    ENT_Zero,
    ENT_Low,
    ENT_High,
    ENT_Chaotic,
    ENT_Trace,
} EntropyType;

#define ENT_TO_NAME(x)                   \
    (x == ENT_Trace)         ? "Trace"   \
        : (x == ENT_Zero)    ? "Zero"    \
        : (x == ENT_Low)     ? "Low"     \
        : (x == ENT_High)    ? "High"    \
        : (x == ENT_Chaotic) ? "Chaotic" \
                             : "Unknown"

#define ENT_FROM_NAME(x)                              \
    (0 == strcmp(x, "`T`"))             ? ENT_Trace   \
        : (0 == strcmp(x, "`Trace`"))   ? ENT_Trace   \
        : (0 == strcmp(x, "`Z`"))       ? ENT_Zero    \
        : (0 == strcmp(x, "`Zero`"))    ? ENT_Zero    \
        : (0 == strcmp(x, "`L`"))       ? ENT_Low     \
        : (0 == strcmp(x, "`Low`"))     ? ENT_Low     \
        : (0 == strcmp(x, "`H`"))       ? ENT_High    \
        : (0 == strcmp(x, "`High`"))    ? ENT_High    \
        : (0 == strcmp(x, "`C`"))       ? ENT_Chaotic \
        : (0 == strcmp(x, "`Chaotic`")) ? ENT_Chaotic \
                                        : -1

#define STR(x) char* x;
#define INT(x) int x;
#define BOOL(x) bool x;
#define TERM(x) TermType x;
#define ENT(x) EntropyType x;
#define AST(x) struct ast_node* x;
#define STRUCT(x, ...) \
    struct {           \
        __VA_ARGS__    \
    } x;

typedef struct ast_node {
    union {
        STRUCT(reserve, STR(str))
        STRUCT(theory, STR(name))
        STRUCT(builtin, STR(str))
        STRUCT(func, STR(name) INT(arity) BOOL(is_private))
        STRUCT(term, STR(val) TERM(type))
        STRUCT(macro, STR(name) AST(param))
        STRUCT(macro_param, STR(str))
        STRUCT(rule, STR(name) AST(let) AST(modulo) AST(attrs))
        STRUCT(fact, STR(name) AST(annote) BOOL(is_constant))
        STRUCT(fact_annote, STR(str))
        STRUCT(facts_block, BOOL(is_action))
        STRUCT(rule_modulo, STR(name))
        STRUCT(rule_attr, INT(color))
        STRUCT(rule_let, AST(key))
        STRUCT(key_mark, ENT(type))
    } attr;

    struct ast_node* sibling;
    struct ast_node* children;
    BlockType type;
} AstNode;

/****************************************************************
 *  Abstract Syntax Tree Functions
 ****************************************************************/
AstNode* ast_node_new(BlockType type);

void ast_node_free(AstNode* node);
void ast_node_add_sibling(AstNode* node, AstNode* sibling);
void ast_node_insert_sibling(AstNode* node, AstNode* sibling);
void ast_node_add_child(AstNode* node, AstNode* child);
AstNode* ast_tree_copy(AstNode* node);
AstNode* ast_tree_siblings_copy(AstNode* node);
void ast_tree_destory(AstNode* node);

void print_ast_tree(AstNode* root, FILE* file);
void print_ast_code(AstNode* root, FILE* file);
void ast2python(AstNode* root, FILE* file);

#endif
