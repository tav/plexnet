The `Unicode Standard <http://www.unicode.org>`_ is a character coding system
designed to support the worldwide interchange, processing, and display of the
written texts of the diverse languages and technical disciplines of the modern
world.

To update the sources:

* Get the latest versions of the files from the Unicode Character Database (UCD)
  directory at http://www.unicode.org/Public/UNIDATA/

* The special ``UnihanNumeric.txt`` file is generated from the large Unihan.txt
  file (currently available inside Unihan.zip in the UCD)::

    $ grep Numeric Unihan.txt > UnihanNumeric.txt

  The original ``Unihan.txt`` is not currently needed and need not be included.

* Make sure to put all the files in appropriate version directories.

* Follow the usual procedure.
