import sys, pandas as pd, numpy as np
R=sys.argv[1]
def desc(name,df,item='item'):
    g=df.groupby(item)['accuracy'].agg(['size','mean'])
    print(f"{name}: subj={df['subject'].nunique()} trials={len(df)} n_{item}={len(g)} resp/item med={g['size'].median():.0f} min={g['size'].min()} max={g['size'].max()} acc mean={df['accuracy'].mean():.3f} item acc range={g['mean'].min():.2f}-{g['mean'].max():.2f}")
for s,f in [('study02','01_Priors/data/study02/data.csv'),('study03','01_Priors/data/study03/data.csv'),('study04','01_Priors/data/study04/data.csv'),('study05','01_Priors/data/study05/data/mars.csv'),('valid_long','04_Validation/data/longform/mars.csv'),('valid_short','04_Validation/data/shortform/mars.csv')]:
    d=pd.read_csv(f"{R}/{f}"); print(list(d.columns)); desc(s,d)
    for c in ['item_set','shape_set','distractor','test_form','testform','long_form','short_form','dimension']:
        if c in d: print('   ',c,dict(d[c].value_counts().sort_index()))
c=pd.read_csv(f"{R}/03_Calibration/data/data.csv"); desc('calib(template)',c); desc('calib(clone)',c,'item_id')
rej=pd.read_csv(f"{R}/03_Calibration/data/reject.csv"); print('reject cols',list(rej.columns), len(rej))
for col in ['item_set','test_form','shape_set','distractor','dimension']: print('   ',col,dict(c[col].value_counts().sort_index()))
print('NaN accuracy', c['accuracy'].isna().sum())
f=pd.read_csv(f"{R}/03_Calibration/designs/features.csv"); st=pd.read_csv(f"{R}/tutorials/stats.csv")
print('features',f.shape,'templates',f['item'].nunique()); print(f.groupby('distractor')['item'].nunique())
t=f.drop_duplicates('item')
print('dimension dist',dict(t['dimension'].value_counts().sort_index())); print('n_features dist',dict(t['n_features'].value_counts().sort_index()))
tt=st.drop_duplicates('item'); print('n_rules dist',dict(tt['n_rules'].value_counts().sort_index()))
m=t.merge(tt[['item','n_rules','n_elements']],on='item')
print(m[['dimension','n_features','n_rules']].corr(method='spearman').round(2))
print('templates by distractor availability:'); print(f.groupby('item')['distractor'].agg(lambda x:'+'.join(sorted(set(x)))).value_counts())
# template-level accuracy vs measures in calibration
a=c.groupby('item')['accuracy'].mean().rename('acc').reset_index().merge(m,on='item')
print(a[['acc','dimension','n_features','n_rules']].corr(method='spearman').round(2))
print('study01 dims', pd.read_csv(f"{R}/01_Priors/data/study01/dimensionality.csv").shape)
s1=pd.read_csv(f"{R}/01_Priors/data/study01/stats.csv", lineterminator='\r'); print(s1.shape, s1.Group.unique(), s1.Item.nunique())
r=pd.read_csv(f"{R}/04_Validation/data/longform/rpm.csv"); print('rpm stim',r.stimulus.nunique(), sorted(r.stimulus.unique())[:12], r.subject.nunique())
