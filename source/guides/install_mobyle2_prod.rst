Production installation guide
======================================

Create a minitage user and install mandatory requirements
--------------------------------------------------------------
-:user: root

.. code-block:: sh

        mkdir -p /opt/minitage
        useradd -d /opt/minitage -m mobyle2
        apt-get install build-essential m4 libtool pkg-config autoconf gettext bzip2 groff man-db automake libsigc++-2.0-dev tcl8.4
        chown -Rf mobyle2 /opt/minitage


Minitage Installation
--------------------------
- :user: mobyle2

.. code-block:: sh

    export prefix=$HOME/
    export python=$HOME/tools/python
    mkdir -p $python
    cd $python
    wget --no-check-certificate https://github.com/minitage/minitage.shell/raw/master/PyBootstrapper.sh
    bash ./PyBootstrapper.sh $python
    /opt/minitage/tools/python/bin/virtualenv --no-site-packages --distribute /opt/minitage/
    . /opt/minitage/bin/activate
    easy_install -U minitage.core
    minimerge -s

Mobyle2 base Installation
-----------------------------------------------------------------
- :user: mobyle2

.. code-block:: sh

        cd /opt/minitage/minilays/
        git clone https://github.com/mobyle2/mobyle2.minilay.git
        ssh-keygen -> enregistrer la clé dans les repos github comme deploy key
        minimerge -av mobyle2-prod

When the install crashes, we need to touch the missing production-related settings file which MUST not be commited.
- :user: mobyle2

.. code-block:: sh

    touch /opt/minitage/pyramid/mobyle2-prod/etc/sys/settings-prod.cfg


Configuring postgresql
------------------------
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


Configuring ldap
------------------------
- :user: root

.. code-block:: sh

    apt-get install slapd ldap-utils
    dpkg-reconfigure -plow slapd
        Omit OpenLDAP server configuration? no
        DNS domain name: mobyle2.rpbs.univ-paris-diderot.fr
        orga name ? mobyle2
        password? **** (postgresql)


Ajout d'un utilisateur de test toto, mdp toto

.. code-block:: sh

    ldapadd -W -x -D "cn=admin,dc=mobyle2,dc=rpbs,dc=univ-paris-diderot,dc=fr" -f /opt/minitage/pyramid/mobyle2-prod/rpbs.ldif  -c -v
    # verify # (mdp toto)
    ldapsearch  -W -x -D "cn=toto,dc=people,dc=mobyle2,dc=rpbs,dc=univ-paris-diderot,dc=fr"  -b dc=people,dc=mobyle2,dc=rpbs,dc=univ-paris-diderot,dc=fr

password is the same as mobyle2 psql


Configuration
----------------
Make your changes inside ``etc/sys/settings-prod.cfg``.
Please refer to the :ref:`prod conf` section of this manual.


logrotate & init script installation
-----------------------------------------------------------------
- :user: root

.. code-block:: sh

    ln -s /opt/minitage/pyramid/mobyle2-prod/etc/init.d/supervisor.initd /etc/init.d/supervisor.mobyle2
    ln -s /opt/minitage/pyramid/mobyle2-prod/etc/logrotate.conf /etc/logrotate.d/mobyle2
    update-rc.d -f supervisor.mobyle2 defaults 99

Launch the application in foreground
-----------------------------------------------------------------

- :user: mobyle2

.. code-block:: sh

    cd /opt/minitage/pyramid/mobyle2-prod
    . sys/share/minitage/minitage.env
    ./bin/gunicorn_paster etc/wsgi/instance1.ini

Launch the application via the supervisor daemon
-----------------------------------------------------------------
- :user: root

.. code-block:: sh

    /etc/init.d/supervisor.mobyle2 restart


Use the supervisor wrapper
-----------------------------------------------------------------
- :user: mobyle2

.. code-block:: sh

    cd /opt/minitage/pyramid/mobyle2-prod
    . sys/share/minitage/minitage.env
    ./bin/supervisorctl --help
    EX: ./bin/supervisorctl restart instance1


URLS::

    http://localhost:9090 : Supervisor
    http://localhost:9091 : application

.. vim:set ft=rest sts=4 ts=4 et:
