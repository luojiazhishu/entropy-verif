CC = gcc
OUTDIR = build
CFLAGS := -I./include -I./$(OUTDIR)/yacc -std=gnu11 

ifeq ($(ENV), release)
	CFLAGS += -O3
else
	CFLAGS += -g -Wall
	ifeq ($(ENV), debug)
		CFLAGS += -DDEBUG
	endif
endif

COMMON_SRCS := yacc/yacc.tab.c lex/lex.yy.c src/ast.c src/utils.c src/syntax.c src/log.c

TARGET = $(OUTDIR)/tamarin+
LIB_TARGET = $(OUTDIR)/libtamarin.so

TARGET_SRCS := $(COMMON_SRCS) src/main.c
LIB_TARGET_SRCS := $(COMMON_SRCS) src/lib.c

TARGET_OBJS := $(addprefix $(OUTDIR)/, $(TARGET_SRCS:.c=.o))
LIB_TARGET_OBJS := $(addprefix $(OUTDIR)/, $(LIB_TARGET_SRCS:.c=.o))

$(LIB_TARGET): CFLAGS += -fPIC 

.PHONY: test clean 
all: $(TARGET)
lib: $(LIB_TARGET)

$(OUTDIR):
	@mkdir -p $(OUTDIR)/src
	@mkdir -p $(OUTDIR)/lex
	@mkdir -p $(OUTDIR)/yacc

$(OUTDIR)/lex/lex.yy.c: lex/lex.l 
	flex -o $@ lex/lex.l

$(OUTDIR)/yacc/yacc.tab.c: yacc/yacc.y 
	bison --yacc -dv -o $@ yacc/yacc.y 

$(OUTDIR)/%.o: %.c 
	$(CC) $(CFLAGS) -c $< -o $@

$(TARGET): $(OUTDIR) $(TARGET_OBJS)
	$(CC) $(CFLAGS) $(TARGET_OBJS) -o $(TARGET)

${LIB_TARGET}: $(OUTDIR) $(LIB_TARGET_OBJS)
	$(CC) $(CFLAGS) -shared $(LIB_TARGET_OBJS) -o $(LIB_TARGET)

test: $(TARGET)
	$(TARGET) -o ./test/output.spthy ./test/test.spthy

valgrind:
	@bash ./test/valgrind/run.sh $(TARGET)

clean:
	@rm -rf lex/lex.yy.c yacc/yacc.tab.c build
