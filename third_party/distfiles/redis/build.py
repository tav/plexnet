def build(info):
    """Compile Redis."""

    os.chdir(join_path(THIRD_PARTY, 'generic', 'redis'))
    return ("make clean", "make")

# ------------------------------------------------------------------------------
# package metadata
# ------------------------------------------------------------------------------

packages = {

    'commands': build,
    'distfile': "",

    'git-231d758': {
        }

    }

versions = ['git-231d758']
