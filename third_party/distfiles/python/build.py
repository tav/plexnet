if sys.platform == 'darwin':
    EXTRA_ARGS = "--enable-toolbox-glue --enable-framework=$PLEXNET_LOCAL/framework"
else:
    EXTRA_ARGS = ""

packages = {

    '2.6.4': {
        'config_flags': "--enable-ipv6 --enable-unicode=ucs2 %s" % EXTRA_ARGS
        },

    'env': {
        'CPPFLAGS': "-I%s" % PLEXNET_INCLUDE,
        'LDFLAGS': "-L%s" % PLEXNET_LIB
        },

    'deps': ['zlib', 'bzip2', 'libreadline', 'openssl']

    }

versions = ['2.6.4']
