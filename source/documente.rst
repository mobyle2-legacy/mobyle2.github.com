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

This documentation use sphinx and publish the result using `sphinxtogithub <http://pypi.python.org/pypi/sphinxtogithub>`_ extension to github pages.
You well need to edit files in source

Eg:

.. code-block:: sh

        vim source/index.rst

Then you ll have to regenerate the documentation

.. code-block:: sh

    cd source && make html


When you have finished:

    - Verify your build by visiting ./index.html with a regular browser
    - Commit ALL the changes you made and what has been regenerated
    - Push them to github
    - When you received the email notifying the pages regeneration, look the website_.



.. _website: http://mobyle2.github.com/

.. vim:set ft=rest sts=4 ts=4 et:
