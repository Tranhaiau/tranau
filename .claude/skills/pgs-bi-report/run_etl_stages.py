"""
Staged runner — calls each loader, pickles result to CACHE, so reloads are fast.
Stage A: dims + small facts. Stage B: BK LSC per-year (incremental).
Stage C: aggregate measures + JSON export.
"""
import os, sys, pickle, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pgs_etl import (
    load_dimensions, load_xuat_xe, load_ky_hd, load_kh_kd, load_khtn,
    load_kh_dvpt, load_uio, load_xe_ton, load_xe_tinh, load_xe_giao, load_xe_vao_ra,
    load_ban_bh, load_cong_no_bh, load_luong, load_gv_vts, load_chi_phi_end,
    load_hvn, load_dkm, load_bk_lsc, compute_measures, RELATIONSHIPS,
    p, read_xlsx_promoted
)
import pandas as pd
import numpy as np
import datetime as dt

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', '_cache')
os.makedirs(CACHE, exist_ok=True)

def cache_path(name):
    return os.path.join(CACHE, name + '.pkl')

def save(name, obj):
    with open(cache_path(name), 'wb') as f: pickle.dump(obj, f)

def load(name):
    p_ = cache_path(name)
    if os.path.exists(p_):
        with open(p_,'rb') as f: return pickle.load(f)
    return None

def stage(name, fn):
    if load(name) is not None:
        print(f"  · {name}: cached")
        return load(name)
    t = time.time()
    obj = fn()
    save(name, obj)
    rows = len(obj) if hasattr(obj,'__len__') else 'n/a'
    print(f"  + {name}: {rows} rows  ({round(time.time()-t,1)}s)")
    return obj

def stage_bk_lsc_incremental(years=('2025',)):
    """Read BK LSC file-by-file, cache each separately, then concat at the end."""
    parts = []
    for yr in years:
        folder = p('DU LIEU', yr)
        if not os.path.isdir(folder): continue
        for fn in sorted(os.listdir(folder)):
            if not fn.lower().endswith(('.xlsx','.xlsm')): continue
            tag = f'bk_lsc_{yr}_{fn.replace(".Xlsx","").replace(".xlsx","")}'
            if load(tag) is not None:
                parts.append(load(tag))
                print(f"  · {tag}: cached")
                continue
            full = os.path.join(folder, fn)
            t = time.time()
            try:
                df = read_xlsx_promoted(full)
                if df.empty: continue
                df['_source_year'] = yr
                df['_source_file'] = fn
                save(tag, df)
                parts.append(df)
                print(f"  + {tag}: {len(df)} rows ({round(time.time()-t,1)}s)")
            except Exception as e:
                print(f"  ! {tag}: {e}")
    if not parts: return pd.DataFrame()
    bk = pd.concat(parts, ignore_index=True)
    # Apply M-equivalent transforms
    import numpy as np
    if 'Số lệnh' in bk.columns:
        bk['RO'] = bk['Số lệnh']
        s = bk['Số lệnh'].astype(str)
        parts2 = s.str.split('.', n=1, expand=True)
        bk['LHSC'] = parts2[1].astype(str).str[0] if 1 in parts2.columns else ''
    if 'Phân loại phụ tùng' in bk.columns and 'LHSC' in bk.columns:
        bk['PK KD'] = bk['LHSC'].astype(str) + ' ' + bk['Phân loại phụ tùng'].astype(str)
    if 'Thương hiệu' in bk.columns:
        th = bk['Thương hiệu'].astype(str).str.upper()
        bk['Thương hiệu N'] = np.where(th.isin(['FORD','HONDA','TOYOTA','BYD']), th, 'KHÁC')
    if 'Tên đơn vị bảo hiểm' in bk.columns:
        bk['Tên đơn vị bảo hiểm'] = bk['Tên đơn vị bảo hiểm'].astype(str).str.upper()
    if 'Ngày lệnh' in bk.columns:
        bk['Ngày lệnh'] = pd.to_datetime(bk['Ngày lệnh'], errors='coerce')
    for c in ['Tổng doanh thu','Doanh thu công việc','Doanh thu vật tư','Tiền vốn','Lợi nhuận']:
        if c in bk.columns: bk[c] = pd.to_numeric(bk[c], errors='coerce')
    return bk

def main(stages='all'):
    print("== Stage A: dims + small facts ==")
    dims = stage('dims', load_dimensions)
    facts = {}
    for name, fn in [
        ('xuat_xe', load_xuat_xe),
        ('ky_hd',   load_ky_hd),
        ('kh_kd',   load_kh_kd),
        ('khtn',    load_khtn),
        ('kh_dvpt', load_kh_dvpt),
        ('uio',     load_uio),
        ('xe_ton',  load_xe_ton),
        ('xe_tinh', load_xe_tinh),
        ('xe_giao', load_xe_giao),
        ('xe_vao_ra', load_xe_vao_ra),
        ('ban_bh',  load_ban_bh),
        ('cong_no_bh', load_cong_no_bh),
        ('luong',   load_luong),
        ('gv_vts',  load_gv_vts),
        ('chi_phi_end', load_chi_phi_end),
        ('hvn',     load_hvn),
        ('dkm',     load_dkm),
    ]:
        if stages in ('all','A'):
            facts[name] = stage(name, fn)
        else:
            v = load(name)
            facts[name] = v if v is not None else pd.DataFrame()

    if stages in ('all','B'):
        print("== Stage B: BK LSC incremental ==")
        bk = stage_bk_lsc_incremental(years=os.environ.get('PGS_BK_YEARS','2025').split(','))
        save('bk_lsc', bk)
        facts['bk_lsc'] = bk
    else:
        v = load('bk_lsc')
        facts['bk_lsc'] = v if v is not None else pd.DataFrame()

    if stages in ('all','C'):
        print("== Stage C: measures + JSON export ==")
        measures = compute_measures(facts, dims)

        def to_records(df):
            if df is None or df.empty: return []
            d = df.copy()
            for c in d.columns:
                if pd.api.types.is_datetime64_any_dtype(d[c]):
                    d[c] = d[c].dt.strftime('%Y-%m-%d')
                elif d[c].dtype == 'object':
                    d[c] = d[c].astype(str).replace({'nan': None, 'NaT': None})
            d = d.where(pd.notna(d), None)
            return d.to_dict(orient='records')

        out = {
            'generated_at': dt.datetime.now().isoformat(timespec='seconds'),
            'dims': {k: to_records(v) for k,v in dims.items()},
            'measures': {k: to_records(v) for k,v in measures.items()},
            'relationships': [{'from_table':a,'from_col':b,'to_table':c,'to_col':d}
                              for (a,b,c,d) in RELATIONSHIPS],
            'row_counts': {k: int(len(v)) for k,v in facts.items()},
        }
        out_path = os.path.join(os.path.dirname(CACHE), 'pgs_data.json')
        with open(out_path,'w',encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, default=str)
        print(f"== DONE → {out_path}  size={os.path.getsize(out_path):,} bytes ==")

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'all')
