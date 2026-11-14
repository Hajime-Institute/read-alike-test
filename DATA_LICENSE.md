# Data license

The derived data in `readings/` and `results/` are licensed under the
**Creative Commons Attribution 4.0 International License (CC BY 4.0)**,
https://creativecommons.org/licenses/by/4.0/ .

Attribution: Hajime Hotta and Sandeep Yella, *Read-Alike Test: Validating Synthetic Document Degradation by Whether
a Reader Fails on the Same Words as on Real Images* (2026). Please also attribute the source datasets below.

## Source datasets

### SmartDoc-QA

`readings/blocks_d1_10.json` and the SmartDoc-QA files in `results/` are derived from SmartDoc-QA:

> N. Nayef, M. M. Luqman, S. Prum, S. Eskenazi, J. Chazalon and J.-M. Ogier, "SmartDoc-QA: A Dataset for Quality
> Assessment of Smartphone Captured Document Images - Single and Multiple Distortions," in 2015 13th International
> Conference on Document Analysis and Recognition (ICDAR), 6th International Workshop on Camera-Based Document
> Analysis and Recognition (CBDAR), pp. 1231-1235, 2015. doi:10.1109/ICDAR.2015.7333960

SmartDoc-QA is distributed through Zenodo (record 5293201). The record page shows CC BY 4.0, but the license file inside
the archive (`SmartDoc-QA_Dataset_License.pdf`) makes the dataset available free of charge for research purposes only and
does not allow re-distribution of the dataset. We therefore release no images, PDFs, ground-truth files or
transcriptions of SmartDoc-QA. Changes made: the captures were rectified and read paragraph by paragraph by four text
readers, synthetic images were made from the source PDFs and read the same way, and the transcriptions were scored
against the ground truth. `blocks_d1_10.json` holds paragraph boxes taken from the source PDFs,
`results/candidate_settings.json` lists the generator settings tried, and the other files hold statistics computed
from the transcriptions (counts, agreements and verdicts, with no text).

### UNLV/ISRI OCR test collection

`readings/unlv/` and `results/unlv/` are derived from the UNLV/ISRI document collection (business letters and
magazine pages, `bus` and `mag` sets):

> S. V. Rice, F. R. Jenkins and T. A. Nartker, "The Fourth Annual Test of OCR Accuracy," Technical Report TR-95-04,
> Information Science Research Institute, University of Nevada, Las Vegas, 1995.

Changes made: zones of the real scans and of synthetic 200 dpi images made from the 400 dpi scans were read with
Tesseract; `readings/unlv/` holds these transcriptions (they reproduce the page text with OCR errors) and
`results/unlv/` holds statistics computed from them. No UNLV images or ground-truth files are included.

The collection is released under the Apache License 2.0 through the Google Code archive project
`isri-ocr-evaluation-tools` (https://code.google.com/archive/p/isri-ocr-evaluation-tools/), whose description covers
the images and ground-truth text as well as the evaluation tools.

## Code

The code in `code/` is under the MIT License (see `LICENSE`), not under this data license.
