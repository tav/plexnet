packages = {

    '0.9.8l': {
        'commands': [
            './config shared no-idea no-mdc2 no-rc5 no-krb5 zlib --prefix=%s -L%s -I%s' %
            (PLEXNET_LOCAL, PLEXNET_LIB, PLEXNET_INCLUDE),
            'make',
            'make install'
            ]
        }

    }

versions = ['0.9.8l']
