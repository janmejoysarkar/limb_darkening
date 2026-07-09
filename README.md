![Logo](https://suit.iucaa.in/sites/default/files/top_banner_compressed_2_1.png)


# SUIT Large scale pattern removal 

- Generates large contamination patch and large scale
artefact removal flat field.
- 5-6 days sun continuum images are needed.
- 1 image per day.
- Saves correction image in data/interim.
- 5 days images > Make featureless sun > 
Remove small scale features > Remove limb darkening > Calib frame

## Usage

Please ensure the following folder structure.
```
.
├── data
│   ├── external
│   ├── interim
│   ├── processed
│   └── raw
└── src
```
Make folders with-
```
mkdir data
cd data
mkdir -p {raw,external,interim,processed}
```
## Authors

- [@janmejoysarkar](https://github.com/janmejoysarkar)

## Acknowledgements

 - [SUIT-POC, IUCAA](https://suit.iucaa.in)
 - [SUIT-team, MPS](https://mps.mpg.de)
 - [Aditya-L1, ISRO](https://www.isro.gov.in/Aditya_L1.html)

