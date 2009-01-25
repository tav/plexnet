# ========================
# Bash Support for Plexnet
# ========================

# Placed into the Public Domain by tav <tav@espians.com>

# @/@ do ``man bash`` to get info on all from ``complete`` to ``compgen`` to ...

# -------------
# What is This?
# -------------

# Reading documentation and remembering commands can be quite a hassle. This 
# script takes advantage of bash's programmable completion to provide useful
# command and parameter listings on tab-completion.

# ------------
# Installation
# ------------

# To use this, simply use the builtin bash command ``source`` on this file, e.g.

#     $ source /path/to/this/file

# To enable completion this support permanently, simply add the line to the
# appropriate personal initialisation files, e.g. ~/.bash_profile, ~/.bashrc,
# ~/.profile, &c.

# A recommended method is to first check for this file's existence, e.g.

#     [ -f /path/to/this/file ] && source /path/to/this/file

# You should now be able to take advantage of all of Plexnet's features. Enjoy.

# ------------------------------------------------------------------------------
# useful variables
# ------------------------------------------------------------------------------

UNAME=$(uname -s)

# ------------------------------------------------------------------------------
# exit if PLEXNET_ROOT is not set
# ------------------------------------------------------------------------------

if [ ! "$PLEXNET_ROOT" ]; then
	echo "The shell variable PLEXNET_ROOT needs to be set to the Plexnet root directory."
    exit
fi

# ------------------------------------------------------------------------------
# set/extend some variables
# ------------------------------------------------------------------------------

if [ "$PLEXNET_ROOT" ]; then

    export PLEXNET_LOCAL=$PLEXNET_ROOT/environ/local

    if [ $PATH ]; then
        export PATH=$PLEXNET_ROOT/environ/startup:$PLEXNET_LOCAL/bin:$PLEXNET_LOCAL/freeswitch/bin:$PATH
    else
        export PATH=$PLEXNET_ROOT/environ/startup:$PLEXNET_LOCAL/bin:$PLEXNET_LOCAL/freeswitch/bin
    fi

    if [ $UNAME == "Darwin" ]; then
        export PATH=$PLEXNET_ROOT/source/client/osx:$PATH
        export DYLD_FALLBACK_LIBRARY_PATH=$PLEXNET_LOCAL/lib:$PLEXNET_LOCAL/freeswitch/lib:$DYLD_LIBRARY_PATH
    fi

    if [ $UNAME == "Linux" ]; then
        export PATH=$PLEXNET_ROOT/source/client/linux:$PATH
        export LD_LIBRARY_PATH=$PLEXNET_LOCAL/lib:$LD_LIBRARY_PATH
    fi

    if [ $PYTHONPATH ]; then
        export PYTHONPATH=$PLEXNET_ROOT/environ/startup:$PYTHONPATH
    else
        export PYTHONPATH=$PLEXNET_ROOT/environ/startup
    fi

    if [ $MANPATH ]; then
        export MANPATH=$PLEXNET_ROOT/documentation/manpage:$PLEXNET_LOCAL/man:$MANPATH
    else
        export MANPATH=$PLEXNET_ROOT/documentation/manpage:$PLEXNET_LOCAL/man
    fi

fi

if [ "$1" == "install" ]; then
    export PLEXNET_INSTALLED="true"
fi

# ------------------------------------------------------------------------------
# utility funktions
# ------------------------------------------------------------------------------

have() {
	unset -v have
	type $1 &> /dev/null && have="yes"
}

# use gnu sed if we have it

[ $UNAME != Linux ] && have gsed && alias sed=gsed

# ------------------------------------------------------------------------------
# define our kompleter funktion
# ------------------------------------------------------------------------------

# $1 -- application
# $2 -- current word
# $3 -- previous word
# $COMP_CWORD -- the index of the current word
# $COMP_WORDS -- array of words
# --commands # --sub-commands # context-specific commands

have plexnet &&
_plexnet_completion() {
    if [ "$2" ]; then
        COMPREPLY=( $( $1 --list-options | grep "^$2" ) )
    else
        COMPREPLY=( $( $1 --list-options ) )
    fi
    return 0
}

# ------------------------------------------------------------------------------
# work out if we are running within an appropriate version of bash, i.e. v2.04+
# ------------------------------------------------------------------------------

bash_version=${BASH_VERSION%.*} # $BASH_VERSION normally looks something
                                # like ``2.05b.0(1)-release``

major_version=${bash_version%.*}
minor_version=${bash_version#*.}

if [ "$PS1" ] && [ $major_version -ge 2 ]; then 
    # we should be in an interaktive shell
    appropriate_bash_version=true;
fi

# ------------------------------------------------------------------------------
# set us up the kompletion!
# ------------------------------------------------------------------------------

if [ "$appropriate_bash_version" = "true" ] && [ "$have" ]; then

    # first, turn on the extended globbing and programmable kompletion
    shopt -s extglob progcomp

    # register completers
    complete -o default -F _plexnet_completion plexnet
    complete -o default -F _plexent_completion local-edit

    # and finally, register files with spesifik kommands
    complete -f -X '!*.plexnet' install-plexnet-package

    # '!*.@([Pp][Rr][Gg]|[Cc][Ll][Pp])' harbour gharbour hbpp

fi

# ------------------------------------------------------------------------------
# klean up after ourselves
# ------------------------------------------------------------------------------

unset bash_version minor_version major_version appropriate_bash_version
unset have
