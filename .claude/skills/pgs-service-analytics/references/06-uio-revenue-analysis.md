# Reference 06 — Phân tích UIO & Doanh thu/VIN/Năm

> **Khi nào load:** Sub-agent `uio-explorer` cần phân tích UIO sâu (im ắng, trẻ/già,
> doanh thu lifecycle); hoặc khi user hỏi "Có bao nhiêu xe chưa quay lại xưởng",
> "Doanh thu trên 1 VIN/năm", "VIN nào đáng gọi nhắc nhất".

---

## 1. UIO segmentation chuẩn

### 1.1 Theo tuổi xe (lifecycle)

```python
import pandas as pd

def segment_uio_by_age(uio_df, today):
    df = uio_df.copy()
    df['ngay_ban'] = pd.to_datetime(df['ngay_ban'])
    df['tuoi_xe_thang'] = ((pd.Timestamp(today) - df['ngay_ban']).dt.days // 30)

    df['lifecycle_stage'] = pd.cut(
        df['tuoi_xe_thang'],
        bins=[-1, 1, 12, 36, 60, 84, 120, 9999],
        labels=['Mới giao (<1m)', 'Năm 1 (1-12m)', 'Năm 2-3 (12-36m)',
                'Năm 4-5 (36-60m)', 'Năm 6-7 (60-84m)', 'Năm 8-10 (84-120m)',
                'Cũ (>10y)']
    )
    return df
```

**Đặc điểm doanh thu mỗi giai đoạn:**

| Lifecycle | Loại RO chính | DT/VIN/năm điển hình | Lưu ý |
|---|---|---|---|
| Mới giao | BDĐK 1k | 800k - 1.2tr | Onboarding KH cực quan trọng |
| Năm 1 | BDĐK 5k, 10k | 2-3tr | KH còn warranty, quay lại đều |
| Năm 2-3 | BDĐK 20k, 30k, 40k | 4-6tr/năm | Peak doanh thu hậu mãi |
| Năm 4-5 | BDĐK 60k, 80k + SC vặt | 5-8tr/năm | Bắt đầu có SC ngoài BDĐK |
| Năm 6-7 | BDĐK 100k+ + SC nhiều | 6-10tr/năm | Peak thứ 2 do SC tăng |
| Năm 8-10 | SC chính + đại tu | 4-12tr/năm dao động lớn | KH bắt đầu tính chuyện đổi xe |
| Cũ | Ngẫu nhiên | < 3tr/năm | Phần lớn KH bỏ xe / chuyển xưởng dã chiến |

### 1.2 Theo trạng thái hoạt động

```python
def segment_uio_by_activity(uio_df, ro_df, today, window_months=12):
    """
    Phân khúc UIO theo hoạt động tại xưởng PGS.
    """
    cutoff = pd.Timestamp(today) - pd.DateOffset(months=window_months)

    # Lần vào xưởng cuối (lấy max ngày từ RO)
    last_visit = (ro_df.groupby('vin')['ngay_mo_RO'].max()
                  .reset_index().rename(columns={'ngay_mo_RO': 'last_RO_date'}))

    df = uio_df.merge(last_visit, on='vin', how='left')
    df['days_since_last_visit'] = (pd.Timestamp(today) - df['last_RO_date']).dt.days

    def classify(row):
        if row['trang_thai'] != 'active':
            return 'Off-list'
        if pd.isna(row['last_RO_date']):
            return 'Chưa từng vào (Cold)'
        d = row['days_since_last_visit']
        if d <= 90:    return 'Active (≤3m)'
        if d <= 180:   return 'Slowing (3-6m)'
        if d <= 365:   return 'Risk (6-12m)'
        if d <= 730:   return 'Silent (12-24m)'
        return 'Lost (>24m)'

    df['activity_segment'] = df.apply(classify, axis=1)
    return df
```

**Bảng phân khúc:**

| Segment | Định nghĩa | Hành động |
|---|---|---|
| Active (≤3m) | Đã vào xưởng trong 3 tháng | Giữ chân, upsell PT |
| Slowing (3-6m) | 3-6 tháng chưa vào | Gọi nhắc nhẹ |
| Risk (6-12m) | 6-12 tháng chưa vào | Gọi nhắc + ưu đãi |
| Silent (12-24m) | 12-24 tháng | Chiến dịch recall mạnh |
| Lost (>24m) | > 24 tháng | Gọi 1 lần cuối, nếu không phản hồi → archive |
| Chưa từng vào | Chưa từng có RO tại PGS | Đặc biệt: KH mua PGS nhưng chưa vào — sales bàn giao kém |

---

## 2. Doanh thu/VIN/Năm (LTV proxy)

### 2.1 Công thức

```
DT/VIN/năm = Σ tong_doanh_thu của VIN trong 12 tháng / 1
```

```python
def revenue_per_vin_per_year(ro_df, ky_start, ky_end):
    """
    Doanh thu trung bình mỗi VIN trong window 12 tháng.
    """
    df = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
               (ro_df['ngay_dong_RO'].between(ky_start, ky_end)) &
               (ro_df['loai_RO'] != 'BH')]

    by_vin = df.groupby('vin').agg(
        total_revenue=('tong_doanh_thu', 'sum'),
        n_RO=('ma_RO', 'count'),
        last_visit=('ngay_dong_RO', 'max')
    ).reset_index()

    return {
        'n_vin_active_in_window': len(by_vin),
        'DT_TB_per_vin_per_year': by_vin['total_revenue'].mean(),
        'DT_median_per_vin': by_vin['total_revenue'].median(),
        'top_decile': by_vin['total_revenue'].quantile(0.9),
        'bottom_decile': by_vin['total_revenue'].quantile(0.1),
        'detail_by_vin': by_vin
    }
```

### 2.2 Phân khúc VIN theo doanh thu

```python
def vin_value_segment(by_vin_df):
    """
    Phân VIN thành 4 nhóm theo decile doanh thu.
    """
    df = by_vin_df.copy()
    df['quartile'] = pd.qcut(df['total_revenue'], q=4,
                             labels=['Q4_low', 'Q3_mid_low', 'Q2_mid_high', 'Q1_high'])
    return df.groupby('quartile').agg(
        n_vin=('vin', 'count'),
        avg_DT=('total_revenue', 'mean'),
        avg_n_RO=('n_RO', 'mean'),
        sum_DT=('total_revenue', 'sum')
    )
```

**Insight thường gặp:**
- Top 25% VIN tạo ra 60-70% doanh thu xưởng → **ưu tiên giữ chân**.
- Bottom 25% VIN có thể chỉ vào 1 lần BDĐK rồi bỏ → cần recall.

### 2.3 LTV (Lifetime Value) ước lượng

```python
def estimate_vin_ltv(by_vin_df, uio_df, expected_lifecycle_years=8):
    """
    LTV = DT/năm hiện tại × số năm còn lại trong lifecycle.
    """
    df = by_vin_df.merge(
        uio_df[['vin', 'ngay_ban']], on='vin'
    )
    df['ngay_ban'] = pd.to_datetime(df['ngay_ban'])
    df['tuoi_nam'] = (pd.Timestamp.now() - df['ngay_ban']).dt.days // 365
    df['nam_con_lai'] = (expected_lifecycle_years - df['tuoi_nam']).clip(lower=0)
    df['LTV_uoc'] = df['total_revenue'] * df['nam_con_lai']
    return df.sort_values('LTV_uoc', ascending=False)
```

→ Sub-agent `vin-recaller` ưu tiên gọi nhắc VIN có LTV ước cao.

---

## 3. UIO im ắng — phân tích sâu

### 3.1 Tách UIO im ắng theo độ ưu tiên gọi lại

```python
def prioritize_silent_vin(silent_df, uio_df, today):
    """
    Xếp hạng VIN im ắng theo độ ưu tiên gọi lại.
    Tiêu chí:
    - Tuổi xe trẻ (< 5 năm): cao
    - Có lịch sử vào xưởng nhiều trước đây: cao
    - Model bán chạy / có KH gốc PGS: cao
    """
    df = silent_df.merge(
        uio_df[['vin', 'ngay_ban', 'model', 'dai_ly_ban_dau']], on='vin'
    )
    df['tuoi_xe_nam'] = (pd.Timestamp(today) - pd.to_datetime(df['ngay_ban'])).dt.days // 365

    def score(row):
        s = 0
        # Tuổi xe (xe trẻ ưu tiên)
        if row['tuoi_xe_nam'] < 3: s += 30
        elif row['tuoi_xe_nam'] < 5: s += 20
        elif row['tuoi_xe_nam'] < 7: s += 10

        # Lịch sử RO (nhiều RO trước đây = quan tâm xưởng cũ)
        n_RO_history = row.get('n_RO_lifetime', 0)
        if n_RO_history >= 6: s += 25
        elif n_RO_history >= 3: s += 15
        elif n_RO_history >= 1: s += 5

        # PGS bán đầu (KH gốc, dễ gọi lại)
        if row['dai_ly_ban_dau'] == 'PGS' or 'PGS' in str(row['dai_ly_ban_dau']):
            s += 20

        # Im ắng càng lâu càng khó gọi (giảm điểm)
        d = row['days_since_last_visit']
        if d > 730: s -= 15
        elif d > 540: s -= 5

        return s

    df['priority_score'] = df.apply(score, axis=1)
    return df.sort_values('priority_score', ascending=False)
```

### 3.2 Phân lô gọi cho CVDV

```python
def split_recall_to_cvdv(prioritized_df, n_cvdv=4, n_per_week=200):
    """
    Phân danh sách recall cho N CVDV, mỗi tuần n_per_week lượt.
    """
    total_top = prioritized_df.head(n_cvdv * n_per_week).copy()
    total_top['phan_lo'] = pd.cut(
        range(len(total_top)),
        bins=n_cvdv,
        labels=[f'CVDV{i+1}' for i in range(n_cvdv)]
    )
    return total_top
```

### 3.3 Mẫu file gọi lại (xuất xlsx cho CVDV)

```python
def export_recall_template(prioritized_df, output_path, week_start_date):
    """
    Xuất file Excel cho CVDV gọi lại theo tuần.
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Recall_Tuần"

    headers = ['STT', 'vin', 'sdt_KH', 'ten_KH', 'model', 'tuoi_xe_nam',
               'days_since_last_visit', 'last_RO_date',
               'priority_score', 'cvdv_phu_trach',
               'ngay_goi', 'ket_qua', 'cuoc_hen_dat', 'ngay_hen', 'note']
    ws.append(headers)

    # Style header
    blue = PatternFill(bgColor='4472C4', fill_type='solid')
    white = Font(bold=True, color='FFFFFF')
    for col in range(1, len(headers)+1):
        c = ws.cell(row=1, column=col)
        c.fill = blue
        c.font = white
        c.alignment = Alignment(horizontal='center', wrap_text=True)
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = 'A2'

    # Data
    for i, row in prioritized_df.iterrows():
        ws.append([
            i+1, row['vin'], row.get('sdt_KH', ''), row.get('ten_KH', ''),
            row['model'], row['tuoi_xe_nam'],
            row['days_since_last_visit'],
            row['last_RO_date'].strftime('%Y-%m-%d') if pd.notna(row['last_RO_date']) else '',
            row['priority_score'], row.get('phan_lo', ''),
            '', '', '', '', ''   # 5 cột để CVDV cập nhật
        ])

    # Data validation cho cột ket_qua
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(
        type="list",
        formula1='"Bắt máy,Bận đầu,Tắt máy,Số sai,KH từ chối,Đặt hẹn,Khác"',
        allow_blank=True
    )
    ws.add_data_validation(dv)
    dv.add('L2:L1000')

    wb.save(output_path)
    return output_path
```

---

## 4. Doanh thu theo cohort (KH mua cùng kỳ)

### 4.1 Cohort retention analysis

```python
def cohort_retention(uio_df, ro_df, today):
    """
    Bao nhiêu % KH mua tháng X vẫn vào xưởng tháng X+1, X+3, X+6, X+12, X+24?
    """
    uio = uio_df[uio_df['trang_thai'] == 'active'].copy()
    uio['cohort_month'] = pd.to_datetime(uio['ngay_ban']).dt.to_period('M')

    ro = ro_df[ro_df['trang_thai_RO'] == 'closed'].copy()
    ro['ro_month'] = pd.to_datetime(ro['ngay_mo_RO']).dt.to_period('M')

    # Map mỗi RO về cohort của VIN
    merged = ro.merge(uio[['vin', 'cohort_month']], on='vin')
    merged['months_since_purchase'] = (merged['ro_month'] - merged['cohort_month']).apply(
        lambda x: x.n if hasattr(x, 'n') else int(x)
    )

    cohort_table = merged.pivot_table(
        index='cohort_month',
        columns='months_since_purchase',
        values='vin',
        aggfunc='nunique',
        fill_value=0
    )

    # Chia cho cohort size
    cohort_size = uio.groupby('cohort_month')['vin'].nunique()
    cohort_pct = cohort_table.div(cohort_size, axis=0) * 100

    return cohort_pct
```

**Đọc cohort table:**
- Hàng = tháng KH mua xe.
- Cột = số tháng sau khi mua.
- Giá trị = % cohort vào xưởng tháng đó.

→ Phát hiện cohort nào "rớt" sau tháng X → diagnose nguyên nhân.

### 4.2 Phát hiện cohort yếu

```python
def weak_cohorts(cohort_pct, benchmark_month_12=70):
    """
    Tìm cohort có retention 12 tháng < 70%.
    """
    if 12 not in cohort_pct.columns:
        return None
    weak = cohort_pct[cohort_pct[12] < benchmark_month_12]
    return weak[12].sort_values()
```

---

## 5. Doanh thu theo model (kết hợp UIO × RO)

### 5.1 DT/Model/VIN/Năm

```python
def revenue_per_model(uio_df, ro_df, ky_start, ky_end):
    """
    Doanh thu trung bình mỗi VIN theo model trong window.
    Phục vụ phân tích: model nào hậu mãi tốt nhất.
    """
    ro = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
               (ro_df['ngay_dong_RO'].between(ky_start, ky_end)) &
               (ro_df['loai_RO'] != 'BH')]

    by_vin = ro.groupby('vin')['tong_doanh_thu'].sum().reset_index()
    by_vin = by_vin.merge(uio_df[['vin', 'model']], on='vin')

    by_model = by_vin.groupby('model').agg(
        n_vin_co_RO=('vin', 'count'),
        DT_TB_per_vin=('tong_doanh_thu', 'mean'),
        DT_total=('tong_doanh_thu', 'sum')
    ).sort_values('DT_total', ascending=False)

    # UIO active của model (mẫu số)
    uio_active = uio_df[uio_df['trang_thai'] == 'active']
    by_model['n_uio_active'] = by_model.index.map(
        lambda m: (uio_active['model'] == m).sum()
    )
    by_model['capture_rate_pct'] = (by_model['n_vin_co_RO'] / by_model['n_uio_active']) * 100

    return by_model
```

### 5.2 Insight pattern

| Model có | Diễn giải |
|---|---|
| DT/VIN cao + capture cao | Model "vàng" — KH trung thành, hậu mãi tốt |
| DT/VIN cao + capture thấp | Cần recall để nâng capture |
| DT/VIN thấp + capture cao | KH chỉ làm BDĐK, ít upsell — đào tạo CVDV |
| DT/VIN thấp + capture thấp | Model có vấn đề — chuyển sang xưởng dã chiến? |

---

## 6. Cross-link với Sales (Sales-Service handoff)

### 6.1 Phát hiện KH cũ có thể đổi xe

```python
def candidates_for_upgrade(uio_df, ro_df, today):
    """
    KH mua xe ≥ 3-5 năm + vẫn vào xưởng đều = candidate refer cho Sales.
    """
    df = uio_df.copy()
    df['ngay_ban'] = pd.to_datetime(df['ngay_ban'])
    df['tuoi_nam'] = (pd.Timestamp(today) - df['ngay_ban']).dt.days // 365

    # Thêm số RO trong 12 tháng qua
    cutoff = pd.Timestamp(today) - pd.DateOffset(months=12)
    ro_recent = ro_df[ro_df['ngay_mo_RO'] >= cutoff]
    n_RO_per_vin = ro_recent.groupby('vin').size().reset_index(name='n_RO_12m')

    df = df.merge(n_RO_per_vin, on='vin', how='left').fillna({'n_RO_12m': 0})

    candidates = df[
        (df['trang_thai'] == 'active') &
        (df['tuoi_nam'].between(3, 5)) &
        (df['n_RO_12m'] >= 1)
    ].sort_values(['n_RO_12m', 'tuoi_nam'], ascending=[False, False])

    return candidates[['vin', 'sdt_KH', 'model', 'tuoi_nam', 'n_RO_12m']]
```

→ Handoff sang `pgs-sales-analytics` qua main agent với payload chuẩn (xem `plugins.md`).

---

## 7. Báo cáo UIO chuẩn

```markdown
## 5. Phân tích UIO (kỳ T4/2026, snapshot 30/04)

**UIO tổng:** 4,127 VIN
- Active: 2,840 (68.8%)
- Đã thanh lý: 285
- Đã đổi chủ: 612
- Không liên lạc: 390

**Phân khúc hoạt động (Active 2,840 VIN):**
| Segment | n VIN | % | DT/VIN/năm |
|---|---|---|---|
| Active (≤3m) | 1,460 | 51% | 5.8tr |
| Slowing (3-6m) | 380 | 13% | 4.2tr |
| Risk (6-12m) | 314 | 11% | 2.5tr |
| Silent (12-24m) | 480 | 17% | 0 (chưa quay lại) |
| Lost (>24m) | 206 | 7% | 0 |

**Capture rate 12 tháng:** 72.0% (2,154/2,994 VIN active đã vào ≥ 1 lần).

**Top 3 model DT/VIN/năm cao nhất:**
1. Fortuner: 8.2tr/năm (n=125 VIN)
2. CR-V: 7.5tr/năm (n=87)
3. Camry: 7.1tr/năm (n=42)

**Top 3 model capture rate cao nhất:**
1. Vios: 81% (n=420 active)
2. Innova Cross: 78% (n=180)
3. Yaris Cross: 76% (n=95)

**Cohort yếu phát hiện:**
- Cohort 06/2024 retention 12 tháng = 58% (vs benchmark 70%) → diagnose nguyên nhân.

**Action xuất ra (vin-recaller):**
- File `recall_T5_DongNai.xlsx`: 800 VIN ưu tiên (200 × 4 CVDV).
- Top 50 VIN trong nhóm "có thể đổi xe": handoff sang Sales (qua main).
```

---

## 8. Quy tắc bất biến

1. **UIO snapshot phải gắn với ngày cụ thể** — UIO thay đổi liên tục (KH bán xe, hãng triệu hồi).
2. **DT/VIN/năm chỉ tính RO không phải BH** — bảo hành làm méo số liệu.
3. **VIN ngoài UIO (xe đối thủ vào sửa) tách riêng** — không gộp vào UIO PGS.
4. **Capture rate phải dùng chung window 12 tháng** — không thay đổi giữa các kỳ.
5. **Recall ưu tiên VIN trẻ + KH PGS gốc** — ROI cao hơn.
6. **VIN > 24 tháng im ắng → archive sau 1 lần gọi cuối** — không gọi mãi (tốn CVDV).
7. **Cohort analysis cần ≥ 12 tháng dữ liệu** — không phân tích cohort < 6 tháng.

---

## 9. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| VIN trong UIO nhưng không có sdt | Loại khỏi recall, flag để cập nhật |
| 1 KH nhiều xe | Dedupe theo sdt khi gọi recall, tránh gọi 5 lần |
| KH đã chuyển nhà → số cũ không đúng | Status `khong_lien_lac`, archive |
| Xe đã bán lại cho người khác | Cập nhật `trang_thai = da_doi_chu` + tách KH cũ khỏi recall |
| Hãng triệu hồi → mọi VIN diện đó vào xưởng | Tách campaign recall riêng, không gộp vào capture rate thường |
| KH cũ + KH mới cùng VIN (sang tay) | Lấy KH hiện tại làm mặc định; lịch sử RO giữ nguyên |
| Model đã ngừng SX | Vẫn tính UIO, nhưng đánh dấu "EOL" → ưu tiên upgrade campaign |
