Development installation guide (in EDIT)
===========================================

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


Postgresql postgresql
-----------------------------------------------------------------
- :user: root

.. code-block:: sh

    apt-get install postgresql-8.4
    su postgres -c "createuser mobyle2 -P"
        Enter password for new role:
        Enter it again:
        Shall the new role be a superuser? (y/n) n
        Shall the new role be allowed to create databases? (y/n) y
        Shall the new role be allowed to create more new roles? (y/n) n
    su postgres -c "createdb  -Eutf-8 -O mobyle2 mobyle2"

Please note the postgresql password for future reference.

How to override some settings locally to your instance:
--------------------------------------------------------

It must be accessible both from inside and outside the inner network of this backend (browser, reverse proxy, backend).

Make a local config in the project directory file like


$prefix/pyramid/mobyle2/myconfig.cfg

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


Some nots:
--------------

- It is also important to know that velruse runs inside the webserver but as a separate component.
  So, we must understand that velruse will be attacked via http and the url must be well configured inside etc/sys/settings.cfg to match the local needs.

URLS::

    http://localhost:9091 : application

.. vim:set ft=rest sts=4 ts=4 et:
