platform2icu = {
    'darwin': 'MacOSX',
    'freebsd': 'FreeBSD',
    'linux': 'Linux',
    'cygwin': 'Cygwin'
    }

ICU_PLATFORM = platform2icu.get(platform)

if ICU_PLATFORM is None:
    raise ValueError("Unknown platform: %s" % platform)

# ------------------------------------------------------------------------------
# package metadata
# ------------------------------------------------------------------------------

packages = {

    '4.0': {
        'config_command': './runConfigureICU',
        'config_flags': (
            '%s --disable-samples --disable-tests --sbindir=%s'
            % (ICU_PLATFORM, PLEXNET_BIN)
            )
        }

    }

versions = ['4.0']
