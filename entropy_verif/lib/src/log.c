#include <stdarg.h>
#include <stdio.h>

#include "log.h"

void logging(LogType type, const char* format, ...)
{
    va_list args;
    va_start(args, format);
    char buffer[LOG_BUFFER_SIZE];

    vsnprintf(buffer, LOG_BUFFER_SIZE, format, args);

    switch (type) {
    case Error:
        fprintf(stderr, "[ERROR] %s\n", buffer);
        break;
    case Warning:
        fprintf(stderr, "[WARNING] %s\n", buffer);
        break;
    case Debug:
        fprintf(stdout, "[DEBUG] %s\n", buffer);
        break;
    default:
        fprintf(stderr, "[UNKNOWN] %s\n", buffer);
        break;
    }

    va_end(args);
}

