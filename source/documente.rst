Contribute to the mobyle2 documentation project
=======================================================


Install the documentation project
---------------------------------------------------------

.. code-block:: sh

    git clone https://github.com/mobyle2/mobyle2.github.com.git
    cd mobyle2.github.com/source
    python bootstrap.py -d
    bin/buildout

Use sphinx, luke
------------------

This documentation uses sphinx and publishes the results using the `sphinxtogithub <http://pypi.python.org/pypi/sphinxtogithub>`_ extension to github pages.
You will need to edit the source files

Eg:

.. code-block:: sh

        vim source/index.rst

Then you'll have to regenerate the documentation

.. code-block:: sh

    cd source && make html



When you have finished:

    - Verify your build by visiting ./index.html with a regular browser
    - Commit ALL the changes you made and what has been regenerated
    - Push them to github
    - When you receive the email notifying the pages regeneration, look at the website_.

.. code-block:: sh

    cd mobyle2.github.com
    git add .
    git commit -am "update doc"
    git push --all



.. _website: http://mobyle2.github.com/

.. vim:set ft=rest sts=4 ts=4 et:
