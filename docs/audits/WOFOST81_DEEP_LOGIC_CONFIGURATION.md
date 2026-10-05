# WOFOST 8.1 Deep Logic Audit — Configuration Contracts

## Principle

Parameters that represent physical fractions, binary switches or positive denominators are part of the executable scientific contract. Accepting values outside their domain can turn otherwise correct equations into silent logic inversions.

## Validation added

- WOFOST81 biomass reallocation fractions, rates and efficiency: [0,1].
- Crop-N NFIX_FR, NMAXRT_FR, NMAXST_FR and residual fractions: [0,1]; NMAXSO non-negative.
- Layered evapotranspiration IAIRDU and IOX: exactly 0 or 1.
- SNOMIN amendment events: non-negative amount/age, positive depth and C:N, composition fractions in [0,1], mineral-N fractions summing to at most 1.

## Existing strong validation

MLWB/SoilProfile validates that maximum rooting depth coincides with a soil-layer boundary. Crop root dynamics limits nominal maximum rooting depth using crop and soil maxima.

## Remaining model-owner questions

- Whether RDI > min(RDMCR,RDMSOL) should hard-fail rather than let RDI define rdmax.
- Scientifically intended admissible ranges for DVS_N_TRANSL and REALLOC_DVS.
- Whether composition constraints should also couple f_orgmat to mineral-N fractions; this depends on the amendment definition and is not imposed here.
- Whether non-layered ET implementations should receive the same strict binary-switch validation as the WOFOST81 layered configuration.
