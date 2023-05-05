# Changelog

## [0.6.0] - 2023-05-05
### Added
 - composite_rupture_sections resolver
 - mfd_histogram resolver
 - color_scale resolver

### Changed
 - now using zipped dependencies for AWS

## [0.5.2] - 2023-04-28
### Changed
 - update solvis 0.7.0
 - replace embedded solution file
 - handle fill style properly
 - remove rounding on rupture rate attributes

## [0.5.1] - 2023-04-25
### Added
 - add version to about resolver
 - added solvis-store
 - use solvis-store for rupture-ids (TEST env only)
### Changed
 - updated serverless npm modules
 - updated nzshm-common, nzshm-model, solvis

## [0.5.0] - 2023-04-13
### Added
 - location_by_id root query
### Changed
 - location_code -> location_id
 - code -> location_id

## [0.4.0] - 2023-04-12
### Added
 - filter_ruptures query
 - sorting for filter_ruptures

## [0.3.0] - 2023-04-06
### Added
 - CompositeSolution model
 - CompositeRuptureDetail models
 - relay pagination
 - style option on fault_surfaces

## [0.2.0] - 2022-??-??
### Added
 - InversionSolutoin 

## [0.0.1] - 2022-??-??
Initial release of the NZ NSHM 2022 revision