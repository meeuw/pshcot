#!/usr/bin/python3
import fileinput
import re
import json

callbackcode = '''
'''
classes = {}
functions = []
for line in fileinput.input():
    if not 'undefined reference to' in line: continue
    m = re.search(r'`(.*)\'', line)
    undefined = m.groups(1)[0]
    if '::' in undefined:
        s = undefined.split('::')
        if not s[0] in classes:
            classes[s[0]] = []
        if not s[1] in classes[s[0]]:
            classes[s[0]].append(s[1])
    else:
        if undefined not in functions:
            functions.append(undefined)

def parsemethod(name, method, index):
    m = re.match(r'(.*)\((.*)\)', method)
    method_name = m.group(1)
    if m.group(2):
        s = m.group(2).split(',')
    else:
        s = []
    params = []
    letter = 'a'
    cpybuf = 'buf[0] = (long long)this;'
    i = 1
    for param in s:
        p = chr(i+ord('a'))
        params.append(param+' '+p)
        cpybuf += "buf[%i] = (long long)%s; " % (i, p)
        i += 1
    if method_name == name:
        ret = ''
        retret = ''
    else:
        ret = 'long long'
        retret = 'return ret;'
    return {
        'name': name,
        'ret':ret,
        'retret':retret,
        'method_name':method_name,
        'params': ", ".join(params),
        'parameters': len(s)+1,
        'cpybuf': cpybuf,
        'index': index,
    }

print('''
#include <stdarg.h>
#include <cstdio>
struct pycallback {
    int parameters;
    long long(*callback)(long long *a);
};

extern struct pycallback pycallbacks[999]; //FIXME
''')

index = 0
for name, methods in classes.items():
    print('class %s {' % name)
    for method in methods:
        print('    %(ret)s %(method_name)s(%(params)s);' % parsemethod(name, method, index))
    print('};')

pycallbacks = {}
for name, methods in classes.items():
    for method in methods:
        pycallbacks[name+"::"+method] = index
        p = parsemethod(name, method, index)
        print('''%(ret)s %(name)s::%(method_name)s(%(params)s)
{
    long long *buf = new long long[%(parameters)i];
    %(cpybuf)s
    long long ret = 0;
    if (pycallbacks[%(index)i].callback) {
        ret = pycallbacks[%(index)i].callback(buf);
    }
    delete buf;
    %(retret)s
}
''' % p)
        index += 1

print('extern "C" {')
for function in functions:
    if function == 'main': continue
    if 'gcov' in function: continue
    pycallbacks[function] = index
    print('''
long long %(function)s(long long a, ...)
{
    long long parameters = pycallbacks[%(index)i].parameters;
    long long *buf = new long long[parameters];
    if (parameters) {
        va_list args;
        va_start(args, a);
        buf[0] = a;
        for (int i = 1; i < parameters; i++) {
            buf[i] = va_arg(args, long long);
        }
        va_end(args);
    }
    long long ret = 0;
    if (pycallbacks[%(index)i].callback) {
        ret = pycallbacks[%(index)i].callback(buf);
    }
    delete buf;
    return ret;
}
''' % {'function':function, 'index':index})
    index += 1
print('}')
print('/* pycallbacks = '+json.dumps(pycallbacks)+' */')
