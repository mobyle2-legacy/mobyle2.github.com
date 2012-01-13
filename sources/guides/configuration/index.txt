Configuration guide
======================================


.. _instance configuration:

Configuration
---------------------
The most important configuration file is ``etc/sys/settings.cfg``.


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

            **[db]** sectionof the buildout settings file
            **[mail]** sectionof the buildout settings file

    - The SMTP parameters

        **[mail]** section of the buildout settings file

It is also important to configure the 'Velruse' address. It must be accessible both from inside and outside the inner network of this backend (browser, reverse proxy, backend).



Relevant configuration settings:

    - **hosts:velruse**: host of the webserver hosting velruse
    - **ports:velruse**: port of the webserver hosting velruse
    - **instance:velruseapp** : the subpath part of the url to velruse (in http://foo/velruse, its velruse)

To set those settings, use the followings sections depending if you are:

    - in :ref:`development mode <override settings>`
    - in :ref:`production mode <prod conf>`


Things to do at the first run
================================

- Create a superuser named "mynick" with "secret" as password

.. code-block:: ini
    
  . sys/share/minitage.env
  ./shell.sh
  >>> from mobyle2.core.tools import create_user
  >>> create_user("mynick", "secret", True)

You can then log on the portal with those credentials to do administrative tasks or give privileges to another already or future user   

Roles configuration
=========================== 
A special word of anonym login, we add in the "mobyle2.core.auth.ACLAuthorizationPolicy" a special case when we are not loggued, the anonym principal is added to the list of known principals. For this reason, do not ever rename this role !!!

Permissions configuration
===========================
The security model of mobyle2 is all about roles.

You attribute roles to users or groups.

Then you allow or deny roles to do relevant actions.

There are two levels of acls: globals or per project.
On the project level, permissions are related to projects and  its inner objects like services, jobs and notebooks.


- At the global level, the permission must be prefixed by 
      
      
        - **mobyle2 > global_** : global acls
        - **mobyle2 > user_**   : user management
        - **mobyle2 > group_**  : group management

- At the project level by either
                                      
        - **mobyle2 > project_XXX**   : project acls
        - **mobyle2 > service_XXX**   : service acls
        - **mobyle2 > notebook_XXX**  : notebook acls
        - **mobyle2 > job_XXX**       : jobs acls


You cannot rename permissions or you ll have to change the webserver code as permissions are hardcoded in the view declarations, the pyramid way to configure view accesses.
The only thing you can do is to edit their descriptions.



.. toctree::
   :maxdepth: 1


   dev.rst
   prod.rst

.. vim:set ft=rest sts=4 ts=4 et:
