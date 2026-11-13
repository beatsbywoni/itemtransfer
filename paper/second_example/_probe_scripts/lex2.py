import sys; sys.path.insert(0, sys.argv[2])
import pandas as pd, numpy as np, pyarrow as pa, pyarrow.ipc as ipc
from scipy.stats import spearmanr
from wordfreq import zipf_frequency
R=sys.argv[1]; C=sys.argv[3]; rng=np.random.default_rng(1)
def rd(f):
    tb=ipc.open_file(f).read_all(); cols={}
    for n in tb.column_names:
        c=tb[n]
        if pa.types.is_dictionary(c.type): c=c.cast(c.type.value_type)
        cols[n]=c.to_pandas()
    return pd.DataFrame(cols)
fam={}
t=rd(f"{R}/elp_bates/ldt_trial.arrow"); i=rd(f"{R}/elp_bates/ldt_item.arrow")
print('ELP acc values', t['acc'].value_counts(dropna=False).to_dict())
t=t.merge(i[['item','isword']],on='item'); t=t[t.isword & t.acc.notna()]
fam['ELP (US English)']=(pd.DataFrame({'p':t.subj.values,'w':t.item.values,'y':t.acc.astype(int).values}),'en')
b=pd.read_pickle(f"{C}/blp.pkl"); print('BLP lexicality',b.lexicality.value_counts().to_dict()); b=b[b.lexicality=='W']
fam['BLP (British English)']=(pd.DataFrame({'p':b.participant.values,'w':b.spelling.values,'y':b.accuracy.values}),'en')
d=pd.read_pickle(f"{C}/dlp.pkl"); print('DLP lexicality',d.lexicality.value_counts().to_dict(), 'blocks',d.block.nunique()); d=d[(d.lexicality=='W')&(d.block!=50)]
fam['DLP (Dutch)']=(pd.DataFrame({'p':d.participant.values,'w':d.spelling.values,'y':d.accuracy.values}),'nl')
m=pd.read_pickle(f"{C}/megalex.pkl"); print('MEGALEX types',m.stimulus_type.value_counts().to_dict(),'repetition',m.repetition.value_counts().to_dict()); m=m[(m.stimulus_type=='word')&(m.repetition==0)]
fam['MEGALEX (French)']=(pd.DataFrame({'p':m.participant_id.values,'w':m.stimulus.values,'y':m.accuracy.values}),'fr')
def sig(x): return 1/(1+np.exp(-x))
def logit_fit(X,k,n):
    b=np.zeros(X.shape[1])
    for _ in range(50):
        p=sig(X@b); W=n*p*(1-p); g=X.T@(k-n*p); H=(X*W[:,None]).T@X
        st=np.linalg.solve(H,g); b+=st
        if np.abs(st).max()<1e-8: break
    return b
out={}
for name,(df,lang) in fam.items():
    df=df[df.y.isin([0,1])]
    g=df.groupby('w').y.agg(['size','sum','mean'])
    # split-half over participants
    ps=df.p.unique(); h=rng.permutation(ps)[:len(ps)//2]; A=df[df.p.isin(h)].groupby('w').y.agg(['size','sum']); B=df[~df.p.isin(h)].groupby('w').y.agg(['size','sum'])
    j=A.join(B,lsuffix='a',rsuffix='b',how='inner'); la=np.log((j.suma+.5)/(j.sizea-j.suma+.5)); lb=np.log((j.sumb+.5)/(j.sizeb-j.sumb+.5)); r=np.corrcoef(la,lb)[0,1]; sb=2*r/(1+r)
    g['zipf']=[zipf_frequency(str(w).lower(),lang) for w in g.index]; g['len']=[len(str(w)) for w in g.index]
    g['logit']=np.log((g['sum']+.5)/(g['size']-g['sum']+.5))
    print(f"\n## {name}: participants={df.p.nunique()} words={len(g)} word trials={len(df)} resp/word median={g['size'].median():.0f} (min {g['size'].min()}, 5th pct {g['size'].quantile(.05):.0f}) mean acc={df.y.mean():.3f}")
    print(f"   words with acc<0.95: {(g['mean']<.95).mean():.2f}; acc<0.5: {(g['mean']<.5).mean():.2f}; words with >=20 resp: {(g['size']>=20).mean():.3f}; split-half r={r:.3f}, Spearman-Brown={sb:.3f}")
    print(f"   zipf==0 (not in wordfreq): {(g.zipf==0).mean():.3f}; zipf range {g.zipf.min():.2f}-{g.zipf.max():.2f} median {g.zipf.median():.2f}; len range {g.len.min()}-{g.len.max()} median {g.len.median():.0f}")
    print(f"   Spearman acc~zipf {spearmanr(g['mean'],g.zipf)[0]:.3f}; acc~len {spearmanr(g['mean'],g.len)[0]:.3f}; zipf~len {spearmanr(g.zipf,g.len)[0]:.3f}")
    for v in ['zipf','len']:
        X=np.column_stack([np.ones(len(g)),g[v].values]); bb=logit_fit(X,g['sum'].values.astype(float),g['size'].values.astype(float)); print(f"   binomial slope on {v}: {bb[1]:.3f} (intercept {bb[0]:.2f})")
    out[name]=g
e=set(out['ELP (US English)'].index.str.lower()); bl=set(out['BLP (British English)'].index.str.lower())
print('\nELP∩BLP shared words:',len(e&bl),'ELP only',len(e-bl),'BLP only',len(bl-e))
j=out['ELP (US English)'].join(out['BLP (British English)'],lsuffix='_e',rsuffix='_b',how='inner'); print('shared-item agreement (logit acc) r=',round(np.corrcoef(j.logit_e,j.logit_b)[0,1],3),'spearman',round(spearmanr(j.mean_e,j.mean_b)[0],3), 'n',len(j))
# published measures
it=pd.read_csv(f"{R}/elp_bates/Items.csv.gz",low_memory=False).set_index('Word')
for c in ['Log_Freq_HAL','LgSUBTLWF','OLD','Ortho_N','Freq_KF']: it[c]=pd.to_numeric(it[c].astype(str).str.replace(',',''),errors='coerce')
g=out['ELP (US English)'].join(it[['Log_Freq_HAL','LgSUBTLWF','OLD','Ortho_N','Length','Freq_KF']],how='left')
print('\nELP published measures coverage:',g[['Log_Freq_HAL','LgSUBTLWF','OLD','Freq_KF']].notna().mean().round(3).to_dict())
print(g[['mean','zipf','Log_Freq_HAL','LgSUBTLWF','len','OLD','Ortho_N']].corr(method='spearman').round(2).to_string())
st=pd.read_csv(f"{R}/dlp1/dlp-stimuli.txt",sep='\t').set_index('spelling')
g=out['DLP (Dutch)'].join(st[['subtlex.log10.frequency','OLD20','coltheart.N','nchar','celex.frequency']],how='left')
print('\nDLP published measures coverage:',g[['subtlex.log10.frequency','OLD20','celex.frequency']].notna().mean().round(3).to_dict())
print(g[['mean','zipf','subtlex.log10.frequency','len','OLD20','coltheart.N']].corr(method='spearman').round(2).to_string())
