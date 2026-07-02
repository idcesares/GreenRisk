# Acknowledgements

GreenRisk is an original scoring instrument, but it is built directly on top of
published research and open models. This page credits that work explicitly.

## Language models

All four signal classifiers are pinned, unmodified checkpoints from the
[ClimateBERT](https://huggingface.co/climatebert) family, hosted on the Hugging
Face Hub under the `climatebert` organization and released under the Apache
License 2.0. GreenRisk loads them at fixed revisions (see
[`models.py`](../models.py)) and does not fine-tune or otherwise alter their
weights.

**Base language model**

```bibtex
@inproceedings{wkbl2022climatebert,
    title={{ClimateBERT: A Pretrained Language Model for Climate-Related Text}},
    author={Webersinke, Nicolas and Kraus, Mathias and Bingler, Julia and Leippold, Markus},
    booktitle={Proceedings of AAAI 2022 Fall Symposium: The Role of AI in Responding to Climate Challenges},
    year={2022},
    doi={https://doi.org/10.48550/arXiv.2212.13631}
}
```

**Climate-detector, climate-specificity, climate-commitment, and
climate-sentiment classifiers** (`is_climate`, `specificity`, `commitment`,
`sentiment_asymmetry` signals):

```bibtex
@techreport{bingler2023cheaptalk,
    title={How Cheap Talk in Climate Disclosures Relates to Climate Initiatives, Corporate Emissions, and Reputation Risk},
    author={Bingler, Julia and Kraus, Mathias and Leippold, Markus and Webersinke, Nicolas},
    type={Working paper},
    institution={Available at SSRN 3998435},
    year={2023}
}
```

This is also the source of the "cheap talk" construct (`1 - P('spec')`) that
GreenRisk uses as the external convergent-validity baseline in
[`docs/validation.md`](validation.md).

**Net-zero/reduction classifier** (`netzero` signal):

```bibtex
@article{schimanski2023climatebertnetzero,
    title={ClimateBERT-NetZero: Detecting and Assessing Net Zero and Reduction Targets},
    author={Schimanski, Tobias and Bingler, Julia and Hyslop, Camilla and Kraus, Mathias and Leippold, Markus},
    year={2023},
    eprint={2310.08096},
    archivePrefix={arXiv},
    primaryClass={cs.LG}
}
```

## Corpus and disclosure framework

The large-scale validation run (`scripts/run_full_corpus.py`) scores the
`climatebert/tcfd_recommendations` dataset, the labeled corpus released
alongside the ClimateBERT paper above. The underlying disclosure standard is
the Task Force on Climate-related Financial Disclosures (TCFD):

> Task Force on Climate-related Financial Disclosures. *Recommendations of the
> Task Force on Climate-related Financial Disclosures.* 2017.

## Held-out contrast set

The Phase 6 face-validity evidence (`data/contrast_set.csv`) is built entirely
from public, regulator-adjudicated or third-party-verified sources — no text
in that file is synthesized. Every row carries its own `source_company`,
`source_document`, `source_url`, and `evidentiary_basis` columns; short
paragraph-length excerpts are reproduced under fair-use/fair-dealing principles
for research and critique. The set spans:

- U.S. SEC enforcement action and German Frankfurt Public Prosecutor's Office
  ruling against DWS Group for ESG misrepresentation;
- U.S. EPA/DOJ "Dieselgate" enforcement action against Volkswagen AG;
- UK Advertising Standards Authority ruling G21-1127656 against HSBC UK Bank plc;
- Microsoft's CDP A-list, SBTi-validated sustainability disclosures;
- Ørsted A/S's CDP A-list, SBTi-validated sustainability disclosures.

Consult `data/contrast_set.csv` directly for the exact citation backing any
individual case.

## Methods and standards

- **Mamdani fuzzy inference** — Mamdani, E.H. and Assilian, S. (1975). "An
  experiment in linguistic synthesis with a fuzzy logic controller."
  *International Journal of Man-Machine Studies*, 7(1), 1–13. GreenRisk's
  rule base and centroid defuzzification follow this model, implemented via
  [scikit-fuzzy](https://github.com/scikit-fuzzy/scikit-fuzzy).
- **W3C PROV-O** — Lebo, T., Sahoo, S., McGuinness, D. (eds.) (2013). *PROV-O:
  The PROV Ontology.* W3C Recommendation. GreenRisk's provenance graphs
  (`artifacts/provenance/`) are serialized against this ontology.

## License compatibility

All cited models and the "cheap talk" baseline code are released under the
Apache License 2.0, the same license used by this repository (see
[`LICENSE`](../LICENSE)).
