Locus Details
=============

This page displays details about a single locus.

Histogram
---------

The histogram represents the **distribution of sequence size in 
base pairs (x-axis)** for a **number of alelles (y-axis)**.

For example, **Figure 1** shows that 12 alleles have a sequence
size distribution between 800 and 899 base pairs.

.. figure:: ../resources/locus_details_hist.png
    :align: center

    Figure 1: Number of alleles (12) that have a sequence size distribution of 800-899 (bp).


Scatter
-------

The scatterplot represents the **sequence size in base pairs (y-axis)** of **each 
allele (x-axis)** contained in the locus.

For example, **Figure 2** shows that allele 12 has a sequence size of 897 base pairs.

.. figure:: ../resources/locus_details_scatter.png
    :align: center

    Figure 2: Sequence size (897 bp) of allele 12.


Details table
-------------

The locus details table displays the following information about the locus:

- **Locus Label**: the Chewie-NS label assigned to the locus.
- **Number of Alleles**: the total number of alleles contained in the locus.
- **Size Range (bp)**: the range of sequence size in base pairs.
- **Median Size**: the median of the allele sequence sizes in base pairs.
- **Uniprot Label**: the Uniprot annotation.
- **Uniprot URI**: the URI of the Uniprot annotation. Clicking on the URI will open the page of the Uniprot annotation.


.. figure:: ../resources/locus_details_table.png
    :align: center

    Figure 3: Locus Details table.


Interactive Buttons
-------------------

Below the Locus Details table, 3 buttons |buttons| allow for the following operations:

- **Download FASTA**: downloads a FASTA file of the locus.
- **BLASTX**: opens the `BLASTX <https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastx&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome>`_ page.
- **BLASTN**: opens the `BLASTN <https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome>`_ page.

   
.. |buttons| image:: /resources/locus_details_buttons.png
    :align: middle
    :scale: 80%
