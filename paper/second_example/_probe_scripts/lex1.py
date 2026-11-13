import sys; sys.path.insert(0, sys.argv[2])
import zipfile, io, pandas as pd, numpy as np
R=sys.argv[1]
pd.set_option('display.width',250)
# BLP
with zipfile.ZipFile(f"{R}/blp/blp-trials.txt.zip") as z:
    with z.open('blp-trials.txt') as f:
        blp=pd.read_csv(f, sep='\t', low_memory=False)
print('## BLP', blp.shape); print(blp.dtypes.to_string()); print(blp.head(3).to_string())
blp.to_pickle(f"{sys.argv[3]}/blp.pkl")
with zipfile.ZipFile(f"{R}/dlp1/dlp-trials.txt.zip") as z:
    with z.open('dlp-trials.txt') as f:
        dlp=pd.read_csv(f, sep='\t', low_memory=False)
print('## DLP', dlp.shape); print(dlp.dtypes.to_string()); print(dlp.head(3).to_string())
dlp.to_pickle(f"{sys.argv[3]}/dlp.pkl")
st=pd.read_csv(f"{R}/dlp1/dlp-stimuli.txt", sep='\t'); print('## DLP stimuli', st.shape, list(st.columns)); print(st.head(3).to_string())
itm=pd.read_csv(f"{R}/dlp1/dlp-items.txt", sep='\t'); print('## DLP items', itm.shape, list(itm.columns))
mg=pd.read_csv(f"{R}/megalex/megalex_visual_exp1.csv", low_memory=False)
print('## MEGALEX', mg.shape); print(mg.dtypes.to_string()); print(mg.head(3).to_string())
mg.to_pickle(f"{sys.argv[3]}/megalex.pkl")
