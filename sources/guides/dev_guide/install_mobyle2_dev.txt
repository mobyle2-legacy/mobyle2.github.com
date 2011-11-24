
Install your mobyle2 instnace
++++++++++++++++++++++++++++++++++


Create a mintiage user and install mandatory requirements
--------------------------------------------------------------
-:user: root

.. code-block:: sh

        export prefix=$HOME/minitage
        export python=$prefix/tools/python
        mkdir -p $prefix
        useradd -d $prefix -m mobyle2
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

When the install crashes, we need to touch the missing production-related settings file which MUST not be commited.
- :user: mobyle2

.. code-block:: sh

    touch $prefix/pyramid/mobyle2/etc/sys/settings-prod.cfg

The project shell profile
------------------------------
Minitage provide a shell sourcable file that helps you to use the constructed minitage environment.
It will update common unix environment variables to grab all your project dependencies along your current shell.
For exemple, it will put all related binaries inside your current ``$PATH`` variable.

You can generate one by issuing the following command:

.. code-block:: sh

    miniemrge -NE mobyle2

Think to regenerate it each once you touch to the project minibuilds.

Now, to use it in your current shell, please source it:

.. code-block:: sh

    . $prefix/pyramid/mobyle2/sys/share/minitage/minitage.env

***PLEASE Always activate the environment shell before doing anything to the project.***

Postgresql installation
-----------------------------------------------------------------

You can install an instance of a postgresql server inside a subdirectory of your minitage based project.
This is prettry easy:

.. code-block:: sh

    $MT/bin/paster create -t minitage.instances.postgresql mobyle2 project_dependencies='' project_eggs='' inside_minitage=y db_name=mobyle2 db_port=5438 db_password=secret db_user=mobyle2 db_host=localhost

You can start the server with:

.. code-block:: sh

        $prefix/sys/etc/init.d/mobyle2_postgresql.mobyle2 restart

Will install a database named ``mobyle2`` listening on the port ``5438`` and which lives under ``$prefix/pyramid/mobyle2/sys/``.

B./sys/etc/init.d/mobyle2_postgresql.mobyle2y default the superuser is named as ``your current loggued user`` and the database owner is ``mobyle2``.

Some wrappers have been generated, please look inside ``sys/bin``.
They are very useful as they make a lot of assumptions like setting automaticly the host & port to connect to (our database).
EG

.. code-block:: sh

        mobyle2.psql

Please note the postgresql password for future reference.


Openldap installation (not mandatory)
-----------------------------------------
.. code-block:: sh

    $MT/bin/easy_install -U minitage.paste.extras
    $MT/bin/paster create -t minitage.instances.openldap mobyle2 db_suffix=net db_orga=mobyle2 ssl_port=6636  db_port=3389 db_user=$(whoami) db_password=secret  --no-interactive

Init script to start the server::

    ./sys/etc/init.d/openldap_mobyle2_mobyle2.net 
    
You have preconfigured wrappers to any ldap tools inside ``sys/bin`` as usual.                                 


How to override some settings locally to your instance:
--------------------------------------------------------

It must be accessible both from inside and outside the inner network of this backend (browser, reverse proxy, backend).

Make a local config in the project directory file like ``$prefix/pyramid/mobyle2/myconfig.cfg``.

.. code-block:: sh

    touch myconfig.cfg

Input any changes you want after extending the dev buildout configuration:
EG:

.. code-block:: ini


    [buildout]
    extends=minitage.buildout-dev.cfg
    [db]
    port=5439



logrotate & init script installation
-----------------------------------------------------------------
- :user: root

.. code-block:: sh

    ln -s $prefix/pyramid/mobyle2/etc/init.d/supervisor.initd /etc/init.d/supervisor.mobyle2
    ln -s $prefix/pyramid/mobyle2/etc/logrotate.conf /etc/logrotate.d/mobyle2
    update-rc.d -f supervisor.mobyle2 defaults 99

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





Some nots:
--------------

- It is also important to know that velruse runs inside the webserver but as a separate component.
  So, we must understand that velruse will be attacked via http and the url must be well configured inside etc/sys/settings.cfg to match the local needs.

URLS::

    http://localhost:9091 : application

.. vim:set ft=rest sts=4 ts=4 et:
