import sys; sys.path.insert(0, sys.argv[2])
import pyarrow as pa, pyarrow.ipc as ipc, pyarrow.compute as pc, pandas as pd, numpy as np
D=sys.argv[1]
def rd(f):
    tb=ipc.open_file(f"{D}/{f}").read_all()
    cols={}
    for n in tb.column_names:
        c=tb[n]
        if pa.types.is_dictionary(c.type): c=c.cast(c.type.value_type)
        cols[n]=c.to_pandas()
    return pd.DataFrame(cols)
t=rd('ldt_trial.arrow'); i=rd('ldt_item.arrow'); s=rd('ldt_subj.arrow')
for n,d in [('trial',t),('item',i),('subj',s)]:
    print('##',n,d.shape); print(d.dtypes.to_string()); print(d.head(4).to_string())
it=pd.read_csv(f"{D}/Items.csv.gz", low_memory=False); print('## Items.csv',it.shape); print(list(it.columns)); print(it.head(3).to_string())
