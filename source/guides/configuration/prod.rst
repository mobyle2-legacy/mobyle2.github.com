.. _prod conf:

Production mode
------------------
This document refers to :ref:`the instance configuration <instance configuration>`.

For security reasons, in production we will use a file: ``etc/sys/settings-prod.cfg`` which is not commited.

This file will override any values define in the regular settings file.

Thus you can override any default like ports & passwords.

That's why at the first run in production the process will fail until you create this file, even empty.

.. vim:set ft=rest sts=4 ts=4 et:
