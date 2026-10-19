%{
#include "global.h"
#include "utils.h"
#include "ast.h"

int yycolumn = 1;

void update_position(char *text) 
{
    for (int i = 0; text[i] != '\0'; ++i) {
        if (text[i] == '\n') {
            yylineno++;
            yycolumn = 1;
        } else {
            yycolumn++;
        }
    }
}

#define RESERVE_BLOCK_SIZE 1024
char* reserve_content = NULL; // save the content of reserve block  
size_t reserve_content_size = 0;
size_t reserve_blocks_size = 0;

#define STATE_STACK_SIZE 1024
int state_stack[STATE_STACK_SIZE];
int state_stack_top = 0;
#define PUSH_STATE(state) state_stack[state_stack_top++] = state
#define POP_STATE() state_stack[--state_stack_top]
%}


/****************************************************************
 *  Basic definitions 
****************************************************************/
digit       [0-9]
alphaNum    [a-zA-Z0-9]
hexdigit    [a-fA-F0-9]{6}
natural     {digit}+
ident       {alphaNum}({alphaNum}|_)*
string      '[^'\n]+'

whitespace  [ \t\r\n]
all         [\0-\377]

built_ins   diffie-hellman|hashing|symmetric-encryption|asymmetric-encryption|signing|bilinear-pairing|xor|multiset|natural-numbers|revealing-signing
entropy_marks   `L`|`Low`|`H`|`High`|`Z`|`Zero`|`C`|`Chaotic`

%option noyywrap
%option nounput
%option noinput

%x THEORY
%x RESERVE
%x LINE_COMMENT
%x BLOCK_COMMENT

%%

<INITIAL>"theory"       { 
                            update_position(yytext); 
                            BEGIN(THEORY);
                            return TOK_THEORY; 
                        }
<THEORY>"begin"         { update_position(yytext); return TOK_BEGIN; }
<THEORY>"end"           { 
                            update_position(yytext); 
                            BEGIN(INITIAL);
                            return TOK_END; 
                        }

<THEORY>":pub"          { update_position(yytext); return TOK_PUB; }
<THEORY>":fresh"        { update_position(yytext); return TOK_FRESH; }
<THEORY>":msg"          { update_position(yytext); return TOK_MSG; }

<THEORY>":"             { update_position(yytext); return TOK_COLON; }
<THEORY>"_"             { update_position(yytext); return TOK_UNDERSCORE; }
<THEORY>","             { update_position(yytext); return TOK_COMMA; }
<THEORY>"/"             { update_position(yytext); return TOK_SLASH; }
<THEORY>"\\"            { update_position(yytext); return TOK_BSLASH; }
<THEORY>"-"             { update_position(yytext); return TOK_MINUS; }
<THEORY>"+"             { update_position(yytext); return TOK_PLUS; }
<THEORY>"="             { update_position(yytext); return TOK_EQUAL; }
<THEORY>"#"             { update_position(yytext); return TOK_SHARP; }
<THEORY>"."             { update_position(yytext); return TOK_DOT; }
<THEORY>"~"             { update_position(yytext); return TOK_TILDE; }
<THEORY>"$"             { update_position(yytext); return TOK_DOLLOR; }
<THEORY>"!"             { update_position(yytext); return TOK_EXCLAMATION; }
<THEORY>"<"             { update_position(yytext); return TOK_LTHAN; }
<THEORY>">"             { update_position(yytext); return TOK_GTHAN; }
<THEORY>"("             { update_position(yytext); return TOK_LPAREN; }
<THEORY>")"             { update_position(yytext); return TOK_RPAREN; }
<THEORY>"["             { update_position(yytext); return TOK_LSQUARE; }
<THEORY>"]"             { update_position(yytext); return TOK_RSQUARE; }
<THEORY>"{"             { update_position(yytext); return TOK_LCURLY; }
<THEORY>"}"             { update_position(yytext); return TOK_RCURLY; }
<THEORY>"'"             { update_position(yytext); return TOK_SQUO; }
<THEORY>"\""            { update_position(yytext); return TOK_DQUO; }

<THEORY>"^"             { update_position(yytext); return OP_EXP; }
<THEORY>"*"             { update_position(yytext); return OP_MUL; }
<THEORY>"XOR"           { update_position(yytext); return OP_XOR; }
<THEORY>"⊕"             { update_position(yytext); return OP_XOR; }
<THEORY>"++"            { update_position(yytext); return OP_UNION; }
<THEORY>"%+"            { update_position(yytext); return OP_PLUS; }

<THEORY>"functions"     { update_position(yytext); return TOK_FUNCTION; }
<THEORY>"[private]"     { update_position(yytext); return TOK_PRIV; }

<THEORY>"equations"     { update_position(yytext); return TOK_EQUATIONS; }

<THEORY>"builtins"      { update_position(yytext); return TOK_BUILTIN; }
<THEORY>{built_ins}     {
                            yylval.str_val = copy_string(yytext); 
                            update_position(yytext); 
                            return TOK_BUILTIN_FUNCTIONS;
                        }

<THEORY>"macros"        { update_position(yytext); return TOK_MACRO; }

<THEORY>"rule"          { update_position(yytext); return TOK_RULE; }
<THEORY>"-->"           { update_position(yytext); return TOK_ARROW; }
<THEORY>"--["           { update_position(yytext); return TOK_LARROW; }
<THEORY>"]->"           { update_position(yytext); return TOK_RARROW; }
<THEORY>"let"           { update_position(yytext); return TOK_LET; }
<THEORY>"in"            { update_position(yytext); return TOK_IN; }
<THEORY>"no_precomp"    { update_position(yytext); return TOK_NOPRECOMP; }
<THEORY>"modulo"        { update_position(yytext); return TOK_MODULO; }
<THEORY>"color="        { update_position(yytext); return TOK_COLOR; }
<THEORY>"colour="       { update_position(yytext); return TOK_COLOR; }

<THEORY>":="            { update_position(yytext); return TOK_WALRUS; }
<THEORY>{entropy_marks} { 
                            yylval.int_val = ENT_FROM_NAME(yytext); 
                            update_position(yytext); 
                            return TOK_ENTROPY_MARK;
                        }

<THEORY>{natural}       { 
                            yylval.int_val = atoi(yytext); 
                            update_position(yytext);
                            return ARITY;   
                        }
<THEORY>{hexdigit}      {
                            yylval.int_val = strtol(yytext, NULL, 16);
                            update_position(yytext);
                            return HEXDIGIT;
                        }
<THEORY>{ident}         {   
                            yylval.str_val = copy_string(yytext); 
                            update_position(yytext);
                            return IDENT;
                        }
<THEORY>{string}        {
                            yylval.str_val = copy_string(yytext); 
                            update_position(yytext);
                            return STRING;
                        }
<THEORY>{whitespace}    { update_position(yytext); }

<THEORY>"//"            { update_position(yytext); BEGIN(LINE_COMMENT);}
<LINE_COMMENT>\n        { update_position(yytext); BEGIN(THEORY);}
<LINE_COMMENT>[^\n]     { update_position(yytext); }

<THEORY>"/*"            { update_position(yytext); BEGIN(BLOCK_COMMENT); }
<BLOCK_COMMENT>"*/"     { update_position(yytext); BEGIN(THEORY); }
<BLOCK_COMMENT>{all}    { update_position(yytext);}

<THEORY,INITIAL>"#{"    {
                            update_position(yytext); 
                            reserve_content = (char*)calloc(RESERVE_BLOCK_SIZE, sizeof(char));
                            reserve_content_size = 0;
                            reserve_blocks_size = RESERVE_BLOCK_SIZE;
                            PUSH_STATE(YYSTATE);
                            BEGIN(RESERVE); 
                        }
<RESERVE>"#}"           { 
                            update_position(yytext); 
                            reserve_content[reserve_content_size] = '\0';
                            yylval.ast_val = ast_node_new(BLK_Reserve);
                            yylval.ast_val->attr.reserve.str = reserve_content;
                            BEGIN(POP_STATE()); 
                            return TOK_RESERVE;
                        }
<RESERVE>{all}          { 
                            update_position(yytext);
                            if (reserve_content_size + 1 >= reserve_blocks_size) {
                                reserve_blocks_size += RESERVE_BLOCK_SIZE;
                                reserve_content = (char*)realloc(reserve_content, reserve_blocks_size * sizeof(char));
                            } 
                            reserve_content[reserve_content_size++] = yytext[0];
                        }

<INITIAL>{all}          { update_position(yytext); }
%%
