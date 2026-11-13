# data_raw_lex: lexical decision megastudies, original authors' releases

Downloaded 2026-11-13 from the authors' public OSF projects through the browser (no login), using
`https://files.osf.io/v1/resources/<node>/providers/osfstorage/<file id>?direct` (or `files.de-1.osf.io`).
Each SHA-256 in `MANIFEST.sha256` equals the hash reported by the OSF API for that file.
Do not redistribute these files. Full record (citations, licences, counts, what is missing):
`PROVENANCE.md` of the second worked example.

| Folder | Source | Licence stated at the source | Files |
|---|---|---|---|
| `elp/` | https://osf.io/n63s2/ (English Lexicon Project, trial-level data; Balota et al., 2007, https://doi.org/10.3758/BF03193014) | none stated | `ldt_raw.zip` (guid eu5ca, version 2, 2021-11-20), `ELP_Trial_Level_Data_Key.txt` (rd632), `ldt.patch` (u2mkb) |
| `elp/dataark/` | https://osf.io/879jw/ (Data Ark copy, 2018; reference only) | none stated | `data.zip` (8xs6h) |
| `blp/` | https://osf.io/b5sdk/ (British Lexicon Project; Keuleers et al., 2012, https://doi.org/10.3758/s13428-011-0118-4) | CC BY-NC-SA 4.0 (`license.txt`) | `blp-trials.txt.zip` (84efq), `blp-items.txt.zip` (6tdnz), `blp-stimuli.txt.zip` (tge67), `license.txt` (5jmgt) |
| `dlp/` | https://osf.io/uw7t6/ (Dutch Lexicon Project 1; Keuleers et al., 2010, https://doi.org/10.3389/fpsyg.2010.00174) | CC BY-NC-SA 4.0 (`license.txt`) | `dlp-trials.txt.zip` (zjdbn), `dlp-trials-block-50.txt.zip` (5qa4s), `dlp-items.txt.zip` (ujvk6), `dlp-stimuli.txt.zip` (jt2ue), `license.txt` (etx4r) |
| `megalex/` | https://osf.io/7z6th/ (MEGALEX; Ferrand et al., 2018, https://doi.org/10.3758/s13428-017-0943-1) | none stated | `By trials Auditory & Visual-MEGALEX.zip` (uq2yb, 2026-03-26), `vw.ParItems.DVandIV.txt` (fndvw), `vp.essais_ElTec&Seuils.txt` (uk9sn) |
| `frequency/` | https://osf.io/djpqz/ (SUBTLEX-US), https://osf.io/zq49t/ (SUBTLEX-UK), https://osf.io/3d8cx/ (SUBTLEX-NL) | CC BY-NC-SA 4.0 (`license_subtlex_osf.txt`, same file in all three) | three `.xlsx` files (7wx25, d3jbg, e8y5b) |
| `osf_api/` | https://api.osf.io/v2/ | not applicable | `lexdl_osf_listing_1.json`: file list with sizes, hashes and dates as returned by the OSF API on 2026-11-13 |

Missing: the ELP item-characteristics table from https://elexicon.wustl.edu/ (site could not be read by the
assistant; save it by hand as `elp/elexicon_items.csv`). Lexique (French) was not downloaded: licence unclear.
