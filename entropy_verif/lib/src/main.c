#include <assert.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "lib.c"

char* input = NULL;
char* output = NULL;

void print_usage(const char* program_name)
{
    printf("Usage: %s [OPTIONS] INPUT\n", program_name);
    printf("Options:\n");
    printf("  -o, --output FILE    Specify the output file\n");
    printf("  -h, --help           Display this help message\n");
    printf("Arguments:\n");
    printf("  INPUT                Specify the input file\n");
}

int parse_arguments(int argc, char* const argv[])
{
    int opt;
    int option_index = 0;
    static struct option long_options[] = {
        { "output", required_argument, 0, 'o' },
        { "help", no_argument, 0, 'h' },
        { 0, 0, 0, 0 }
    };

    while ((opt = getopt_long(argc, argv, "o:t:h", long_options, &option_index)) != -1) {
        switch (opt) {
        case 'o':
            output = optarg;
            break;
        case 'h':
            return -1;
        default:
            return -1;
        }
    }

    if (optind < argc) {
        input = argv[optind];
    } else {
        fprintf(stderr, "Error: Missing input file\n");
        return -1;
    }

    if (!output) {
        output = "output.spthy";
    }

    return 0;
}

int main(int argc, char* const argv[])
{
    if (-1 == parse_arguments(argc, argv)) {
        print_usage(argv[0]);
        return -1;
    }

#ifdef DEBUG
    extern int yydebug;
    yydebug = 1;
    printf("DEBUG MODE\n");
#endif

    printf("input: %s\n", input);
    printf("output: %s\n", output);

    tamarin_parse(input, output);

    return 0;
}
