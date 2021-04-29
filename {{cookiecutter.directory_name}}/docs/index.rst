.. Chewie-NS documentation master file, created by
   sphinx-quickstart on Thu May 14 18:17:23 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Chewie-NS's documentation!
======================================

About Chewie-NS
---------------

Welcome!
::::::::

Chewie-NS is a web-based wg/cgMLST allele Nomenclature Server, based on the 
`TypOn ontology <https://jbiomedsem.biomedcentral.com/articles/10.1186/2041-1480-5-43>`_,
that integrates with the `chewBBACA suite <https://github.com/B-UMMI/chewBBACA>`_
to provide a centralized service to **share, download or update schemas**, allowing the 
**easy sharing of results**, while ensuring the **reproducibility and consistency** 
of these steps. 

Chewie-NS is developed by the `Molecular Microbiology and Infection Unit (UMMI) 
<http://im.fm.ul.pt>`_ at the 
`Instituto de Medicina Molecular João Lobo Antunes 
<https://imm.medicina.ulisboa.pt/>`_ and `Faculdade de Medicina, Universidade de Lisboa 
<https://www.medicina.ulisboa.pt/>`_.

Goals
:::::

With this service we have the following main goals:

1. Providing a public and centralised web service to manage typing schemas.
2. Establish a common nomenclature for allele calling.
3. Ensure the reproducibility and consistency of wg/cgMLST analysis.

Tutorial
::::::::

Chewie-NS has a tutorial website at `<https://tutorial.chewbbaca.online/>`_!
The tutorial will allow users to learn how to interact with Chewie-NS.

Tutorial instructions are available at the :doc:`user/tutorial`!

Citation
::::::::

If you use **Chewie-NS**, please cite: 

Mamede, R., Vila-Cerqueira, P., Silva, M., Carriço, J. A., & Ramirez, M. (2020). Chewie Nomenclature Server (chewie-NS): a deployable nomenclature server for easy sharing of core and whole genome MLST schemas. Nucleic Acids Research.

Available from: `<https://academic.oup.com/nar/advance-article/doi/10.1093/nar/gkaa889/5929238>`_

Licensing
:::::::::

This project is licensed under the `GPLv3 license 
<https://github.com/B-UMMI/Nomenclature_Server_docker_compose/blob/master/LICENSE>`_.
The source code of Chewie-NS is available at `<https://github.com/B-UMMI/Chewie-NS>`_
and the webservice is available at `<https://chewbbaca.online/>`_.

Contacts
::::::::

For any issues contact the development team at imm-bioinfo@medicina.ulisboa.pt or 
open an issue at the Chewie-NS Github `repository <https://github.com/B-UMMI/Chewie-NS>`_.

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   getting_started/overview
   getting_started/installation
   about/gdpr
   about/presentations


.. toctree::
   :maxdepth: 1
   :caption: Chewie-NS API

   user/api_usage


.. toctree::
   :maxdepth: 1
   :caption: Chewie-NS User Interface

   user_interface/ui_usage
   

.. toctree::
   :maxdepth: 1
   :caption: Integration with chewBBACA

   user/chewbbaca
