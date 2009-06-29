packages = {

    '0.23': {
        'config_flags': (
            '--mandir=%s --enable-indirect-deps '
            '--with-pc-path=%s/lib/pkgconfig:%s/share/pkgconfig' % (
                PLEXNET_MAN, PLEXNET_LOCAL, PLEXNET_LOCAL
                )
            )
        }

    }

versions = ['0.23']
