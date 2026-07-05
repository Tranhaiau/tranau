# Reference 02 — Công thức KPIs Xưởng / KTV / CVDV

> **Khi nào load:** Sub-agent `ro-analyzer` cần tính doanh thu/RO, hiệu suất KTV, năng suất xưởng,
> capture rate. Đây là file công thức gốc — sai 1 công thức = báo cáo sai cả tháng.

---

## 1. Tầng KPI — 3 cấp

```
┌─ Cấp đại lý (xưởng) ────────┐
│  - Doanh thu xưởng           │
│  - Tổng RO                   │
│  - Capture rate              │
│  - Comeback rate             │
│  - FTF rate tổng             │
└──────────────────────────────┘
              │
┌─ Cấp KTV/CVDV (cá nhân) ────┐
│  - Doanh thu/KTV/ngày        │
│  - Số RO/KTV/ngày            │
│  - Giờ công / RO             │
│  - FTF rate cá nhân          │
│  - CSI điểm chạm cá nhân     │
└──────────────────────────────┘
              │
┌─ Cấp RO (giao dịch) ─────────┐
│  - Doanh thu/RO              │
│  - CLĐ/RO, PT/RO             │
│  - Thời gian xử lý/RO        │
└──────────────────────────────┘
```

---

## 2. Cấp đại lý

### 2.1 Doanh thu xưởng

```
Doanh thu xưởng = Σ tong_doanh_thu của RO closed trong kỳ
```

```python
import pandas as pd

def doanh_thu_xuong(ro_df, ky_start, ky_end, include_BH=False):
    df = ro_df[
        (ro_df['trang_thai_RO'] == 'closed') &
        (ro_df['ngay_dong_RO'].between(ky_start, ky_end))
    ].copy()
    if not include_BH:
        df = df[df['loai_RO'] != 'BH']  # bảo hành thường = 0 doanh thu

    tot = df['tong_doanh_thu'].sum()
    return {
        'tong_doanh_thu': tot,
        'doanh_thu_CLĐ': df['doanh_thu_CLĐ'].sum(),
        'doanh_thu_PT': df['doanh_thu_PT'].sum(),
        'doanh_thu_DS': df.get('doanh_thu_DS', pd.Series([0])).sum(),
        'tong_RO': len(df),
        'co_cau_pct': {
            'CLĐ': df['doanh_thu_CLĐ'].sum() / max(tot, 1) * 100,
            'PT': df['doanh_thu_PT'].sum() / max(tot, 1) * 100,
            'DS': df.get('doanh_thu_DS', pd.Series([0])).sum() / max(tot, 1) * 100
        }
    }
```

### 2.2 Doanh thu / RO trung bình

```
DT/RO = Tổng doanh thu / Tổng RO
PT/RO = Doanh thu PT / Tổng RO
CLĐ/RO = Doanh thu CLĐ / Tổng RO
```

**Benchmark hệ thống PGS (tham khảo, VND):**

| Loại RO | DT/RO | PT/RO | CLĐ/RO |
|---|---|---|---|
| BDĐK 1k | 800k - 1.2tr | 600k | 200k |
| BDĐK 10k | 1.5tr - 2.5tr | 1.2tr | 500k |
| BDĐK 40k | 3.5tr - 5tr | 2.8tr | 1.2tr |
| BDĐK 80k | 6tr - 9tr | 4.5tr | 2tr |
| SC cơ bản | 1.5tr - 3tr | 1tr | 1tr |
| SC phức tạp | 5tr - 15tr+ | 4tr+ | 3tr+ |
| Đồng sơn nhẹ | 3tr - 6tr | 1.5tr | 2tr |
| Đồng sơn nặng | 15tr - 60tr | 6tr | 8tr |

```python
def dt_per_ro_breakdown(ro_df, ky_start, ky_end):
    df = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
               (ro_df['ngay_dong_RO'].between(ky_start, ky_end))]
    return df.groupby('loai_RO').agg(
        n_RO=('ma_RO', 'count'),
        DT_RO=('tong_doanh_thu', 'mean'),
        PT_RO=('doanh_thu_PT', 'mean'),
        CLĐ_RO=('doanh_thu_CLĐ', 'mean')
    )
```

### 2.3 Capture Rate (UIO → vào xưởng)

```
Capture rate (12 tháng) = VIN active đã vào xưởng PGS ≥ 1 lần / Tổng VIN active × 100%
```

```python
def capture_rate(uio_df, ro_df, today, window_months=12):
    cutoff = pd.Timestamp(today) - pd.DateOffset(months=window_months)

    ro_window = ro_df[ro_df['ngay_mo_RO'] >= cutoff]
    vin_in_workshop = set(ro_window['vin'].dropna())

    active_uio = uio_df[uio_df['trang_thai'] == 'active']
    vin_active = set(active_uio['vin'])

    captured = vin_active & vin_in_workshop
    return {
        'capture_rate_pct': len(captured) / max(len(vin_active), 1) * 100,
        'n_uio_active': len(vin_active),
        'n_captured': len(captured),
        'n_silent': len(vin_active - vin_in_workshop)   # cho vin-recaller
    }
```

**Benchmark:**
| Capture rate | Đánh giá |
|---|---|
| < 50% | Yếu — mất KH nhiều |
| 50-65% | Trung bình |
| 65-80% | Tốt |
| > 80% | Rất tốt (top hệ thống) |

### 2.4 Comeback Rate

```
Comeback rate = RO comeback (KH quay lại < 7d cùng triệu chứng) / Tổng RO closed × 100%
```

```python
def comeback_rate(ro_df, ky_start, ky_end):
    df = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
               (ro_df['ngay_dong_RO'].between(ky_start, ky_end))]
    if 'comeback_flag' not in df.columns:
        return None
    return {
        'comeback_rate_pct': df['comeback_flag'].mean() * 100,
        'n_comeback': df['comeback_flag'].sum(),
        'n_RO_total': len(df)
    }
```

| Comeback | Đánh giá |
|---|---|
| < 3% | Rất tốt |
| 3-5% | Tốt |
| 5-8% | Cần cải thiện |
| > 8% | Nghiêm trọng — diagnose |

### 2.5 FTF Rate (First-Time Fix)

```
FTF = RO sửa đúng lần đầu (không comeback trong 14d) / Tổng RO SC closed × 100%
```

```python
def ftf_rate(ro_df, ky_start, ky_end, only_SC=True):
    df = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
               (ro_df['ngay_dong_RO'].between(ky_start, ky_end))]
    if only_SC:
        df = df[df['loai_RO'] == 'SC']
    if 'FTF_flag' not in df.columns or len(df) == 0:
        return None
    return {
        'ftf_rate_pct': df['FTF_flag'].mean() * 100,
        'n_ftf': df['FTF_flag'].sum(),
        'n_RO_SC': len(df)
    }
```

**Benchmark:** > 90% tốt; < 85% cần diagnose.

### 2.6 Hiệu suất khoang (capacity utilization)

```
Hiệu suất khoang = Σ giờ công / (Số khoang × Số ngày × Giờ làm) × 100%
```

```python
def capacity_utilization(ro_chi_tiet_df, n_khoang, ky_start, ky_end, h_per_day=8):
    df = ro_chi_tiet_df[ro_chi_tiet_df['loai'] == 'CLĐ']
    total_h = df['gio_cong'].sum()
    n_days = pd.bdate_range(ky_start, ky_end).size  # working days
    capacity_h = n_khoang * n_days * h_per_day
    return {
        'utilization_pct': total_h / max(capacity_h, 1) * 100,
        'total_h_used': total_h,
        'capacity_h': capacity_h,
        'spare_h': capacity_h - total_h
    }
```

**Benchmark:** 70-85% healthy. > 95% quá tải. < 50% thừa năng lực.

---

## 3. Cấp KTV (cá nhân)

### 3.1 KPI cá nhân tổng hợp

```python
def per_ktv_kpis(ro_df, ro_chi_tiet_df, ktv_master, ky_start, ky_end):
    closed = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
                   (ro_df['ngay_dong_RO'].between(ky_start, ky_end))]

    by_ktv = closed.groupby('ma_KTV_chinh').agg(
        n_RO=('ma_RO', 'count'),
        DT_total=('tong_doanh_thu', 'sum'),
        DT_RO=('tong_doanh_thu', 'mean'),
        PT_RO=('doanh_thu_PT', 'mean'),
        CLĐ_RO=('doanh_thu_CLĐ', 'mean'),
        ftf_rate=('FTF_flag', 'mean'),
        comeback_rate=('comeback_flag', 'mean')
    ).reset_index()

    chi_tiet_clđ = ro_chi_tiet_df[ro_chi_tiet_df['loai'] == 'CLĐ']
    gio_per_ktv = (chi_tiet_clđ.groupby('ma_KTV_thuc_hien')['gio_cong']
                   .sum().reset_index())
    gio_per_ktv.columns = ['ma_KTV_chinh', 'tong_gio_cong']

    by_ktv = by_ktv.merge(gio_per_ktv, on='ma_KTV_chinh', how='left')

    n_days = pd.bdate_range(ky_start, ky_end).size
    by_ktv['DT_per_day'] = by_ktv['DT_total'] / n_days
    by_ktv['n_RO_per_day'] = by_ktv['n_RO'] / n_days
    by_ktv['gio_per_RO'] = by_ktv['tong_gio_cong'] / by_ktv['n_RO']

    by_ktv = by_ktv.merge(
        ktv_master[['ma_KTV', 'ten', 'level', 'target_RO_ngay']],
        left_on='ma_KTV_chinh', right_on='ma_KTV', how='left'
    )
    by_ktv['pct_dat_target'] = by_ktv['n_RO_per_day'] / by_ktv['target_RO_ngay'] * 100
    return by_ktv
```

### 3.2 Diagnose pattern KTV yếu

```python
def diagnose_ktv(per_ktv_df, team_avg, threshold=0.7):
    diagnoses = []
    for _, row in per_ktv_df.iterrows():
        if row['n_RO'] < 30:
            diagnoses.append({
                'ma_KTV': row['ma_KTV_chinh'],
                'pattern': 'sample_too_small',
                'note': f"Mẫu {row['n_RO']} RO — chưa đủ kết luận (Hook H7)"
            })
            continue

        weak = []
        if row['ftf_rate'] < team_avg['ftf_rate'] * threshold:
            weak.append('FTF_yeu')
        if row['comeback_rate'] > team_avg['comeback_rate'] * (2 - threshold):
            weak.append('comeback_cao')
        if row['gio_per_RO'] > team_avg['gio_per_RO'] * (2 - threshold):
            weak.append('cham')
        if row['DT_RO'] < team_avg['DT_RO'] * threshold:
            weak.append('DT_RO_thap')

        if not weak:
            pattern = 'on_track'
        elif 'FTF_yeu' in weak and 'comeback_cao' in weak:
            pattern = 'chat_luong_kem'  # nghiêm trọng nhất
        elif 'FTF_yeu' in weak:
            pattern = 'ky_thuat_chua_chuan'
        elif 'cham' in weak and 'DT_RO_thap' in weak:
            pattern = 'cham_va_thap'
        elif 'cham' in weak:
            pattern = 'thoi_gian_cham'
        else:
            pattern = ','.join(weak)

        diagnoses.append({
            'ma_KTV': row['ma_KTV_chinh'],
            'pattern': pattern,
            'weak_metrics': weak,
            'kpi_vs_team': {
                'ftf_ratio': row['ftf_rate'] / max(team_avg['ftf_rate'], 0.01),
                'comeback_ratio': row['comeback_rate'] / max(team_avg['comeback_rate'], 0.01),
                'speed_ratio': row['gio_per_RO'] / max(team_avg['gio_per_RO'], 0.01)
            }
        })
    return pd.DataFrame(diagnoses)
```

### 3.3 Pattern → Module training (cho handoff Layer 5)

```python
PATTERN_TO_TRAINING_KTV = {
    'chat_luong_kem':       ['quy_trinh_chan_doan', 'quality_check', 'sua_dung_lan_dau'],
    'ky_thuat_chua_chuan':  ['quy_trinh_chan_doan', 'sua_dung_lan_dau'],
    'cham_va_thap':         ['quy_trinh_lam_viec', 'thoi_gian_chuan_BDĐK'],
    'thoi_gian_cham':       ['thoi_gian_chuan_BDĐK', 'su_dung_dung_cu'],
    'comeback_cao':         ['kiem_tra_truoc_ban_giao', 'quality_check'],
    'on_track':             []
}
```

→ `ro-analyzer` xuất `suggested_handoff` với module này; main quyết định gửi sang `pgs-training-management`.

---

## 4. Cấp CVDV

### 4.1 KPI CVDV

```python
def per_cvdv_kpis(ro_df, csi_df, hen_df, cvdv_master, ky_start, ky_end):
    closed = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
                   (ro_df['ngay_dong_RO'].between(ky_start, ky_end))]

    by_cvdv = closed.groupby('ma_CVDV').agg(
        n_RO=('ma_RO', 'count'),
        DT_RO=('tong_doanh_thu', 'mean'),
        PT_RO=('doanh_thu_PT', 'mean')   # CVDV chốt PT → upsell
    ).reset_index()

    csi_window = csi_df[csi_df['ngay_khao_sat'].between(ky_start, ky_end)]
    csi_per_cvdv = csi_window.groupby('ma_CVDV').agg(
        csi_mean=('diem_tong', 'mean'),
        csi_don_tiep=('diem_don_tiep', 'mean'),
        csi_tu_van=('diem_tu_van', 'mean'),
        n_phieu=('phieu_id', 'count')
    ).reset_index()

    if hen_df is not None and len(hen_df):
        hen_window = hen_df[hen_df['ngay_hen'].between(ky_start, ky_end)]
        hen_per_cvdv = hen_window.groupby('ma_CVDV_phu_trach').agg(
            n_hen=('ma_hen', 'count'),
            n_da_den=('trang_thai_hen', lambda x: (x == 'đa_den').sum())
        )
        hen_per_cvdv['ty_le_đa_den'] = hen_per_cvdv['n_da_den'] / hen_per_cvdv['n_hen']
        hen_per_cvdv = (hen_per_cvdv.reset_index()
                        .rename(columns={'ma_CVDV_phu_trach': 'ma_CVDV'}))
        by_cvdv = by_cvdv.merge(hen_per_cvdv, on='ma_CVDV', how='left')

    return by_cvdv.merge(csi_per_cvdv, on='ma_CVDV', how='left')
```

### 4.2 KPI CVDV "upsell"

```
Upsell ratio = PT/RO của CVDV / PT/RO TB team
```

> CVDV giỏi: PT/RO cao **và** CSI không bị giảm → upsell hợp lý, không "ép".

```python
def cvdv_upsell_quality(per_cvdv_df, team_avg):
    rows = []
    for _, r in per_cvdv_df.iterrows():
        if r['n_RO'] < 30:
            verdict = 'sample_too_small'
        else:
            upsell_ratio = r['PT_RO'] / max(team_avg['PT_RO'], 1)
            csi_drop = r['csi_mean'] < team_avg['csi_mean'] * 0.95

            if upsell_ratio >= 1.10 and not csi_drop:
                verdict = 'upsell_chat_luong'  # giỏi
            elif upsell_ratio >= 1.10 and csi_drop:
                verdict = 'upsell_ep_KH'  # cảnh báo
            elif upsell_ratio < 0.85:
                verdict = 'upsell_yeu'
            else:
                verdict = 'on_track'

        rows.append({**r.to_dict(), 'verdict': verdict})
    return pd.DataFrame(rows)
```

### 4.3 Pattern CVDV → Module training

```python
PATTERN_TO_TRAINING_CVDV = {
    'upsell_yeu':       ['ky_nang_tu_van_phu_tung', 'phan_tich_lich_su_xe'],
    'upsell_ep_KH':     ['ky_nang_giao_tiep_KH', 'dao_duc_nghe_nghiep'],
    'csi_thap':         ['xu_ly_phan_nan', 'don_tiep_chuyen_nghiep'],
    'on_track':         []
}
```

---

## 5. Time-series KPI (theo dõi xu hướng)

### 5.1 Tính KPI theo tuần

```python
def weekly_kpis(ro_df, ky_start, ky_end):
    df = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
               (ro_df['ngay_dong_RO'].between(ky_start, ky_end))].copy()
    df['week'] = df['ngay_dong_RO'].dt.to_period('W-MON')
    return df.groupby('week').agg(
        n_RO=('ma_RO', 'count'),
        DT_total=('tong_doanh_thu', 'sum'),
        DT_RO=('tong_doanh_thu', 'mean'),
        ftf_rate=('FTF_flag', 'mean'),
        comeback_rate=('comeback_flag', 'mean')
    )
```

### 5.2 Phát hiện xu hướng giảm

```python
def detect_declining_trend(weekly_df, kpi='DT_RO', n_weeks=4):
    """
    Cảnh báo nếu KPI giảm liên tục n_weeks tuần.
    """
    series = weekly_df[kpi].tail(n_weeks)
    if len(series) < n_weeks:
        return None
    is_declining = all(series.iloc[i] > series.iloc[i+1]
                       for i in range(len(series)-1))
    if is_declining:
        return {
            'kpi': kpi,
            'verdict': 'declining',
            'series': series.tolist(),
            'pct_drop_total': (series.iloc[0] - series.iloc[-1]) / series.iloc[0] * 100
        }
    return None
```

---

## 6. Sanity check tổng (Hook H4)

```python
def assert_workshop_kpis_valid(kpis):
    assert 0 <= kpis['capture_rate_pct'] <= 100, 'Capture rate out of range'
    assert 0 <= kpis['ftf_rate_pct'] <= 100, 'FTF out of range'
    assert 0 <= kpis['comeback_rate_pct'] <= 100, 'Comeback out of range'
    assert kpis['tong_doanh_thu'] >= 0, 'DT âm'

    # Tỉ trọng cộng = 100%
    pct_sum = sum(kpis['co_cau_pct'].values())
    assert abs(pct_sum - 100) < 0.5, f'Cơ cấu DT không = 100%: {pct_sum}'
```

---

## 7. Quy tắc trình bày KPI trong báo cáo

```markdown
## 3. KPI Xưởng (kỳ T4/2026, n=842 RO closed)

**Cấp đại lý:**
| KPI | Giá trị | vs T3 | vs benchmark |
|---|---|---|---|
| Tổng doanh thu | 4.85 tỷ | +12% MoM | — |
| Tổng RO | 842 | +8% | — |
| DT/RO TB | 5.76tr | +4% | trên BM (5.0tr) |
| Capture rate | 72% | +3 điểm % | tốt (BM 65-80%) |
| Comeback rate | 4.2% | -0.3 điểm % | tốt (BM <5%) |
| FTF rate | 91.5% | +1.2 điểm % | tốt (BM >90%) |
| Hiệu suất khoang | 78% | +5 điểm % | healthy (BM 70-85%) |

**Cơ cấu doanh thu:** CLĐ 28% — PT 58% — ĐS 14%.

**KTV cần chú ý:** (mẫu ≥ 30 RO)
- KTV001 (Phạm Văn A, L3): pattern `chat_luong_kem` — FTF 0.71 vs team 0.92,
  comeback 11% vs team 4%. → handoff training quy_trinh_chan_doan + quality_check.
- KTV007 (Lê Văn C, L2): pattern `cham_va_thap` — gio/RO 5.2h vs team 3.1h.
  → handoff training thoi_gian_chuan_BDĐK.

**CVDV cần chú ý:**
- CVDV004 verdict `upsell_ep_KH` — PT/RO 1.45× team nhưng CSI thấp 4.05 vs team 4.42.
  → handoff training ky_nang_giao_tiep_KH.
```

---

## 8. Quy tắc bất biến

1. **Không xếp hạng cá nhân với mẫu < 30 RO/kỳ** — Hook H7.
2. **Tỉ trọng CLĐ + PT + ĐS phải = 100%** — Hook H4 sanity.
3. **Capture rate dùng window 12 tháng cố định** — không thay đổi window giữa các kỳ.
4. **Comeback định nghĩa "cùng triệu chứng < 7d"** — không nới lỏng định nghĩa.
5. **FTF chỉ tính trên RO loại SC** — BDĐK/BH không tính FTF.
6. **Mỗi pattern KPI yếu phải có module training tương ứng** — bảng mục 3.3 và 4.3.
7. **KPI dùng RO closed, không dùng RO open** — open RO không có dữ liệu hoàn chỉnh.

---

## 9. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| RO open carryover từ tháng trước → đóng tháng này | Tính vào doanh thu tháng đóng (theo `ngay_dong_RO`) |
| 1 RO có 2-3 KTV | Header KTV chính cho diagnose; ro_chi_tiet cho giờ công cá nhân |
| KTV chuyên đồng sơn | Tính riêng nhóm "DS only KTV", không gộp với SC |
| RO bảo hành (BH) | Loại khỏi DT/RO; tính riêng `n_RO_BH`, `gio_cong_BH` |
| RO cancelled | Loại khỏi mọi KPI |
| KTV mới (< 3 tháng) | Đánh dấu "trainee", không xếp pattern, mở `pgs-training-management` cho onboarding |
| Capture rate giảm đột biến | Verify có UIO mới import vào (làm tăng mẫu số) chưa kịp vào xưởng |
