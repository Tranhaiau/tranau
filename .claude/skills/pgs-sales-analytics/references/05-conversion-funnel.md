# Reference 05 — Phễu Chuyển đổi & Năng lực TVBH

> **Khi nào load:** Sub-agent `funnel-diagnoser` cần tính tỷ lệ chuyển đổi pipeline,
> đánh giá năng lực TVBH, hoặc khi user hỏi "TVBH nào yếu", "Tỷ lệ chốt thấp do đâu".

---

## 1. Mô hình phễu chuẩn PGS (5 stage)

```
   ┌─────────────────────────────────────┐
   │  COLD (KHTN tiếp cận)               │  Stage 1
   │  - Có sđt, đã tiếp xúc lần đầu      │
   └──────────────┬──────────────────────┘
                  │ Cold→Warm
   ┌──────────────▼──────────────────────┐
   │  WARM (báo giá / lái thử)           │  Stage 2
   │  - Đã được báo giá hoặc lái thử     │
   └──────────────┬──────────────────────┘
                  │ Warm→Hot
   ┌──────────────▼──────────────────────┐
   │  HOT (đặt cọc)                      │  Stage 3
   │  - Đã cọc + cam kết mua             │
   └──────────────┬──────────────────────┘
                  │ Hot→HĐ
   ┌──────────────▼──────────────────────┐
   │  HĐ (ký hợp đồng + giao xe)         │  Stage 4
   │  - Đã ký HĐ chính thức              │
   └─────────────────────────────────────┘

   ┌─────────────────────────────────────┐
   │  MẤT (lost)                         │  Stage 5 (off-funnel)
   │  - KH chuyển đối thủ / huỷ ý định   │
   └─────────────────────────────────────┘
```

### 1.1 Khi nào chuyển stage?

| Chuyển | Bằng chứng cần |
|---|---|
| Tiếp cận → Cold | TVBH có sdt + ngày tiếp xúc đầu (`ngay_tiep_can`) |
| Cold → Warm | Có `ngay_bao_gia` HOẶC `ngay_lai_thu` |
| Warm → Hot | Có `ngay_dat_coc` + số tiền cọc thực tế trong hệ thống |
| Hot → HĐ | Có `ngay_chot` + `ma_HD` link sang `sales_pgs` |
| Bất kỳ → Mất | Có `ngay_mat` + `ly_do_mat` |

### 1.2 Chống "auto-promote" stage

Đôi khi TVBH đẩy KH lên stage cao hơn để báo cáo đẹp:
- Cập nhật `trang_thai = Hot` mà không có `ngay_dat_coc`.
- Chuyển `Cold → Warm` chỉ vì gọi điện thêm 1 lần.

→ Hook H2 trong `01-data-schema.md` đã chặn các trường hợp này.

---

## 2. Công thức tính tỷ lệ chuyển đổi

### 2.1 Conversion rates (CR)

```python
def funnel_conversion_rates(quan_tri_df, ky_start, ky_end, scope_b2c=True):
    """
    Tính tỷ lệ chuyển đổi cho 1 team/chi nhánh trong kỳ.

    Quy ước: tính trên tập KHTN có ngay_tiep_can trong kỳ
    (chứ không phải các trạng thái snapshot tại thời điểm).
    """
    df = quan_tri_df.copy()
    if scope_b2c:
        df = df[df.get('loai_KH', 'B2C') == 'B2C']
    df = df[df['ngay_tiep_can'].between(ky_start, ky_end)]

    n_cold = len(df)  # tất cả KHTN tiếp cận trong kỳ = Cold
    n_warm = df['ngay_bao_gia'].notna() | df['ngay_lai_thu'].notna()
    n_warm = n_warm.sum()
    n_hot = df['ngay_dat_coc'].notna().sum()
    n_HD = (df['trang_thai'] == 'HĐ').sum()
    n_mat = (df['trang_thai'] == 'Mất').sum()
    n_active = n_cold - n_HD - n_mat  # còn trong pipeline

    return {
        'n_cold': n_cold,
        'n_warm': n_warm,
        'n_hot': n_hot,
        'n_HD': n_HD,
        'n_mat': n_mat,
        'n_active': n_active,
        'cr_cold_to_warm': safe_div(n_warm, n_cold),
        'cr_warm_to_hot': safe_div(n_hot, n_warm),
        'cr_hot_to_HD': safe_div(n_HD, n_hot),
        'cr_cold_to_HD_overall': safe_div(n_HD, n_cold),
        'cr_lost_rate': safe_div(n_mat, n_cold)
    }

def safe_div(a, b):
    return a / b if b > 0 else None
```

### 2.2 Diễn giải tỷ lệ (benchmark)

| CR | "Tốt" | "Trung bình" | "Yếu" | Lưu ý |
|---|---|---|---|---|
| Cold → Warm | > 60% | 45-60% | < 45% | Phụ thuộc nguồn KHTN (online thường thấp hơn walkin) |
| Warm → Hot | > 45% | 30-45% | < 30% | Phụ thuộc khả năng chốt deal & cạnh tranh giá |
| Hot → HĐ | > 65% | 50-65% | < 50% | Có thể do thủ tục tài chính kéo dài |
| Cold → HĐ overall | > 20% | 12-20% | < 12% | KPI tổng phổ biến nhất |
| Lost rate | < 25% | 25-40% | > 40% | Cao = áp lực cạnh tranh hoặc TVBH yếu |

> **Cảnh báo Hook H3:** Nếu mẫu < 30 KHTN/kỳ → tỷ lệ không đáng tin.
> Mẫu < 50 → có thể tham khảo nhưng nên gắn cờ "mẫu nhỏ".

---

## 3. Funnel theo TVBH (đánh giá năng lực cá nhân)

### 3.1 Bảng KPI cá nhân

```python
def per_tvbh_funnel(quan_tri_df, ky_start, ky_end):
    """
    Tính các KPI cá nhân TVBH trong kỳ.
    """
    df = quan_tri_df[quan_tri_df['ngay_tiep_can'].between(ky_start, ky_end)]

    grouped = df.groupby('ma_TVBH')
    rows = []
    for ma_TVBH, sub in grouped:
        kpis = funnel_conversion_rates(sub, ky_start, ky_end)
        kpis['ma_TVBH'] = ma_TVBH
        kpis['n_KHTN'] = len(sub)

        # Thời gian trung bình Cold → HĐ
        sub_HD = sub[sub['trang_thai'] == 'HĐ']
        if len(sub_HD) > 0:
            days = (pd.to_datetime(sub_HD['ngay_chot']) -
                    pd.to_datetime(sub_HD['ngay_tiep_can'])).dt.days
            kpis['ngay_TB_cold_to_HD'] = days.mean()
        else:
            kpis['ngay_TB_cold_to_HD'] = None

        # Tỷ lệ mời lái thử
        kpis['cr_cold_to_lai_thu'] = safe_div(
            sub['ngay_lai_thu'].notna().sum(), len(sub)
        )

        rows.append(kpis)

    return pd.DataFrame(rows)
```

### 3.2 So sánh với TB team — tìm pattern yếu

```python
def diagnose_tvbh_pattern(per_tvbh_df, team_avg, threshold=0.7):
    """
    Diagnose: TVBH có CR thấp hơn 70% TB team = "yếu" ở stage đó.
    """
    diagnoses = []
    for _, row in per_tvbh_df.iterrows():
        if row['n_KHTN'] < 30:
            diagnoses.append({
                'ma_TVBH': row['ma_TVBH'],
                'pattern': 'sample_too_small',
                'note': f"Mẫu {row['n_KHTN']} KHTN — không kết luận"
            })
            continue

        weak_stages = []
        if row['cr_cold_to_warm'] < team_avg['cr_cold_to_warm'] * threshold:
            weak_stages.append('Cold→Warm')
        if row['cr_warm_to_hot'] < team_avg['cr_warm_to_hot'] * threshold:
            weak_stages.append('Warm→Hot')
        if row['cr_hot_to_HD'] < team_avg['cr_hot_to_HD'] * threshold:
            weak_stages.append('Hot→HĐ')

        if not weak_stages:
            pattern = 'on_track'
        elif len(weak_stages) == 1:
            pattern = f"{weak_stages[0].lower().replace('→', '_to_')}_yeu"
        else:
            pattern = 'multi_stage_yeu'

        diagnoses.append({
            'ma_TVBH': row['ma_TVBH'],
            'pattern': pattern,
            'weak_stages': weak_stages,
            'cr_chot_vs_team': row['cr_cold_to_HD_overall'] / team_avg['cr_cold_to_HD_overall']
        })

    return pd.DataFrame(diagnoses)
```

### 3.3 Pattern → Module training tương ứng (cho handoff Layer 5)

```python
PATTERN_TO_TRAINING_MODULE = {
    'cold_to_warm_yeu':     ['khai_thac_nhu_cau', 'tao_thien_cam_dau_tien'],
    'warm_to_hot_yeu':      ['xu_ly_tu_choi', 'thuc_hien_lai_thu_chuyen_nghiep'],
    'hot_to_hd_yeu':        ['chot_deal', 'ho_tro_thu_tuc_tai_chinh'],
    'multi_stage_yeu':      ['kien_thuc_san_pham_co_ban', 'ky_nang_giao_tiep_KH'],
    'sample_too_small':     [],  # không đề xuất training, cần thời gian
    'on_track':             []   # đã tốt, không cần
}
```

→ `funnel-diagnoser` xuất `suggested_handoff` với module này, main quyết định gửi sang `pgs-training-management`.

---

## 4. Vòng quay pipeline (pipeline velocity)

### 4.1 Công thức

```
Pipeline Velocity = (n_KHTN_active × CR_to_HD × Avg_HD_value) / Avg_Cycle_Days

Đơn vị: VND/ngày — "Mỗi ngày pipeline tạo ra bao nhiêu doanh số"
```

### 4.2 Code

```python
def pipeline_velocity(quan_tri_df, ky_start, ky_end):
    df = quan_tri_df[quan_tri_df['trang_thai'].isin(['Cold', 'Warm', 'Hot'])]
    n_active = len(df)

    # CR overall trên history 90 ngày
    history = quan_tri_df[
        quan_tri_df['ngay_tiep_can'].between(
            pd.Timestamp(ky_end) - pd.Timedelta(days=90),
            pd.Timestamp(ky_end)
        )
    ]
    n_hist = len(history)
    n_HD_hist = (history['trang_thai'] == 'HĐ').sum()
    cr_to_HD = n_HD_hist / max(n_hist, 1)

    # Avg HD value
    avg_HD_value = history.loc[
        history['trang_thai'] == 'HĐ', 'gia_tri_du_kien'
    ].mean() or 0

    # Avg cycle days
    HD_rows = history[history['trang_thai'] == 'HĐ']
    if len(HD_rows) > 0:
        cycle_days = (pd.to_datetime(HD_rows['ngay_chot']) -
                      pd.to_datetime(HD_rows['ngay_tiep_can'])).dt.days.mean()
    else:
        cycle_days = 30  # default

    velocity = (n_active * cr_to_HD * avg_HD_value) / max(cycle_days, 1)
    return {
        'velocity_VND_per_day': velocity,
        'n_active': n_active,
        'cr_to_HD': cr_to_HD,
        'avg_HD_value': avg_HD_value,
        'avg_cycle_days': cycle_days
    }
```

### 4.3 Diễn giải

- Velocity tăng → pipeline khoẻ.
- Velocity giảm dù n_active tăng → KH chất lượng thấp hoặc cycle dài hơn.
- Velocity giảm dù CR ổn → giá trị HĐ trung bình giảm (KH chuyển sang model rẻ hơn).

---

## 5. Lý do mất KH (lost analysis)

### 5.1 Phân loại lý do mất

```python
LOST_REASONS = {
    'gia_cao': 'Giá cao hơn đối thủ',
    'thieu_mau_xe': 'Không có màu/version KH muốn',
    'cho_doi_qua_lau': 'Lead time giao xe quá lâu',
    'doi_thu_khuyen_mai_tot': 'Đối thủ KM hấp dẫn hơn',
    'KH_doi_y': 'KH thay đổi ý định / hoãn kế hoạch',
    'tu_van_chua_du': 'Tư vấn chưa đáp ứng nhu cầu',
    'tai_chinh_khong_duoc': 'Không vay được hoặc không đủ tiền',
    'gioi_thieu_xe_khac': 'TVBH giới thiệu sang xe phù hợp hơn (không phải mất tệ)',
    'khac': 'Khác'
}

def lost_analysis(quan_tri_df, ky_start, ky_end):
    lost = quan_tri_df[
        (quan_tri_df['trang_thai'] == 'Mất') &
        (quan_tri_df['ngay_mat'].between(ky_start, ky_end))
    ]
    if len(lost) == 0:
        return None

    breakdown = lost['ly_do_mat'].value_counts(normalize=True).to_dict()

    # Tách "lành tính" (giới thiệu xe khác) vs "thực mất"
    benign = breakdown.pop('gioi_thieu_xe_khac', 0)
    return {
        'n_lost': len(lost),
        'lost_breakdown_pct': breakdown,
        'benign_pct': benign,
        'top_3_reasons': sorted(breakdown.items(), key=lambda x: -x[1])[:3]
    }
```

### 5.2 Action mapping

| Lý do mất chiếm > 25% | Action |
|---|---|
| `gia_cao` | Review giá vs đối thủ; xem xét chương trình tài chính/KM |
| `thieu_mau_xe` | Đề xuất hãng nhập thêm; điều chuyển kho từ chi nhánh khác |
| `cho_doi_qua_lau` | Cải thiện forecast nhu cầu; đặt hàng sớm hơn |
| `doi_thu_KM_tot` | Theo dõi sát đối thủ; đề xuất KM phản công |
| `tu_van_chua_du` | Training TVBH (handoff sang skill training) |
| `tai_chinh_khong_duoc` | Mở rộng partner ngân hàng, kế hoạch trả góp |

---

## 6. Phát hiện bán "luồn" pipeline

### 6.1 Định nghĩa

HĐ trong `sales_pgs.xlsx` mà không có `ma_KHTN` tương ứng trong `quan_tri.xlsx`.
→ TVBH bán ngoài quy trình, không cập nhật pipeline → mất dữ liệu cải tiến.

### 6.2 Code phát hiện

```python
def detect_pipeline_skip(sales_pgs, quan_tri):
    """
    Tìm HĐ trong sales_pgs nhưng KH không có trong quan_tri.
    Match theo sdt hoặc tên (fuzzy).
    """
    # Lấy danh sách KH đã bán HĐ
    HD_customers = sales_pgs[['ma_HD', 'ma_TVBH', 'sdt', 'ngay_HD']].copy()

    # Lấy danh sách KH có trong quan_tri (kể cả Mất)
    qt_customers = quan_tri[['ma_KHTN', 'ma_TVBH', 'sdt']].copy()

    # Match theo sdt
    HD_with_pipe = HD_customers.merge(
        qt_customers[['sdt', 'ma_KHTN']],
        on='sdt', how='left'
    )

    skip = HD_with_pipe[HD_with_pipe['ma_KHTN'].isna()]
    return skip[['ma_HD', 'ma_TVBH', 'sdt', 'ngay_HD']]
```

### 6.3 Diễn giải

- < 5% HĐ luồn: bình thường (có thể do KH refer trực tiếp đặt cọc nhanh).
- 5-15%: cảnh báo, cần quy trình.
- \> 15%: nghiêm trọng, có rủi ro mất kiểm soát chất lượng pipeline.

→ `funnel-diagnoser` flag cho `plan-builder` đưa vào nhóm GP "Quy trình".

---

## 7. Heatmap pipeline theo ngày trong tuần

```python
def pipeline_heatmap_by_dow(quan_tri_df, period_days=90):
    """
    Phát hiện pattern: ngày nào KHTN tiếp cận nhiều, ngày nào chuyển đổi cao.
    """
    df = quan_tri_df.copy()
    df['ngay_tiep_can'] = pd.to_datetime(df['ngay_tiep_can'])
    cutoff = df['ngay_tiep_can'].max() - pd.Timedelta(days=period_days)
    df = df[df['ngay_tiep_can'] >= cutoff]

    df['dow'] = df['ngay_tiep_can'].dt.day_name()
    by_dow = df.groupby('dow').agg(
        n_cold=('ma_KHTN', 'count'),
        n_HD=('trang_thai', lambda x: (x == 'HĐ').sum())
    )
    by_dow['cr_to_HD'] = by_dow['n_HD'] / by_dow['n_cold']
    return by_dow
```

Insight thường gặp:
- T7-CN: walkin nhiều, CR thấp (KH "đi xem cho biết").
- T2-T4: walkin ít, CR cao (KH có ý định mua thật sự).
- T5-T6: cân bằng.

→ Bố trí lịch trực TVBH cho hợp lý.

---

## 8. Quy tắc trình bày phần Phễu trong báo cáo

### 8.1 Mẫu chuẩn

```markdown
## 3.b. Phễu chuyển đổi & Năng lực TVBH (kỳ T4/2026)

**Phễu team (n=142 KHTN B2C):**
| Stage | Số | CR sang stage sau |
|---|---|---|
| Cold | 142 | — |
| Warm | 87 | 61.3% |
| Hot | 41 | 47.1% |
| HĐ | 28 | 68.3% |
| (Cold→HĐ overall) | 19.7% |
| Mất | 35 | 24.6% |

**Top 3 lý do mất:**
1. Đối thủ KM tốt hơn (32%) — Hyundai Custin tặng BHVC + 30tr T4
2. Giá cao (24%) — phân khúc B-SUV cạnh tranh giá gắt
3. Lead time giao xe (18%) — Yaris Cross thiếu màu trắng ngọc trai

**TVBH cần chú ý:**
- NV001 (Nguyễn Văn A): pattern `cold_to_warm_yeu` (CR 0.32 vs team 0.61);
  mẫu 38 KHTN đủ kết luận. → Đề xuất handoff training.
- NV007 (Lê Văn C): mẫu nhỏ 12 KHTN — không kết luận, theo dõi tháng tới.

**Pipeline skip phát hiện:** 3 HĐ trong sales_pgs không có trong quan_tri (~10%).
→ Nhóm GP Quy trình.
```

### 8.2 Quy tắc bất biến

1. **Không xếp hạng TVBH có < 30 KHTN/kỳ** — Hook H3.
2. **Mỗi pattern phải có module training tương ứng** — bảng mục 3.3.
3. **Lost reason "khác" > 30% → file dữ liệu kém chất lượng** — yêu cầu cải tiến cách ghi nhận.
4. **Pipeline velocity là chỉ số leading** — báo trước doanh số 30-45 ngày.
5. **Phát hiện skip pipeline → không tự kỷ luật**, chỉ nêu trong báo cáo + đề xuất quy trình.
