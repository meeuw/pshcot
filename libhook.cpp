#include <stdarg.h>
extern "C" {
struct pycallback {
    int parameters;
    long long(*callback)(long long *a);
};

struct pycallback pycallbacks[999];

int registercallback(int i, long long(*callback)(long long *a), int parameters) {
    pycallbacks[i].parameters = parameters;
    pycallbacks[i].callback = callback;
}
}
