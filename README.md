# Multidomain, Automated, Photopatterning of DNA-Functionalized Hydrogels (**MAPDH**)

Multidomain, Automated, Photopatterning of DNA-Functionalized Hydrogels (**MAPDH**) is a platform for the automated fabrication of DNA-functionalized hydrogels using digital, maskless photolithography. 

* The preprint can be found at https://doi.org/10.26434/chemrxiv-2023-qmfjq
* The MAPDH protocol can be found at https://dx.doi.org/10.17504/protocols.io.j8nlkw2ywl5r/v1

## Getting Started

To streamline MAPDH use, example scripts and functions are provided.

Key files:
* Patterning_functions
  * This file contains all necessary functions, with documentation, to run all operations in MAPDH.
* Patterning_example_script
  * This file is an example that uses built-in masks to pattern differently shaped hydrogels.
* MAPDH_example_script
  * This file is an example for fully automated MADPH - incorporating the flow controller, patterning setup, bright-field and fluorescence imaging into one script for multi-domain patterning and simultaneous imaging.
* 

### Prerequisites

* Install lastest version of [Micromanager](https://micro-manager.org/)
* Install lastest version of [Pycromanager](https://github.com/micro-manager/pycro-manager)

* Python and other required packages, with version numbers:
  * Python: 3.8
  * anaconda: 2020.07
  * Scikit-image: 0.19.3
  * Pandas: 1.4.4
  * numpy: 1.18.5
  * PIL: 7.2.0
  * Pycromanager: 0.6.0

### Patterning examples
These are real-time videos for fabrication of hydrogel letters taken using bright-field microscopy, with a field of view of 1250 microns. Each letter is fabricated using the message_mask_generator package in Python. Each letter here is the same domain, i.e., each hydrogel has the same composition.

https://user-images.githubusercontent.com/67386551/219878485-338b717b-f008-45a6-b417-a819aa724788.mp4

https://user-images.githubusercontent.com/67386551/219878132-83617d94-9442-419f-b393-dbde8f758fe1.mp4

