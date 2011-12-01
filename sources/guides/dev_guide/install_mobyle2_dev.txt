
Install your mobyle2 instance
++++++++++++++++++++++++++++++++++


Create a minitage user and install mandatory requirements
--------------------------------------------------------------
-:user: root

.. code-block:: sh

        export prefix=$HOME/minitage
        export python=$prefix/tools/python
        mkdir -p $prefix
        useradd -d $prefix -s bash -m mobyle2
        apt-get install build-essential m4 libtool pkg-config autoconf gettext bzip2 groff man-db automake libsigc++-2.0-dev tcl8.4
        chown -Rf mobyle2 $prefix


Minitage Installation
--------------------------
.. code-block:: sh

    export prefix=$HOME/
    export python=$HOME/tools/python
    mkdir -p $python
    cd $python
    wget --no-check-certificate https://github.com/minitage/minitage.shell/raw/master/PyBootstrapper.sh
    bash ./PyBootstrapper.sh $python
    $prefix/tools/python/bin/virtualenv --no-site-packages --distribute $prefix/
    . $prefix/bin/activate
    easy_install -U minitage.core
    minimerge -s

Mobyle2 base Installation
-----------------------------------------------------------------
- :user: mobyle2

.. code-block:: sh

        cd $PREFIX/minilays/
        git clone https://github.com/mobyle2/mobyle2.minilay.git
        ssh-keygen -> enregistrer la clé dans les repos github comme deploy key
        minimerge -av mobyle2


The project shell profile
------------------------------
Minitage provides a shell sourceable file that helps you using the constructed minitage environment.
It will update common unix environment variables to grab all your project dependencies along your current shell.
For example, it will put all related binaries inside your current ``$PATH`` variable.

You can generate one by issuing the following command:

.. code-block:: sh

    minimerge -NE mobyle2

Remember to regenerate it each time you modify the project minibuilds.

Now, to use it in your current shell, please source it:

.. code-block:: sh

    . $prefix/pyramid/mobyle2/sys/share/minitage/minitage.env

**PLEASE Always activate the environment shell before doing anything to the project.**

Postgresql installation
-----------------------------------------------------------------

You can install an instance of a postgresql server inside a subdirectory of your minitage based project.
This is pretty easy:

.. code-block:: sh

    $prefix/bin/paster create -t minitage.instances.postgresql mobyle2 project_dependencies='' project_eggs='' inside_minitage=y db_name=mobyle2 db_port=5438 db_password=secret db_user=mobyle2 db_host=localhost

You can start the server with:

.. code-block:: sh

        $prefix/sys/etc/init.d/mobyle2_postgresql.mobyle2 restart

It will install a database named ``mobyle2`` listening on the port ``5438`` and which lives under ``$prefix/pyramid/mobyle2/sys/``.

B./sys/etc/init.d/mobyle2_postgresql.mobyle2y default the superuser is named as ``your current logged user`` and the database owner is ``mobyle2``.

Some wrappers have been generated, please look inside ``sys/bin``.
They are very useful as they make a lot of assumptions like setting automatically the host & port to connect to (our database).
EG

.. code-block:: sh

        mobyle2.psql

Please note the postgresql password for future reference.


Openldap installation (not mandatory)
-----------------------------------------
.. code-block:: sh

    $MT/bin/easy_install -U minitage.paste.extras
    $MT/bin/paster create -t minitage.instances.openldap mobyle2 db_suffix=net db_orga=mobyle2 ssl_port=6636  db_port=3389 db_user=$(whoami) db_password=secret db_host=127.0.0.1  --no-interactive

Mettre ::

    dn: dc=mobyle2,dc=net
    objectClass: dcObject
    objectClass: organization
    dc: mobyle2
    o: Example Corporation
    description: The Example Corporation

    dn: dc=people,dc=mobyle2,dc=net
    objectClass: dcObject
    objectClass: organization
    dc: people
    o: Example Corporation
    description: The Example Corporation

    dn: dc=people,dc=mobyle2,dc=net
    objectClass: dcObject
    objectClass: organization
    dc: people
    o: Example Corporation
    description:: VGhlIEV4YW1wbGUgQ29ycG9yYXRpb24g
    structuralObjectClass: organization
    creatorsName: cn=kiorky,dc=mobyle2,dc=net
    modifiersName: cn=kiorky,dc=mobyle2,dc=net

    dn: cn=toto,dc=people,dc=mobyle2,dc=net
    gidNumber: 2
    objectClass: posixAccount
    objectClass: top
    objectClass: inetOrgPerson
    objectClass: organizationalPerson
    objectClass: person
    uidNumber: 1
    uid: 1
    homeDirectory: /where
    sn: toto
    cn: toto
    structuralObjectClass: inetOrgPerson
    creatorsName: cn=kiorky,dc=mobyle2,dc=net
    createTimestamp: 20111124184725Z
    mail: toto@foo.com
    userPassword:: e1NTSEF9MmI1THl6UEI0NTFvTW5SdkMzV1Q4QmJUYlNJL3hwWm9iWDg1TEE9PQ==
    modifiersName: cn=kiorky,dc=mobyle2,dc=net

Dans un fichier base.ldif

puis

.. code-block:: sh

    ./sys/bin/mobyle2.net.slapadd  -l base.ldif

Init script to start the server::

    ./sys/etc/init.d/openldap_mobyle2_mobyle2.net

You have preconfigured wrappers to any ldap tools inside ``sys/bin`` as usual.

On peut ensuite se connecter au serveur ldap pour nos tests.


How to override some settings locally to your instance:
--------------------------------------------------------
Please refer to the :ref:`override settings` section.


Launch the application in foreground
-----------------------------------------------------------------

- :user: mobyle2

.. code-block:: sh

    cd $prefix/pyramid/mobyle2
    . sys/share/minitage/minitage.env
    ./p.sh

Update your mobyle2 instance
+++++++++++++++++++++++++++++

This is a minimum 2 steps thing

- You need first to update your project:

.. code-block:: sh

    cd $prefix/pyramid/mobyle2
    git pull


Then you can update python packages or sources grabbed on various repositories for your project

.. code-block:: sh

    ./bin/develop up -v

On any suspicious output, just update the code by hand of the relative modules inside ``src.mrdeveloper/``.


Some notes:
--------------

- It is also important to know that velruse runs inside the webserver but as a separate component.
  So, we must understand that velruse will be attacked via http and the url must be well configured inside etc/sys/settings.cfg to match the local needs.

URLS::

    http://localhost:9091 : application




.. vim:set ft=rest sts=4 ts=4 et:
