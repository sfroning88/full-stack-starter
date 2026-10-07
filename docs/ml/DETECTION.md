# Detecting Unrest

Last updated: **August 2026**

## Project Motivations

There are `~1300` [holocene-epoch volcanoes](https://en.wikipedia.org/wiki/Holocene) with eruptions during the last `12000 years`.
`~975` of these eruptions are on the [`Pacific Ring of Fire`](https://en.wikipedia.org/wiki/Ring_of_Fire).
Affected regions typically brunt low monitoring manpower, improper resources, and outdated equipment.
The `Nazca plate` is [\*subducting\*\*](https://en.wikipedia.org/wiki/Subduction) (sliding) at a `convergence rate of 7.4 cm / year`.
The resulting [**`Southern Volcanic Zone (SVZ)`**](https://en.wikipedia.org/wiki/Andean_Volcanic_Belt#Southern_Volcanic_Zone) contains a continuous chain of `~60` [`stratovolcanoes`](https://en.wikipedia.org/wiki/Stratovolcano).
The [`Sernageomin`](https://www.sernageomin.cl/) actively monitors `~20` high-risk volcanoes near `Santiago (Chile)`.
This leaves `~5 M rural citizens` unprotected in poor-infrastructure farming villages.

Volcanic monitoring is expensive, particular in remote or inhospitable regions, requiring dedicated observatories and `volcanologists`.
Poor infrastructure hampers evacuation efforts, leaving evacuees subject to ash plume and fast-moving explosive `pyroclastic flows`.

## TinyML Saves the Day

Research labs have been exploring the application of machine learning models for detecting volcanic unrest (pre-eruption states).
A combination of different `geosignals` can be cross-corraborated to make evacuation decisions.
The crux of `fiery-spirit` explores how `TinyML` practice can improve monitoring capabilities in underserved regions.

## Two-Tiered Detection System

The system contains a `cloud-based visual model` and an `edge device (on-ground sensor) waveform model`.
The bane of volcanology is signal reliability – there's a plethora of red herrings for eruption indicators.
The challenge boils down to unifying multiple noisy data streams to leverage machine learning.

### Cloud AI

| **Detection AI/ML Method** | **Ground Deformation from Satellite Imagery**        |
| -------------------------- | ---------------------------------------------------- |
| Goal                       | Detect the presence of **ground deformation**        |
| Target                     | `Binary classification` on the presence of `fringes` |
| Input                      | `Interferograms` from InSAR satellite imagery        |
| Data                       | `Hephaestus` (global); `Okada` synthetics            |
| Test                       | `SVZ` volcano frames                                 |
| Base                       | ViT-Small or ResNet (pretrained)                     |
| Adaptions                  | LoRA (attention-projections only)                    |
| Constraints                | (none)                                               |
| Dashboard                  | Interactive map of `SVZ` volcanoes                   |
| Metric                     | `Recall`; `abstention_rate`                          |

### Tiny AI

| **Detection AI/ML Method** | **Seismic Activity from Signal Waveforms**                               |
| -------------------------- | ------------------------------------------------------------------------ |
| Goal                       | Detect changes across `volcanic tremors` and `long-period events`        |
| Target                     | `Categorial classification` of seismic activity (`VT`, `LP`, `TR`, `TC`) |
| Input                      | `Spectrograms` from seismic ground equipment                             |
| Data                       | Waveforms from the `Llaima` volcano                                      |
| Test                       | Waveforms from the `Villarica` volcano (stretch)                         |
| Base                       | CNN `teacher` (trained from-scratch)                                     |
| Adaptions                  | Distillation (to `student`), pruning, fine-tuning, quantization          |
| Constraints                | `flash` (storage), `peak_ram` usage (memory), `MACs` (power)             |
| Dashboard                  | Live `spectrogram` feed; signal escalation                               |
| Metrics                    | `accuracy_loss` per budget savings                                       |

## Shared Interactivity

The `unification` for `volcanologists` happens with dashboard:

- (left) interactive map of `SVZ` volcanoes with satellite imagery available
- (right) `spectogram` feed of chosen volcano with escalation recommendation

The `model_registry`, `HMAC-SHA256 verification`, `model-storage`, `challenger_promotion`, and other core model storage and serving functionalies are borrowed from [**`deep-focus`**](https://github.com/sfroning88/deep-focus.git).

## Academic Literature

The project is based on these sources:

- [Application of Machine Learning to Classification of Volcanic Deformation in Routinely Generated InSAR Data](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2018JB015911)
- [Large-scale demonstration of machine learning for the detection of volcanic deformation in Sentinel-1 satellite imagery](https://link.springer.com/article/10.1007/s00445-022-01608-x)
- [A Deep Neural Networks Approach to Automatic Recognition Systems for Volcano-Seismic Events](https://www.academia.edu/90956564/A_Deep_Neural_Networks_Approach_to_Automatic_Recognition_Systems_for_Volcano_Seismic_Events)
- [Llaima volcano dataset: In-depth comparison of deep artificial neural network architectures on seismic events classification](https://pmc.ncbi.nlm.nih.gov/articles/PMC7206203/)
- [OkadaTorch A Differentiable Programming of Okada Model to Calculate Displacements and Strains from Fault Parameters](https://arxiv.org/abs/2507.17126)
- [Tsunami Early Warning From Global Navigation Satellite System Data Using Convolutional Neural Networks](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2022GL099511)
