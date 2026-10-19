#ifndef GLOBAL_H
#define GLOBAL_H

#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef YYPARSER
#include "yacc.tab.h"
#define ENDFILE 0
#endif
#include "ast.h"

/****************************************************************
 *  Global Flags
 ****************************************************************/
extern bool FlagError;

/****************************************************************
 *  Global Variables
 ****************************************************************/
extern AstNode* AST;

#endif