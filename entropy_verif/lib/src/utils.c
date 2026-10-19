#include <stdarg.h>
#include <stdlib.h>
#include <string.h>

#include "global.h"
#include "utils.h"

/**
 * @description: copy a string
 * @param {char*} str
 * @return {char*}
 */
char* copy_string(const char* str)
{
    char* new_str = malloc(strlen(str) + 1);
    memcpy(new_str, str, strlen(str) + 1);
    return new_str;
}

/**
 * @description: concatenate strings
 * @param {int} str_num
 * @param {...} string list
 * @return {*}
 */
char* concat_string(int str_num, ...)
{
    va_list args;
    int total_length = 0;
    char *result, *p;

    // calculate the total length of the strings
    va_start(args, str_num);
    for (int i = 0; i < str_num; i++) {
        total_length += strlen(va_arg(args, char*));
    }
    va_end(args);

    // allocate memory for the result string
    result = (char*)malloc(total_length + 1);
    if (!result) {
        fprintf(stderr, "Failed to allocate memory\n");
        exit(1);
    }

    // concatenate the strings
    va_start(args, str_num);
    p = result;
    for (int i = 0; i < str_num; i++) {
        char* str = va_arg(args, char*);
        while (*str) {
            *p++ = *str++;
        }
    }
    *p = '\0';
    va_end(args);

    return result;
}
