#include "ast.h"
#include "global.h"
#include "syntax.h"
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

extern int yyparse();
extern FILE* yyin;

AstNode* AST = NULL;

int tamarin_parse(const char* input, const char* output)
{
    yyin = fopen(input, "r");
    if (!yyin) {
        fprintf(stderr, "Error: Cannot open file %s\n", input);
        return -1;
    }

    int ret = yyparse();
    if (ret != 0) {
        fprintf(stderr, "Error: Parsing failed\n");
        return -1;
    }

    fclose(yyin);

    FILE* out = fopen(output, "w");
    if (!out) {
        fprintf(stderr, "Error: Cannot open file %s\n", output);
        return -1;
    }
    
    ast2python(AST, out);
    fclose(out);

    ast_tree_destory(AST);
    return 0;
}