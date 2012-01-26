Utiliser le pshell
==================

lancer le pshell pyramid sous minitage

.. code-block:: sh
    
    bin/paster --plugin-pyramid  pshell etc/wsgi/instance.ini#projectapp


sqlalchemy-migrations
=====================

http://readthedocs.org/docs/sqlalchemy-migrate/en/v0.7.2/versioning.html#project-setup


Créer le rep de version des db
-------------------------------
.. code-block:: sh
    
    bin/migrate create src.mrdeveloper/mobyle2.core/src/mobyle2/core/schemas_migrations "mobyle2 project"


Mettre la db sous version
--------------------------

.. code-block:: sh
    
    bin/pyramidpy src.mrdeveloper/mobyle2.core/src/mobyle2/core/schemas_migrations/manage.py version_control \
    postgresql+psycopg2://mobyle2:secret@localhost:5438/mobyle2 \
    src.mrdeveloper/mobyle2.core/src/mobyle2/core/schemas_migrations/

exemple  récuperer le numéro de version 

.. code-block:: sh
    
    bin/pyramidpy src.mrdeveloper/mobyle2.core/src/mobyle2/core/schemas_migrations/manage.py \
    version src.mrdeveloper/mobyle2.core/src/mobyle2/core/schemas_migrations/

Créer un alias du manage du repository
----------------------------------------

créer un alias avec le rép de versions et l'uri de la db 

.. code-block:: sh
    
    bin/migrate manage manage.py --repository="$INS/src.mrdeveloper/mobyle2.core/src/mobyle2/core/schemas_migrations/" \
    --url="postgresql+psycopg2://mobyle2:secret@localhost:5438/mobyle2"

ce qui nous permet dorénavant de taper 

.. code-block:: sh
    
    bin/pyramidpy manage.py db_version

Créer un script de migration
-----------------------------
.. code-block:: sh
    
    bin/pyramidpy manage.py script 'remove_project-and_add_workspace'

Migrer
-------
.. code-block:: sh
    
    bin/pyramidpy manage.py upgrade
    0 -> 1...
    done

    bin/pyramidpy manage.py db_version
    1

Downgrader
-----------
.. code-block:: sh
    
    bin/pyramidpy manage.py downgrade --version 0
    1 -> 0...
    done
    
    bin/pyramidpy manage.py db_version
    0


