#ifndef LOG_H
#define LOG_H

#define LOG_BUFFER_SIZE 1024

typedef enum {
    Error,
    Warning,
    Debug,
} LogType;

void logging(LogType type, const char* format, ...);

#define ERROR(format, ...) logging(Error, format, ##__VA_ARGS__)
#define WARNING(format, ...) logging(Warning, format, ##__VA_ARGS__)
#define DEBUG(format, ...) logging(Debug, format, ##__VA_ARGS__)

#endif
