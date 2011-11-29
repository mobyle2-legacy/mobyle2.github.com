Configuration guide
======================================


.. _instance configuration:

Configuration
---------------------
The ost important configuration file is ``etc/sys/settings.cfg``.


Some of the settings you can find there:

.. code-block:: ini

        [users]
        pyramid=mobyle2

        [passwords]
        admin=XXXXXX

        [db] # parametres postgresql
        user = mobyle2
        password =  ************
        host = localhost
        port = 5432
        name = mobyle2

        [hosts]
        instance=0.0.0.0
        instance1=0.0.0.0
        instance2=0.0.0.0
        instance3=0.0.0.0
        instance4=0.0.0.0
        # l'HOST exterieur d'ou est accessible velruse
        velruse=mobyle2.somewhere.fr
        [ports]
        instance=9090
        instance1=9091
        instance2=9092
        instance3=9093
        instance4=9094
        # le port
        velruse=8080


Please note that it is important to define or verify the configuration settings of:

    - The database access

        **[db]** section of the buildout settings file

    - The filesystem user **in production mode only**

        **users:mobyle2** option of the buildout settings file

    - The passwords

      Some options are security sensitives:

            **db:password** option of the buildout settings file

    - The SMTP parameters

        **[mail]** section of the buildout settings file

It is also important to configure the 'Velruse' address. It must be accessible both from inside and outside the inner network of this backend (browser, reverse proxy, backend).



Relevant configuration settings:

    - **hosts:velruse**: host of the webserver hosting velruse
    - **ports:velruse**: port of the webserver hosting velruse
    - **instance;velruseapp** : the subpath part of the url to velruse (in http://foo/velruse, its velruse)

To set those settings, use the followings sections depending if you are:

    - in :ref:`development mode <override settings>`
    - in :ref:`production mode <prod conf>`

.. toctree::
   :maxdepth: 1


   dev.rst
   prod.rst

.. vim:set ft=rest sts=4 ts=4 et:
