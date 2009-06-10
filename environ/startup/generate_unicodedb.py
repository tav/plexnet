
def read_table(casefold_file):
    table = {}
    
    # Case folding
    for line in casefold_file:
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        code, status, two, _ = line.split(';')
        code = int(code, 16)
        if status.strip() in ['C', 'F']:
            l = [str(int(c, 16)) for c in two.split(' ') if c]
            table[code] = l

    return table

def write_table(table, f):
    print >>f, "_casefold = {"
    for code, l in table.iteritems():
        print >>f, "  %d : [%s]," % (code, ', '.join(l))
    print >>f, "}"

if __name__ == '__main__':
    casefold_file = open('CaseFolding.txt')
    table = read_table(casefold_file)
    f = open("unicodedb.py", "w")
    write_table(table, f)
    f.close()
