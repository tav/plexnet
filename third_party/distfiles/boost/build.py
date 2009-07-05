def build(info):
    """Compile Boost Jam and Return the boost compile commands."""

    cur_dir = os.getcwd()

    user_config = open('user-config.jam', 'wb')
    user_config.write("using python : 2.6 : %s ;\n" % sys.prefix)
    user_config.close()

    jam_dir = join_path(cur_dir, 'tools', 'jam', 'src')
    os.chdir(jam_dir)

    print_message("Compiling Boost Jam", PROGRESS)
    proc = Popen('./build.sh', shell=True)
    status = proc.wait()
    if status:
        print_message("Error compiling Boost Jam", ERROR)
        sys.exit(1)

    TOOLSET = Popen(['./build.sh', '--guess-toolset'], stdout=PIPE).communicate()[0].strip()

    cmd = """./tools/jam/src/bin.*/bjam -sICU_PATH=%s --user-config=user-config.jam --prefix=%s --toolset=%s --with-thread --with-filesystem --with-regex --with-program_options --with-python --with-system --with-iostreams %s""" % (PLEXNET_LOCAL, PLEXNET_LOCAL, TOOLSET, PARALLEL)

    os.chdir(cur_dir)

    return ("%s stage" % cmd, "%s install" % cmd)

# ------------------------------------------------------------------------------
# package metadata
# ------------------------------------------------------------------------------

packages = {

    'commands': build,

    '1.37a': {
        'deps': ['icu', 'pkgconfig']
        }

    }

versions = ['1.37a']
