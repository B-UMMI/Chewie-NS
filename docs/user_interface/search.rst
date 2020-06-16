Search
======

The **Search** button on the sidebar will take the user a page to search alleles in the Chewie-NS database.

Searching for an allele
-----------------------

In order to search for an allele, the user needs to fill the **Allele Sequence** box
with the **DNA Sequence only** of the allele.

.. important:: You can only search for **one** allele at once. Multiple allele sequences will cause errors.

.. figure:: ../resources/sequences_empty.png
    :align: center

    Figure 1: Empty Allele Sequence box. 


By defaulta and when the allele does not exist Chewie-NS's database, a table 
is rendered with a message refering that no matches were found.


**If the allele exists** in Chewie-NS's database, the table will contain the following columns:

- **Schema**: the ID of the schema that the allele belongs to. Clicking on the ID will take you to the :doc:`schema_evaluation` page.
- **Locus ID**: the ID of the locus the allele belongs to. Clicking on the ID will take you to the :doc:`locus_details` page.

.. figure:: ../resources/sequences_filled.png
    :align: center

    Figure 2: Allele Sequence box with an allele sequence with matched results.
