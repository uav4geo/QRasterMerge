# QRasterMerge

<img width="128" height="128" alt="Image" src="https://github.com/user-attachments/assets/851ec651-60fb-4994-9a0a-47ec464fcd7d" />

QGIS plugin for seamlessly merging overlapping rasters. It features memory-efficient cutline merging and histogram matching capabilities.

![Image](https://github.com/user-attachments/assets/7d5ed474-5c1c-4be1-ab7b-b14927477312)

## Installation

> **Note:** This plugin is not yet available on the QGIS plugin manager as it is waiting for approval. Please install manually from the releases page.

Install `QRasterMerge` via the [QGIS](https://qgis.org) plugin manager or import the .zip file manually from [releases](https://github.com/uav4geo/QRasterMerge/releases). Before you install it, make sure you also have the [QPIP](https://github.com/opengisch/qpip) plugin installed, which will take care of installing a few dependencies for you.

## Usage

1. From QGIS, go to `Raster` --> `QRasterMerge` --> `Seamless Merge`
2. Pick at least 2 raster layers
3. Check the settings, including `Blending Distance` and `Equalize Color Histograms`
4. Press `Run`.

### Histogram Matching Reference

When using histogram matching, the first layer is used as the reference (colors will be matched to the first layer). If you want to use a different reference layer, rearrange the order of the layers in the input layers list. 

## License

AGPLv3
