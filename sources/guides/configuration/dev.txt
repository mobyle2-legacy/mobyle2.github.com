.. _override settings:

Development mode
------------------
This document refers to :ref:`the instance configuration <instance configuration>`.

**This apply only to local development instances**.

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

.. vim:set ft=rest sts=4 ts=4 et:
