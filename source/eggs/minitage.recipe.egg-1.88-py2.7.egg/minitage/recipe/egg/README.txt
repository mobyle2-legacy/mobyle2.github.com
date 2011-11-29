===============================================
minitage.recipe.egg
===============================================


Abstract
-----------------
    - This recipe intends to install eggs and python software
    - Its heavilly inspired by zc.recipe.eggs* and try to completly replace it whereas be API compatbile.
    - You can use it in conjunction with the buildout.minitagificator extension which monkey patch zc.buildout to use minitage recipes.
    - The recipe has a robust offline mode.
    - What we can do that zc.recipe.egg wouldnt do, either at all or not in the way we want to:

        * Don't rely on easy_install to detect and install dependencies, that can lead to versions inccompatibilities
        * Handles and preserve eggs extra dependencies
        * Apply specific patches for eggs based on their name and them generate a specific egg with a specific version, burried in the buildout via the "versions".
        * Make the minitage environnent comes into the environment when building if any, making compilation steps easy if you have declared and build the neccessary dependencies.
        * Be able to install unindexed at all stuff, just by precising url to install, that can be even an automatic checkout from any repository.
        * You have hooks to play with the recipe, if it doesnt fit exactly to your need, you can hook for a specific egg at any point of the build.
        * Check md5 on indexes which append md5 fragments on urls, to verify package integrity

    - If you need scripts generation, just use the minitage.recipe:scripts recipe, it's a specialized recipe of this one. Its use is similar, with just a bunch more options.

Specific options
-----------------

Please look for options at : http://pypi.python.org/pypi/minitage.recipe.common#options-shared-by-all-the-recipes

* urls

    See the shared options for more information on how to set them.
    This is how to specify a distrbituion with is not indexed on pypi and where find-links dance can not work.
    This is also how to specify to install something from svn::

        urls = http://foo.tld/my_super_egg|svn|666 # checkout and install this egg from svn at revision 666

    The directory bit can be used to set the subdirectory to cd to find the setup.py
    eg::

        urls = http://foo.tld/my_super_egg|svn|666|subdirectory # checkout and install this egg from svn at revision 666 and will cd to subdirectory to do the setup.py dance


* eggs

    A list of egg requirements to install without the version specs bit.::

        Plone
        lxml

* EGGNAME-patch-options
    patch binary to use for this egg
* EGGNAME-patch-binary
    Options to give to the patch program when applying patches for this egg
* EGGNAME-patches
    Specific patchs for an egg name to apply at install time::

        Django-patches = ${buildout:directory}/foo.patch

* EGGNAME-UNAME-patches
    Same as previous, but will just occurs on this UNAME specifc OS (linux|freebsd|darwin)
    Specific patchs for an egg name to apply at install time::

        Django-linux-patches = ${buildout:directory}/foo.patch

* EGGNAME-VERSION-patches
    patches apply only on this specific version

* EGGNAME-VERSION-UNAME-patches
    patches apply only on this specific version


* versions
    Default to buildout:versions. versions part to use to pin the version of the installed eggs.
    It defaults to buildout's one
* index
    Custom eggs index (not pypi/simple). It defaults to buildout's one
* install-previous-version
    install previous version of an egg (recursivly on errors)
* find-links
    additionnal links vhere we can find eggs. It defaults to buildout's one
* extra-paths
        Extra paths to include in a generated script or at build time.
* relative-paths
    If set to true, then egg paths will be generated relative to the script path.
    This allows a buildout to be moved without breaking egg paths.
    This option can be set in either the script section or in the buildout section.
* Specifying the python to use, two ways:

    * python
        The name of a section to get the Python executable from. If not specified, then
        the buildout python option is used. The Python executable is found in the
        executable option of the named section. It defaults to buildout's one
    * executable
        path to the python executable to use.

* hooks

  A hook is in the form /path/to/hook:CALLABLE::

        myhook=${buildout:directory}/toto.py:foo

  Where we have toto.py::

        def foo(options, buildout):
            return 'Hourray'

  The complete possible hooks list:

    * post-download-hook
        hook executed after each download
    * post-checkout-hook
        hook executed after each checkout
    * EGGNAME-pre-setup-hook
        hook executed before running the setup.py dance
    * EGGNAME-post-setup-hook
        hook executed after running the setup.py dance


BDIST EGGS OPTIONS:

You can have global and per distributions bdist_ext options.

* (EGGNAME-)define

    A comma-separated list of names of C preprocessor variables to define.

* (EGGNAME-)undef

    A comman separated list of names of C preprocessor variables to undefine.

* (EGGNAME-)link-objects

    The name of an link object to link against. Due to limitations in distutils and desprite the option name, only a single link object can be specified.

* (EGGNAME-)debug

    Compile/link with debugging information

* (EGGNAME-)force

    Forcibly build everything (ignore file timestamps)

* (EGGNAME-)compiler

    Specify the compiler type

* (EGGNAME-)swig

    The path to the swig executable
* (EGGNAME-)swig-cpp

    Make SWIG create C++ files (default is C)

* (EGGNAME-)swig-opts

    List of SWIG command line options


* (EGGNAME-)bdistext-OPTIONNAME

    will add an entry in the setup.cfg's bdist_egg like:

        OPTIONNAME = foo

Patches
--------

    * When you use patches for an egg, his version will become ::

        Django-1.0-final -> Django-1.0-final-ZMinitagePatched-$PatchesNamesComputation$

    * This name have some Z* inside to make some precedence on other eggs at the same version. (see setuptools naming scheme)
    * After that the egg is created, the buildout is backed up and patched to point to this version
    * Thus, you can have in your common egg cache, this egg for your specific project, and the classical one for others.
      This can be interessant, for example, for the zope RelStorage patch to apply on ZODB code.

Detailled documentation
-------------------------
