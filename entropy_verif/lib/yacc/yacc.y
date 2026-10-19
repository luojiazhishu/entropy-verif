%{
#define YYPARSER 

#ifdef DEBUG
#define YYDEBUG 1
#endif

#include "ast.h"
#include "utils.h"
#include "global.h"

extern int yylineno;
extern int yycolumn;

int yylex();
void yyerror(const char *s);

%}


%union {
    int int_val;
    char *str_val;
    struct ast_node *ast_val;
}

/****************************************************************
 *  Token Definitions
 ****************************************************************/
/* basic tokens */
%token <str_val> IDENT
%token <int_val> HEXDIGIT
%token <str_val> STRING
%token <int_val> ARITY

/* theory tokens */
%token TOK_THEORY TOK_BEGIN TOK_END 
 
/* symbol tokens */
%token TOK_COLON TOK_UNDERSCORE TOK_COMMA TOK_SLASH TOK_BSLASH TOK_MINUS TOK_PLUS TOK_EQUAL 
%token TOK_SHARP TOK_DOT TOK_TILDE TOK_DOLLOR TOK_EXCLAMATION  TOK_SQUO TOK_DQUO TOK_WALRUS
%token TOK_LTHAN TOK_GTHAN TOK_LPAREN TOK_RPAREN TOK_LSQUARE TOK_RSQUARE TOK_LCURLY TOK_RCURLY

%nonassoc LOWER_PAREN
%nonassoc TOK_LPAREN

/* term operation tokens */
%token OP_EXP OP_MUL OP_XOR OP_UNION OP_PLUS

%left OP_PLUS
%left OP_UNION TOK_PLUS
%left OP_XOR
%left OP_MUL
%left OP_EXP    

/* functions tokens */
%token TOK_FUNCTION TOK_PRIV

/* equations tokens */
%token TOK_EQUATIONS

/* term tokens */
%token TOK_PUB TOK_FRESH TOK_MSG

/* builtins tokens */
%token TOK_BUILTIN
%token <str_val> TOK_BUILTIN_FUNCTIONS

/* macros tokens */
%token TOK_MACRO

/* heuristic tokens */
/* %token HEURISTIC */

/* tactic tokens */
/* %token TACTIC PRESORT PRIO DEPRIO */

/* rule tokens */
%token TOK_RULE TOK_ARROW TOK_LARROW TOK_RARROW TOK_LET TOK_IN TOK_NOPRECOMP TOK_MODULO TOK_COLOR
%token <int_val> TOK_ENTROPY_MARK

/* lemma tokens */
/* %token LEMMA */

%token <ast_val> TOK_RESERVE

%type <ast_val> root root_elements theory body bodyblock signature_spec functions function_list function_sym 
%type <ast_val> equations equation_list equation built_in built_ins built_in_fun
%type <ast_val> macros macro_list macro macro_param rule simple_rule rule_head rule_fact_block rule_arrow 
%type <ast_val> let_block let_equations facts fact_list fact fact_ident fact_param  fact_annotes fact_annote_list fact_annote 
%type <ast_val> modulo rule_attrs rule_attr_list rule_attr 
%type <int_val> hexcolor
%type <ast_val> term tupleterm nestedterm msetterm_list msetterm natterm xorterm multterm expterm  nary_app nary_param literal nonnode_var  msg_var
%type <ast_val> key_mark key_list key_block

%% 
root
    : root_elements {
        AST = ast_node_new(BLK_Root);
        ast_node_add_child(AST, $1);
    }

root_elements
    : root_elements theory {
        ast_node_add_sibling($1, $2);
        $$ = $1;
    }
    | root_elements TOK_RESERVE {
        ast_node_add_sibling($1, $2);
        $$ = $1;
    }
    | theory { $$ = $1; } 
    | TOK_RESERVE { $$ = $1; }
    
theory
    : TOK_THEORY IDENT TOK_BEGIN body TOK_END {
        AstNode* node = ast_node_new(BLK_Theory);
        ast_node_add_child(node, $4);
        node->attr.theory.name = $2;
        $$ = node;
    }

body
    : body bodyblock {
        ast_node_add_sibling($1, $2);
        $$ = $1;
    } 
    | bodyblock { $$ = $1; }
    
bodyblock
    : signature_spec    { $$ = $1; } 
    | rule              { $$ = $1; }
    | TOK_RESERVE       { $$ = $1; }

signature_spec
    : functions { $$ = $1; }
    | equations { $$ = $1; }
    | built_in  { $$ = $1; }
    | macros    { $$ = $1; }

functions
    : TOK_FUNCTION TOK_COLON function_list {
        AstNode* node = ast_node_new(BLK_Functions);
        ast_node_add_child(node, $3);
        $$ = node;
    }

function_list
    : function_list TOK_COMMA function_sym {
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | function_sym { $$ = $1; }

function_sym
    : IDENT TOK_SLASH ARITY {
        AstNode* node = ast_node_new(BLK_Function);
        node->attr.func.name = $1;
        node->attr.func.arity = $3;
        node->attr.func.is_private = false;
        $$ = node;
    }
    | IDENT TOK_SLASH ARITY TOK_PRIV {
        AstNode* node = ast_node_new(BLK_Function);
        node->attr.func.name = $1;
        node->attr.func.arity = $3;
        node->attr.func.is_private = true;
        $$ = node;
    }

equations
    : TOK_EQUATIONS TOK_COLON equation_list {
        AstNode* node = ast_node_new(BLK_Equations);
        ast_node_add_child(node, $3);
        $$ = node;
    }

equation_list
    : equation_list TOK_COMMA equation {
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | equation { $$ = $1; }

equation
    : msetterm TOK_EQUAL msetterm {
        AstNode* node = ast_node_new(BLK_Equation);
        ast_node_add_child(node, $1);
        ast_node_add_child(node, $3);
        $$ = node;
    }


expterm
    : expterm OP_EXP term {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpExp;
        ast_node_add_child(node, $1);
        ast_node_add_child(node, $3);
        $$ = node;
    }
    | term { $$ = $1; }

multterm
    : multterm OP_MUL expterm {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpMul;
        ast_node_add_child(node, $1);
        ast_node_add_child(node, $3);
        $$ = node;
    }
    | expterm { $$ = $1; }

xorterm
    : xorterm OP_XOR multterm {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpXor;
        ast_node_add_child(node, $1);
        ast_node_add_child(node, $3);
        $$ = node;
    }
    | multterm { $$ = $1; }

natterm
    : natterm OP_PLUS xorterm {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpPlus;
        ast_node_add_child(node, $1);
        ast_node_add_child(node, $3);
        $$ = node;
    }
    | xorterm{ $$ = $1; }

msetterm
    : msetterm OP_UNION natterm {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpUnion;
        ast_node_add_child(node, $1);
        ast_node_add_child(node, $3);
        $$ = node;
    }
    | msetterm TOK_PLUS natterm {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpUnion;
        ast_node_add_child(node, $1);
        ast_node_add_child(node, $3);
        $$ = node;
    }
    | natterm { $$ = $1; }

msetterm_list
    : msetterm_list TOK_COMMA msetterm {
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | msetterm { $$ = $1; }

nestedterm
    : TOK_LPAREN msetterm TOK_RPAREN { $$ = $2; }

tupleterm
    : TOK_LTHAN msetterm_list TOK_GTHAN { 
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpTuple;
        ast_node_add_child(node, $2);
        $$ = node;
    }

/* disable this syntax */
/* binary_app
    : IDENT TOK_LCURLY tupleterm TOK_RCURLY term {} */

nary_param
    : nary_param TOK_COMMA msetterm {
        ast_node_add_sibling($1, $3);
        $$ = $1;        
    }
    | msetterm { $$ = $1;}

nary_app
    : IDENT TOK_LPAREN nary_param TOK_RPAREN {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_OpFuncion;
        node->attr.term.val = $1;
        ast_node_add_child(node, $3);      
        $$ = node;
    }

/* disable this syntax */
/* ident_natural
    : IDENT { $$ = copy_string($1); }
    | IDENT TOK_DOT ARITY { 
        char arity[16];
        snprintf(arity, 16, "%d", $3);
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = copy_string("ident");
        node->attr.term.val = concat_string(3, $1, ".", arity);
        $$ = node;
    } */
    
msg_var 
    : IDENT TOK_MSG {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_VarMsg;
        node->attr.term.val = concat_string(2, $1, ":msg");
        free($1);
        $$ = node;
    }

nonnode_var
    : IDENT %prec LOWER_PAREN { 
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_VarMsg;
        node->attr.term.val = $1;
        $$ = node;
    }
    | TOK_DOLLOR IDENT { 
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_VarPub;
        node->attr.term.val = concat_string(2, "$", $2);
        free($2);
        $$ = node;
    }
    | TOK_TILDE IDENT {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_VarFresh;
        node->attr.term.val = concat_string(2, "~", $2);
        free($2);
        $$ = node;
    }
    | IDENT TOK_PUB {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_VarPub;
        node->attr.term.val = concat_string(2, $1, ":pub");
        free($1);
        $$ = node;
    }
    | IDENT TOK_FRESH {
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_VarFresh;
        node->attr.term.val = concat_string(2, $1, ":fresh");
        free($1);
        $$ = node;
    }
    | msg_var { $$ = $1; }

literal
    : STRING { 
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_Literal;
        node->attr.term.val = $1;
        $$ = node;
    }
    | TOK_TILDE STRING { 
        AstNode* node = ast_node_new(BLK_Term);
        node->attr.term.type = TERM_LiteralFresh;
        node->attr.term.val = concat_string(2, "~", $2);
        free($2);
        $$ = node;
    }
    | nonnode_var { $$ = $1; }

term
    : tupleterm { $$ = $1;}
    | nestedterm { $$ = $1;}
    | nary_app { $$ = $1;}
    | literal { $$ = $1; }


built_in
    : TOK_BUILTIN TOK_COLON built_ins {
        AstNode* node = ast_node_new(BLK_BuiltIn);
        ast_node_add_child(node, $3);
        $$ = node;
    }

built_ins
    : built_ins TOK_COMMA built_in_fun {
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | built_in_fun {
        $$ = $1;
    }

built_in_fun
    : TOK_BUILTIN_FUNCTIONS {
        AstNode* node = ast_node_new(BLK_BuiltInFunc);
        node->attr.builtin.str = $1;
        $$ = node;
    }

macros
    : TOK_MACRO TOK_COLON macro_list {
        AstNode* node = ast_node_new(BLK_Macros);
        ast_node_add_child(node, $3);
        $$ = node;
    }

macro_list
    : macro_list TOK_COMMA macro {
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | macro {
        $$ = $1;
    }

macro
    : IDENT TOK_LPAREN TOK_RPAREN TOK_EQUAL msetterm {
        AstNode* node = ast_node_new(BLK_Macro);
        node->attr.macro.name = $1;
        ast_node_add_child(node, $5);
        $$ = node;
    }
    | IDENT TOK_LPAREN macro_param TOK_RPAREN TOK_EQUAL msetterm {
        AstNode* node = ast_node_new(BLK_Macro);
        node->attr.macro.name = $1;
        node->attr.macro.param = $3;
        ast_node_add_child(node, $6);
        $$ = node;
    }

macro_param
    : macro_param TOK_COMMA IDENT {
        AstNode* node = ast_node_new(BLK_MacroParam);
        node->attr.macro_param.str = $3;
        ast_node_add_sibling($1, node);
        $$ = $1;
    }
    | IDENT {
        AstNode* node = ast_node_new(BLK_MacroParam);
        node->attr.macro_param.str = $1;
        $$ = node;
    }
 

/* rule        := simple_rule [variants] */
rule
    : simple_rule {
        $$ = $1;
    }
    
simple_rule
    : rule_head rule_fact_block rule_arrow rule_fact_block {
        ast_node_add_child($1, $2); // premise facts
        ast_node_add_child($1, $3); // action facts
        ast_node_add_child($1, $4); // conclusion facts
        $$ = $1;
    }
    | rule_head let_block rule_fact_block rule_arrow rule_fact_block {
        $1->attr.rule.let = $2;
        ast_node_add_child($1, $3); // premise facts
        ast_node_add_child($1, $4); // action facts
        ast_node_add_child($1, $5); // conclusion facts
        $$ = $1;
    }

rule_head
    : TOK_RULE IDENT TOK_COLON {
        AstNode* node = ast_node_new(BLK_Rule);
        node->attr.rule.name = $2;
        $$ = node;
    }
    | TOK_RULE modulo IDENT TOK_COLON {
        AstNode* node = ast_node_new(BLK_Rule);
        node->attr.rule.modulo = $2;
        node->attr.rule.name = $3;
        $$ = node;
    }
    | TOK_RULE IDENT rule_attrs TOK_COLON {
        AstNode* node = ast_node_new(BLK_Rule);
        node->attr.rule.name = $2;
        node->attr.rule.attrs = $3;
        $$ = node;
    }
    | TOK_RULE modulo IDENT rule_attrs TOK_COLON {
        AstNode* node = ast_node_new(BLK_Rule);
        node->attr.rule.modulo = $2;
        node->attr.rule.name = $3;
        node->attr.rule.attrs = $4;
        $$ = node;
    }

rule_fact_block
    : TOK_LSQUARE TOK_RSQUARE { 
        $$ = ast_node_new(BLK_RuleFacts); 
        $$->attr.facts_block.is_action = false;
    }
    | TOK_LSQUARE facts TOK_RSQUARE { 
        AstNode* node = ast_node_new(BLK_RuleFacts);
        ast_node_add_child(node, $2);
        node->attr.facts_block.is_action = false;
        $$ = node;
    }

rule_arrow
    : TOK_ARROW {  
        $$  = ast_node_new(BLK_RuleFacts); 
        $$->attr.facts_block.is_action = true;
    }
    | TOK_LARROW TOK_RARROW {  
        $$  = ast_node_new(BLK_RuleFacts); 
        $$->attr.facts_block.is_action = true;
    }
    | TOK_LARROW facts TOK_RARROW { 
        AstNode* node = ast_node_new(BLK_RuleFacts);
        node->attr.facts_block.is_action = true;
        ast_node_add_child(node, $2);
        $$ = node; 
    }

facts
    : fact_list { $$ = $1; }
    | fact_list TOK_COMMA { $$ = $1; }

fact_list
    : fact_list TOK_COMMA fact {
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | fact { $$ = $1;}

fact
    : fact_ident TOK_LPAREN TOK_RPAREN { $$ = $1; }
    | fact_ident TOK_LPAREN fact_param TOK_RPAREN {
        ast_node_add_child($1, $3);
        $$ = $1;
    }
    | fact_ident TOK_LPAREN fact_param TOK_RPAREN fact_annotes {
        ast_node_add_child($1, $3);
        $1->attr.fact.annote = $5;
        $$ = $1;
    }
    
fact_ident
    : IDENT {
        AstNode* node = ast_node_new(BLK_RuleFact);
        node->attr.fact.name = $1;
        node->attr.fact.is_constant = false;
        $$ = node;
    }
    |TOK_UNDERSCORE IDENT {
        AstNode* node = ast_node_new(BLK_RuleFact);
        node->attr.fact.name = concat_string(2, "_", $2);
        node->attr.fact.is_constant = false;
        $$ = node;
        free($2);
    }
    | TOK_EXCLAMATION IDENT {
        AstNode* node = ast_node_new(BLK_RuleFact);
        node->attr.fact.name = $2;
        node->attr.fact.is_constant = true;
        $$ = node;
    }

fact_param
    :  fact_param TOK_COMMA msetterm {
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | msetterm { $$ = $1;}

fact_annotes
    : TOK_LSQUARE fact_annote_list TOK_RSQUARE  { $$ = $2; }

fact_annote_list
    : fact_annote_list TOK_COMMA fact_annote {
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | fact_annote {
        $$ = $1;
    }
fact_annote
    : TOK_PLUS {
        AstNode* node = ast_node_new(BLK_RuleFactAnnote);
        node->attr.fact_annote.str = copy_string("+");
        $$ = node;
    }
    | TOK_MINUS {
        AstNode* node = ast_node_new(BLK_RuleFactAnnote);
        node->attr.fact_annote.str = copy_string("-");
        $$ = node;
    }
    | TOK_NOPRECOMP{
        AstNode* node = ast_node_new(BLK_RuleFactAnnote);
        node->attr.fact_annote.str = copy_string("no_precomp");
        $$ = node;
    }

let_block
    : TOK_LET let_equations TOK_IN { 
        AstNode* node = ast_node_new(BLK_RuleLet);
        ast_node_add_child(node, $2);
        $$ = node;
    }
    | TOK_LET key_block TOK_IN { 
        AstNode* node = ast_node_new(BLK_RuleLet);
        node->attr.rule_let.key = $2;
        $$ = node;
    }
    | TOK_LET key_block let_equations TOK_IN { 
        AstNode* node = ast_node_new(BLK_RuleLet);
        node->attr.rule_let.key = $2;
        ast_node_add_child(node, $3);
        $$ = node;
    }

let_equations
    : let_equations equation {
        ast_node_add_sibling($1, $2);
        $$ = $1;
    }
    | equation { $$ = $1; }

key_block
    : TOK_LPAREN key_list TOK_RPAREN { 
        AstNode* node = ast_node_new(BLK_KeyBlock);
        ast_node_add_child(node, $2);
        $$ = node;
    }

key_list
    : key_list TOK_COMMA key_mark{
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | key_mark { $$ = $1; }

key_mark
    : nonnode_var TOK_WALRUS TOK_ENTROPY_MARK {
        AstNode* node = ast_node_new(BLK_KeyMark);
        ast_node_add_child(node, $1);
        node->attr.key_mark.type = $3;
        $$ = node;
    }

modulo
    : TOK_LPAREN TOK_MODULO IDENT TOK_RPAREN {
        AstNode* node = ast_node_new(BLK_RuleModulo);
        node->attr.rule_modulo.name = $3;
        $$ = node;
    }

rule_attrs
    : TOK_LSQUARE rule_attr_list TOK_RSQUARE { $$ = $2; }
    
rule_attr_list
    : rule_attr_list TOK_COMMA rule_attr {
        ast_node_add_sibling($1, $3);
        $$ = $1;
    }
    | rule_attr { $$ = $1; }

rule_attr
    : TOK_COLOR hexcolor {
        AstNode* node = ast_node_new(BLK_RuleAttr);
        node->attr.rule_attr.color = $2;
        $$ = node;
    }

hexcolor
    : HEXDIGIT { $$ = $1; }
    | TOK_SHARP HEXDIGIT { $$ = $2; }
    | TOK_SQUO HEXDIGIT TOK_SQUO { $$ = $2; }
    | TOK_SQUO TOK_SHARP HEXDIGIT TOK_SQUO { $$ = $3; }

%%

void yyerror(const char *s) {
    fprintf(stderr, "Syntax Error: %s at line %d, column %d, TEXT %s\n", s, yylineno, yycolumn, yylval.str_val);
}

int yywrap(){
    return 1;
}

