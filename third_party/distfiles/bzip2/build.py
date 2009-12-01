if sys.platform == 'darwin':
    BZIP2_MAKEFILE = 'Makefile-libbz2_dylib'
else:
    BZIP2_MAKEFILE = 'Makefile-libbz2_so'

packages = {

    '1.0.5': {
        'commands': [
            'make install PREFIX=%s' % PLEXNET_LOCAL,
            'make clean',
            'make -f %s all PREFIX=%s' % (BZIP2_MAKEFILE, PLEXNET_LOCAL)
            ]
        }

    }

versions = ['1.0.5']
