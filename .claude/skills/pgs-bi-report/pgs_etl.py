"""
PGS BI ETL - Replicates Power Query (M) cleaning + Model View (relationships) + DAX measures
in pure pandas. Source data: D:\\TCT PGS\\Claude Data\\
Output: D:\\TCT PGS\\Claude Data\\BAO CAO BI\\output\\pgs_data.json (aggregated, ready for HTML dashboard)
"""
import os, sys, json, glob, re, datetime as dt, warnings
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

ROOT = os.environ.get("PGS_DATA_ROOT", r"D:\TCT PGS\Claude Data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
OUT = os.path.normpath(OUT)
os.makedirs(OUT, exist_ok=True)

def p(*a): return os.path.join(ROOT, *a)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers (Power Query equivalents)
# ─────────────────────────────────────────────────────────────────────────────
def read_xlsx_promoted(path, sheet=None, min_header_nonnull=5, max_scan=15, engine=None):
    """Read xlsx, auto-promote headers by finding first row with enough non-null cells.
    Replicates the M pattern: PromoteHeaders after skipping junk rows."""
    if engine is None:
        engine = 'calamine'
    try:
        raw = pd.read_excel(path, sheet_name=sheet or 0, header=None, engine=engine)
    except Exception:
        try:
            raw = pd.read_excel(path, sheet_name=sheet or 0, header=None, engine='openpyxl')
        except Exception as e:
            print(f"  ! cannot read {path}: {e}")
            return pd.DataFrame()
    hdr = None
    for i in range(min(max_scan, len(raw))):
        if raw.iloc[i].notna().sum() >= min_header_nonnull:
            hdr = i; break
    if hdr is None:
        return raw
    df = raw.iloc[hdr+1:].copy()
    import unicodedata
    df.columns = [unicodedata.normalize('NFC', str(c).strip()) if pd.notna(c) else f"_c{i}"
                  for i, c in enumerate(raw.iloc[hdr])]
    df = df.reset_index(drop=True)
    df = df.dropna(how='all').reset_index(drop=True)
    return df

def upper_text(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.upper().replace({'NAN': np.nan})
    return df

def to_date(s):
    return pd.to_datetime(s, errors='coerce')

def to_num(s):
    return pd.to_numeric(s, errors='coerce')

def safe_div(a, b):
    return np.where((b == 0) | pd.isna(b), 0, np.divide(a, b, where=(b != 0)))

# ─────────────────────────────────────────────────────────────────────────────
# Dimension tables (PowerQuery: MÃ DANH MỤC folder)
# ─────────────────────────────────────────────────────────────────────────────
def load_dimensions():
    dims = {}
    # Mã đơn vị (Dealer)
    f = p("MA DANH MUC", "MA DON VI - 2026.xlsx")
    if not os.path.exists(f):
        f = p("MA DANH MUC", "MA DON VI.xlsx")
    if os.path.exists(f):
        dims['donvi'] = read_xlsx_promoted(f)
    # Tỉnh PGS
    f = p("MA DANH MUC", "TINH THANH - PGS.xlsx")
    if os.path.exists(f):
        dims['tinh'] = read_xlsx_promoted(f, min_header_nonnull=2)
    # Danh mục kiểu xe
    for fn in ["BANG KE DANH MUC KIEU XE.Xlsx", "DANH MUC KIEU XE.xlsx"]:
        f = p("MA DANH MUC", fn)
        if os.path.exists(f):
            dims['kieuxe'] = read_xlsx_promoted(f); break
    # Danh mục xe
    f = p("MA DANH MUC", "BANG KE DANH MUC XE.Xlsx")
    if os.path.exists(f):
        dims['dmxe'] = read_xlsx_promoted(f)
    # KTV
    f = p("MA DANH MUC", "BANG KE KY THUAT VIEN.Xlsx")
    if os.path.exists(f):
        dims['ktv'] = read_xlsx_promoted(f)
    # DM công việc
    f = p("MA DANH MUC", "DANH MUC CONG VIEC.Xlsx")
    if os.path.exists(f):
        dims['cv'] = read_xlsx_promoted(f)
    # DM SC
    f = p("MA DANH MUC", "DANH MUC TO SUA CHUA.Xlsx")
    if os.path.exists(f):
        dims['sc'] = read_xlsx_promoted(f)
    # DM nhóm vật tư
    f = p("MA DANH MUC", "DANH MUC NHOM VAT TU.Xlsx")
    if os.path.exists(f):
        dims['nhomvt'] = read_xlsx_promoted(f)
    # DM DVGT
    f = p("MA DANH MUC", "DANH MUC DVGT.xlsx")
    if os.path.exists(f):
        dims['dvgt'] = read_xlsx_promoted(f)
    # Mã bảo hiểm
    f = p("MA DANH MUC", "MA BAO HIEM.xlsx")
    if os.path.exists(f):
        dims['baohiem'] = read_xlsx_promoted(f, min_header_nonnull=2)
    # FORD MODEL
    f = p("MA DANH MUC", "FORD MODEL.xlsx")
    if os.path.exists(f):
        dims['ford_model'] = read_xlsx_promoted(f, min_header_nonnull=2)
    return dims

# ─────────────────────────────────────────────────────────────────────────────
# Fact: XUẤT XE (Sales) — replicates 'XUẤT XE' M query
# Sources from BAO CAO CHI TIET KET QUA LAI LO BAN XE.Xlsx (since original is corrupted)
# ─────────────────────────────────────────────────────────────────────────────
def load_xuat_xe():
    candidates = [
        p("DU LIEU", "BAO CAO CHI TIET KET QUA LAI LO BAN XE.Xlsx"),
        p("DU LIEU", "2023 End", "BAO CAO KET QUA LAI LO BAN XE (CHI TIET).Xlsx"),
        p("BÁO CAO KET QUA LAI LO (CHI TIET).Xlsx"),
    ]
    frames = []
    for f in candidates:
        if not os.path.exists(f): continue
        df = read_xlsx_promoted(f)
        if df.empty: continue
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    xx = pd.concat(frames, ignore_index=True)
    # Type conversions matching M
    if 'Ngày bán' in xx.columns:
        xx['Ngày bán'] = to_date(xx['Ngày bán'])
    # Thương hiệu N (Conditional column in M)
    if 'Thương hiệu' in xx.columns:
        th = xx['Thương hiệu'].astype(str).str.upper()
        xx['Thương hiệu N'] = np.where(th.isin(['FORD','HONDA','TOYOTA','BYD']), th, 'KHÁC')
    upper_text(xx, ['Tên đơn vị bảo hiểm'])
    # Numeric fields
    num_cols = ['Tổng lãi gộp xe và phụ kiện (Cả KM)', 'Giá vốn', 'Doanh thu xe', 'Doanh thu phụ kiện']
    for c in num_cols:
        if c in xx.columns: xx[c] = to_num(xx[c])
    return xx

# ─────────────────────────────────────────────────────────────────────────────
# Fact: KÝ HĐ (Contracts)
# ─────────────────────────────────────────────────────────────────────────────
def load_ky_hd():
    f = p("DU LIEU", "2023 End", "BANG KE LAP DIEU KIEN HOP DONG.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if 'Ngày hợp đồng' in df.columns:
        df['Ngày hợp đồng'] = to_date(df['Ngày hợp đồng'])
    if 'Ngày giao xe' in df.columns:
        df['Ngày giao xe'] = to_date(df['Ngày giao xe'])
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Fact: KH KD (Sales Plan)
# ─────────────────────────────────────────────────────────────────────────────
def load_kh_kd():
    f = p("DU LIEU", "BANG KE KE HOACH BAN XE.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    upper_text(df, ['Nhân viên kinh doanh'])
    for c in ['Tháng','Kế hoạch KHTN','Kế hoạch xe giao mới','Kế hoạch KHTN Hot','Mã đơn vị']:
        if c in df.columns: df[c] = to_num(df[c])
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Fact: KHTN (Customer leads) — Try multiple paths since main file may be corrupted
# ─────────────────────────────────────────────────────────────────────────────
def load_khtn():
    f = p("DU LIEU", "BAO CAO KHACH HANG TIEM NANG.Xlsx")
    if not os.path.exists(f) or not _is_valid_xlsx(f):
        return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if df.empty: return df
    if 'Ngày tạo' in df.columns: df['Ngày tạo'] = to_date(df['Ngày tạo'])
    if 'Ngày ký HĐ' in df.columns: df['Ngày ký HĐ'] = to_date(df['Ngày ký HĐ'])
    if 'Trạng thái' in df.columns:
        df = df[~df['Trạng thái'].astype(str).str.upper().isin(['DỪNG THEO DÕI','ĐÃ HOÀN CỌC'])]
    if 'Id khác hàng' in df.columns:
        df['Mã đơn vị'] = df['Id khác hàng'].astype(str).str[:2].apply(to_num)
    if 'Trạng thái' in df.columns:
        ch = df['Trạng thái'].astype(str).str.upper()
        ch = ch.replace({
            'ĐÃ XUẤT HOÁ ĐƠN VÀ GIAO XE':'KHĐ',
            'ĐÃ KÝ HỢP ĐỒNG':'KHĐ',
            'ĐÃ GIAO XE':'KHĐ',
            'VERY HOT':'HOT',
            'WARM':'W'
        })
        df['CHUYỂN ĐỔI'] = ch
    return df

def _is_valid_xlsx(path):
    import zipfile
    try:
        zipfile.ZipFile(path).close(); return True
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────────────────────
# Fact: BK LSC (Service Repair Orders) — Combine 2023, 2024, 2025 folders
# ─────────────────────────────────────────────────────────────────────────────
def load_bk_lsc(years=None):
    frames = []
    if years is None:
        years = os.environ.get('PGS_BK_YEARS','2025').split(',')
    for year_dir in years:
        folder = p("DU LIEU", year_dir.strip())
        if not os.path.isdir(folder): continue
        for fn in sorted(os.listdir(folder)):
            if not fn.lower().endswith(('.xlsx','.xlsm')): continue
            f = os.path.join(folder, fn)
            try:
                df = read_xlsx_promoted(f)
                if df.empty: continue
                df['_source_year'] = year_dir
                df['_source_file'] = fn
                frames.append(df)
                print(f"   BK LSC + {fn}: {len(df)} rows", flush=True)
            except Exception as e:
                print(f"  ! BK LSC skip {fn}: {e}")
    if not frames: return pd.DataFrame()
    bk = pd.concat(frames, ignore_index=True)
    # Replicate: rename Số lệnh -> RO; split LHSC
    if 'Số lệnh' in bk.columns:
        bk['RO'] = bk['Số lệnh']
        # LHSC pattern: '12345.A123' -> first letter after '.'
        s = bk['Số lệnh'].astype(str)
        parts = s.str.split('.', n=1, expand=True)
        bk['LHSC'] = parts[1].astype(str).str[0] if 1 in parts.columns else ''
    # PK KD = LHSC + Phân loại phụ tùng
    if 'Phân loại phụ tùng' in bk.columns and 'LHSC' in bk.columns:
        bk['PK KD'] = bk['LHSC'].astype(str) + ' ' + bk['Phân loại phụ tùng'].astype(str)
    # Conditional Thương hiệu N
    if 'Thương hiệu' in bk.columns:
        th = bk['Thương hiệu'].astype(str).str.upper()
        bk['Thương hiệu N'] = np.where(th.isin(['FORD','HONDA','TOYOTA','BYD']), th, 'KHÁC')
    upper_text(bk, ['Tên đơn vị bảo hiểm'])
    # Type conversions
    if 'Ngày lệnh' in bk.columns:
        bk['Ngày lệnh'] = to_date(bk['Ngày lệnh'])
    for c in ['Tổng doanh thu','Doanh thu công việc','Doanh thu vật tư','Tiền vốn','Lợi nhuận']:
        if c in bk.columns: bk[c] = to_num(bk[c])
    return bk

# ─────────────────────────────────────────────────────────────────────────────
# Fact: KH DVPT (Service Plan)
# ─────────────────────────────────────────────────────────────────────────────
def load_kh_dvpt():
    f = p("DU LIEU", "KH DVPT.xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    try:
        df = pd.read_excel(f, sheet_name=0, engine='calamine')
    except Exception:
        df = pd.read_excel(f, sheet_name=0)
    # Type
    if 'KH THÁNG' in df.columns: df['KH THÁNG'] = to_date(df['KH THÁNG'])
    for c in ['TỔNG DOANH THU','LƯỢT XE VÀO XƯỞNG','DOANH THU CÔNG','DOANH THU SCC',
              'DOANH THU BẢO DƯỠNG','DOANH THU SƠN','DOANH THU GÒ','DOANH THU CÔNG KHÁC',
              'DOANH THU PHỤ TÙNG']:
        if c in df.columns: df[c] = to_num(df[c])
    if 'TỔNG DOANH THU' in df.columns:
        df = df[df['TỔNG DOANH THU'] != 0]
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Fact: UIO (Unit In Operation)
# ─────────────────────────────────────────────────────────────────────────────
def load_uio():
    f = p("DU LIEU", "BAO CAO UIO.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    for c in ['Ngày vào xưởng đầu tiên','Ngày vào xưởng cuối cùng']:
        if c in df.columns: df[c] = to_date(df[c])
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Fact: XE TỒN, XE TỈNH, XE GIAO, XE VÀO RA
# ─────────────────────────────────────────────────────────────────────────────
def load_xe_ton():
    f = p("DU LIEU", "BAO CAO TUOI TON KHO XE (HOA DON).Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if 'Ngày nhập kho' in df.columns: df['Ngày nhập kho'] = to_date(df['Ngày nhập kho'])
    return df

def load_xe_tinh():
    f = p("DU LIEU", "BANG KE XUAT XE.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    return df

def load_xe_giao():
    f = p("DU LIEU", "BANG KE CAP PHIEU XE RA (PHONG KINH DOANH).Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if 'Ngày ra' in df.columns: df['Ngày ra'] = to_date(df['Ngày ra'])
    return df

def load_xe_vao_ra():
    f = p("DU LIEU", "BANG TONG HOP XE VAO RA.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if 'NGÀY VÀO XƯỞNG' in df.columns: df['NGÀY VÀO XƯỞNG'] = to_date(df['NGÀY VÀO XƯỞNG'])
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Fact: BÁN BẢO HIỂM, CÔNG NỢ BH
# ─────────────────────────────────────────────────────────────────────────────
def load_ban_bh():
    f = p("DU LIEU", "BANG KE LENH BAN BAO HIEM.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if 'Ngày' in df.columns: df['Ngày'] = to_date(df['Ngày'])
    return df

def load_cong_no_bh():
    f = p("DU LIEU", "CAN DOI PHAT SINH CONG NO.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if 'Ngày hóa đơn' in df.columns: df['Ngày hóa đơn'] = to_date(df['Ngày hóa đơn'])
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Fact: LƯƠNG, GV VTS, CHI PHÍ End
# ─────────────────────────────────────────────────────────────────────────────
def load_luong():
    f = p("DU LIEU", "SO CHI TIET TAI KHOAN-622.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if 'Ngày C.từ' in df.columns: df['Ngày C.từ'] = to_date(df['Ngày C.từ'])
    if 'Phát sinh nợ' in df.columns: df['Phát sinh nợ'] = to_num(df['Phát sinh nợ'])
    return df

def load_gv_vts():
    f = p("DU LIEU", "SO CHI TIET TAI KHOAN-63223.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if 'Ngày C.từ' in df.columns: df['Ngày C.từ'] = to_date(df['Ngày C.từ'])
    if 'Phát sinh nợ' in df.columns: df['Phát sinh nợ'] = to_num(df['Phát sinh nợ'])
    return df

def load_chi_phi_end():
    f = p("DU LIEU", "SO CHI TIET TAI KHOAN-627.Xlsx")
    if not os.path.exists(f): return pd.DataFrame()
    df = read_xlsx_promoted(f)
    if 'Ngày C.từ' in df.columns: df['Ngày C.từ'] = to_date(df['Ngày C.từ'])
    if 'Phát sinh nợ' in df.columns: df['Phát sinh nợ'] = to_num(df['Phát sinh nợ'])
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Fact: HVN (Honda Vietnam ĐKM data) — Combine all xlsx in HVN folder
# ─────────────────────────────────────────────────────────────────────────────
def load_hvn():
    """Original source was \\ĐKM VN\\HVN (monthly Honda registration) which doesn't exist
    in D:\\TCT PGS\\Claude Data. Per user instruction, skip this folder."""
    return pd.DataFrame()

def _load_hvn_attempt():
    folder = p("HVN")
    if not os.path.isdir(folder): return pd.DataFrame()
    frames = []
    for fn in os.listdir(folder):
        if not fn.lower().endswith('.xlsx'): continue
        if 'pbix' in fn.lower(): continue
        f = os.path.join(folder, fn)
        try:
            df = read_xlsx_promoted(f, min_header_nonnull=4)
            if df.empty: continue
            # Only keep files matching HVN ĐKM schema
            if not any('Nhãn hiệu' in str(c) or 'chuẩn hóa' in str(c) for c in df.columns):
                continue
            df = df.loc[:, ~df.columns.duplicated()]
            if 'Tháng' in df.columns:
                df = df[df['Tháng'].astype(str) != 'Tháng']
            df['_source_file'] = fn
            frames.append(df)
        except Exception as e:
            print(f"  ! HVN skip {fn}: {e}")
    if not frames: return pd.DataFrame()
    all_cols = []
    for d in frames:
        for c in d.columns:
            if c not in all_cols: all_cols.append(c)
    frames = [d.reindex(columns=all_cols) for d in frames]
    hvn = pd.concat(frames, ignore_index=True)
    upper_text(hvn, ['Nhãn hiệu (chuẩn hóa)','Số loại (Chuẩn hóa)','Phân khúc',
                     'Tỉnh/ Thành phố','Region','Chủ sở hữu','Area','For SUV',
                     'Phân khúc (DOC material)'])
    # Build Ngày from Năm + Tháng
    if 'Năm' in hvn.columns and 'Tháng' in hvn.columns:
        try:
            hvn['Năm'] = to_num(hvn['Năm']).astype('Int64')
            hvn['Tháng'] = to_num(hvn['Tháng']).astype('Int64')
            hvn['Ngày'] = pd.to_datetime(
                hvn['Năm'].astype(str)+'-'+hvn['Tháng'].astype(str)+'-01',
                errors='coerce')
        except Exception: pass
    return hvn

# ─────────────────────────────────────────────────────────────────────────────
# Fact: ĐKM (registrations) — District data N.csv
# ─────────────────────────────────────────────────────────────────────────────
def load_dkm():
    f = p("District data N.csv")
    if not os.path.exists(f): return pd.DataFrame()
    try:
        df = pd.read_csv(f, low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(f, encoding='latin-1', low_memory=False)
    # standard column names
    if 'Date' in df.columns: df['Date'] = to_date(df['Date'])
    if 'Unit' in df.columns: df['Unit'] = to_num(df['Unit'])
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Date table
# ─────────────────────────────────────────────────────────────────────────────
def build_date_table(min_d, max_d):
    rng = pd.date_range(min_d, max_d, freq='D')
    return pd.DataFrame({
        'Date': rng,
        'Year': rng.year,
        'Month': rng.month,
        'YearMonth': rng.strftime('%Y-%m'),
        'Quarter': rng.quarter,
        'DayOfWeek': rng.dayofweek+1,
    })

# ─────────────────────────────────────────────────────────────────────────────
# Compute aggregated KPIs (replicating key DAX measures)
# ─────────────────────────────────────────────────────────────────────────────
def _norm_cols(df):
    """Normalize column names to NFC Unicode so comparisons work consistently."""
    import unicodedata
    if df is None or df.empty: return df
    df.columns = [unicodedata.normalize('NFC', str(c)) for c in df.columns]
    return df

def compute_measures(facts, dims):
    """Produce tidy aggregated tables keyed by (Year, Month, Mã đơn vị, Tỉnh, Thương hiệu)."""
    rep = {}
    for k in list(facts.keys()):
        facts[k] = _norm_cols(facts[k])

    xx = facts.get('xuat_xe', pd.DataFrame())
    if not xx.empty and 'Ngày bán' in xx.columns:
        xx = xx.copy()
        xx['Ngày bán'] = pd.to_datetime(xx['Ngày bán'], errors='coerce')
        xx['_Year'] = xx['Ngày bán'].dt.year
        xx['_Month'] = xx['Ngày bán'].dt.month
        if 'Thương hiệu N' not in xx.columns and 'Thương hiệu' in xx.columns:
            th = xx['Thương hiệu'].astype(str).str.upper()
            xx['Thương hiệu N'] = np.where(th.isin(['FORD','HONDA','TOYOTA','BYD']), th, 'KHÁC')
        key_cols = ['_Year','_Month']
        for c in ['Mã đơn vị cơ sở','Thương hiệu N','Thành phố']:
            if c in xx.columns: key_cols.append(c)
        g = xx.groupby(key_cols, dropna=False)
        agg = {'xe_ban': ('Số khung','count')}
        if 'Tổng lãi gộp xe và phụ kiện (Cả KM)' in xx.columns:
            agg['lai_gop'] = ('Tổng lãi gộp xe và phụ kiện (Cả KM)','sum')
        if 'Giá vốn' in xx.columns:
            agg['gia_von'] = ('Giá vốn','sum')
        kpi_xx = g.agg(**agg).reset_index().rename(columns={
            '_Year':'Year','_Month':'Month',
            'Mã đơn vị cơ sở':'Mã đơn vị','Thương hiệu N':'Thương hiệu','Thành phố':'Tỉnh'})
        rep['sales_kpi'] = kpi_xx

    bk = facts.get('bk_lsc', pd.DataFrame())
    if not bk.empty and 'Ngày lệnh' in bk.columns:
        bk['_Year'] = bk['Ngày lệnh'].dt.year
        bk['_Month'] = bk['Ngày lệnh'].dt.month
        key_cols = ['_Year','_Month','Mã đơn vị']
        if 'Thương hiệu N' not in bk.columns and 'Thương hiệu' in bk.columns:
            bk['Thương hiệu N'] = bk['Thương hiệu'].astype(str).str.upper()
        if 'Thương hiệu N' in bk.columns: key_cols.append('Thương hiệu N')
        agg_dict = {'TOTAL_LX':('RO','nunique')}
        if 'Tổng doanh thu' in bk.columns: agg_dict['TOTAL_DT'] = ('Tổng doanh thu','sum')
        if 'Doanh thu công việc' in bk.columns: agg_dict['TOTAL_CLD'] = ('Doanh thu công việc','sum')
        if 'Doanh thu vật tư' in bk.columns: agg_dict['TOTAL_PT'] = ('Doanh thu vật tư','sum')
        if 'Lợi nhuận' in bk.columns: agg_dict['TOTAL_LN_PT'] = ('Lợi nhuận','sum')
        g = bk.groupby(key_cols, dropna=False).agg(**agg_dict).reset_index()
        g = g.rename(columns={'_Year':'Year','_Month':'Month','Thương hiệu N':'Thương hiệu'})
        rep['service_kpi'] = g

    khd = facts.get('kh_dvpt', pd.DataFrame())
    if not khd.empty and 'KH THÁNG' in khd.columns:
        khd['_Year'] = khd['KH THÁNG'].dt.year
        khd['_Month'] = khd['KH THÁNG'].dt.month
        g = khd.groupby(['_Year','_Month','Mã đơn vị'], dropna=False).agg(
            KH_TONG_DT=('TỔNG DOANH THU','sum'),
            KH_LUOT_XE=('LƯỢT XE VÀO XƯỞNG','sum'),
            KH_CLD=('DOANH THU CÔNG','sum'),
            KH_PT=('DOANH THU PHỤ TÙNG','sum')
        ).reset_index().rename(columns={'_Year':'Year','_Month':'Month'})
        rep['service_plan'] = g

    khtn = facts.get('khtn', pd.DataFrame())
    if not khtn.empty and 'Ngày tạo' in khtn.columns:
        khtn['_Year'] = khtn['Ngày tạo'].dt.year
        khtn['_Month'] = khtn['Ngày tạo'].dt.month
        g = khtn.groupby(['_Year','_Month','Mã đơn vị','CHUYỂN ĐỔI'], dropna=False).size().reset_index(name='count')
        rep['funnel'] = g.rename(columns={'_Year':'Year','_Month':'Month'})

    uio = facts.get('uio', pd.DataFrame())
    if not uio.empty:
        rep['uio_summary'] = uio.groupby(['Mã đơn vị','Tỉnh'], dropna=False).agg(
            total_uio=('Số khung','nunique')
        ).reset_index() if 'Số khung' in uio.columns else pd.DataFrame()

    hvn = facts.get('hvn', pd.DataFrame())
    if not hvn.empty and 'Ngày' in hvn.columns:
        hvn['_Year'] = hvn['Ngày'].dt.year
        hvn['_Month'] = hvn['Ngày'].dt.month
        g = hvn.groupby(['_Year','_Month','Tỉnh/ Thành phố','Nhãn hiệu (chuẩn hóa)'], dropna=False).size().reset_index(name='dkm_unit')
        rep['market_share_hvn'] = g.rename(columns={'_Year':'Year','_Month':'Month',
                                                   'Tỉnh/ Thành phố':'Tỉnh',
                                                   'Nhãn hiệu (chuẩn hóa)':'Thương hiệu'})

    dkm = facts.get('dkm', pd.DataFrame())
    if not dkm.empty and 'Date' in dkm.columns:
        dkm['_Year'] = dkm['Date'].dt.year
        dkm['_Month'] = dkm['Date'].dt.month
        grp_cols = ['_Year','_Month']
        if 'Maker' in dkm.columns: grp_cols.append('Maker')
        if 'Tỉnh_corect' in dkm.columns: grp_cols.append('Tỉnh_corect')
        elif 'Province' in dkm.columns: grp_cols.append('Province')
        g = dkm.groupby(grp_cols, dropna=False)['Unit'].sum().reset_index()
        g = g.rename(columns={'_Year':'Year','_Month':'Month','Maker':'Thương hiệu',
                              'Tỉnh_corect':'Tỉnh','Province':'Tỉnh'})
        rep['market_share_dkm'] = g

    return rep

# ─────────────────────────────────────────────────────────────────────────────
# Relationships (Model View) — explicitly defined as in model.bim
# ─────────────────────────────────────────────────────────────────────────────
RELATIONSHIPS = [
    ("XUẤT XE","Mã đơn vị cơ sở","#Mã đơn vị","Mã đơn vị"),
    ("XUẤT XE","Ngày bán","#Date","Date"),
    ("XUẤT XE","Mã kiểu xe","#Danh mục kiểu xe","Mã kiểu xe"),
    ("XUẤT XE","Thành phố","#Tỉnh PGS","TỈNH THÀNH"),
    ("KÝ HĐ","Ngày hợp đồng","#Date","Date"),
    ("KÝ HĐ","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("KÝ HĐ","Mã kiểu xe","#Danh mục kiểu xe","Mã kiểu xe"),
    ("KH KD","Tháng","#Date","Month"),
    ("KH KD","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("KHTN","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("KHTN","Ngày tạo","#Date","Date"),
    ("KHTN","Loại xe","#Danh mục kiểu xe","Mã kiểu xe"),
    ("KHTN","Ngày ký HĐ","#Date","Date (inactive)"),
    ("BK LSC","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("BK LSC","Mã CV","#DM công việc","Mã CV"),
    ("BK LSC","Ngày lệnh","#Date","Date"),
    ("BK LSC","RO","GV VTS","Số RO"),
    ("KH DVPT","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("KH DVPT","KH THÁNG","#Date","Date"),
    ("HVN","Ngày","#Date","Date"),
    ("HVN","Tỉnh/ Thành phố","#Tỉnh PGS","TỈNH THÀNH"),
    ("HVN","Nhãn hiệu (chuẩn hóa)","#Mã đơn vị","Thương hiệu"),
    ("ĐKM","Date","#Date","Date"),
    ("ĐKM","Tỉnh_corect","#Tỉnh PGS","TỈNH THÀNH"),
    ("ĐKM","Maker","#Mã đơn vị","Thương hiệu"),
    ("UIO DV","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("UIO DV","Ngày vào xưởng cuối cùng","#Date","Date"),
    ("UIO DV","TỈNH FULL","#Tỉnh PGS","TỈNH THÀNH"),
    ("LN BÁN XE","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("LN BÁN XE","Số khung","XE TỈNH","Số khung"),
    ("BÁN BẢO HIỂM","MÃ đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("BÁN BẢO HIỂM","Đơn vị bảo hiểm","#BẢO HIỂM","TÊN BẢO HIỂM"),
    ("XE TỒN","Mã kiểu xe","#Danh mục kiểu xe","Mã kiểu xe"),
    ("XE TỒN","Đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("XE TỒN","Ngày nhập kho","#Date","Date"),
    ("XE GIAO","Ngày ra","#Date","Date"),
    ("XE GIAO","Số khung","XUẤT XE","Số khung"),
    ("XE VÀO RA","NGÀY VÀO XƯỞNG","#Date","Date"),
    ("XE VÀO RA","Mã đơn vị cơ sở","#Mã đơn vị","Mã đơn vị"),
    ("DT TỒN XƯỞNG","Mã đơn vị cơ sở","#Mã đơn vị","Mã đơn vị"),
    ("PT TỒN","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("CÔNG NỢ BH","Mã đơn vị cơ sở","#Mã đơn vị","Mã đơn vị"),
    ("LƯƠNG","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("GV VTS","Ngày C.từ","#Date","Date"),
    ("CHI PHÍ End","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("#KTV","Mã tổ","#DM SC","Mã tổ"),
    ("#KTV","Đơn vị","#Mã đơn vị","Mã đơn vị"),
    ("CLĐ KTV","Mã đơn vị","#Mã đơn vị","Mã đơn vị"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("[1/5] Loading dimensions...")
    dims = load_dimensions()
    for k,v in dims.items():
        print(f"   - {k}: {len(v)} rows")
    print("[2/5] Loading facts...")
    facts = {
        'xuat_xe': load_xuat_xe(),
        'ky_hd':   load_ky_hd(),
        'kh_kd':   load_kh_kd(),
        'khtn':    load_khtn(),
        'bk_lsc':  load_bk_lsc(),
        'kh_dvpt': load_kh_dvpt(),
        'uio':     load_uio(),
        'xe_ton':  load_xe_ton(),
        'xe_tinh': load_xe_tinh(),
        'xe_giao': load_xe_giao(),
        'xe_vao_ra': load_xe_vao_ra(),
        'ban_bh':  load_ban_bh(),
        'cong_no_bh': load_cong_no_bh(),
        'luong':   load_luong(),
        'gv_vts':  load_gv_vts(),
        'chi_phi_end': load_chi_phi_end(),
        'hvn':     load_hvn(),
        'dkm':     load_dkm(),
    }
    for k,v in facts.items():
        print(f"   - {k}: {len(v)} rows, cols={list(v.columns)[:5]}")

    print("[3/5] Computing measures...")
    measures = compute_measures(facts, dims)
    for k,v in measures.items():
        print(f"   - {k}: {len(v)} rows")

    print("[4/5] Exporting JSON for dashboard...")
    # Helper: convert df to records JSON-safe
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
    out_path = os.path.join(OUT, 'pgs_data.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, default=str)
    print(f"[5/5] Done → {out_path}  size={os.path.getsize(out_path):,} bytes")

if __name__ == '__main__':
    main()