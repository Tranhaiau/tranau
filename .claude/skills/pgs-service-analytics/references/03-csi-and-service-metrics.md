# Reference 03 — CSI, FTF, Đặt hẹn, BDĐK Đúng hạn

> **Khi nào load:** Sub-agent `csi-diagnoser` cần phân tích phản hồi KH;
> hoặc khi user hỏi "CSI giảm vì sao", "Tỷ lệ no-show cao", "BDĐK không đúng hạn".

---

## 1. CSI — Customer Satisfaction Index

### 1.1 Định nghĩa

CSI = chỉ số hài lòng KH sau RO, đo qua khảo sát tự động (SMS/Zalo/email/phone) sau 3-7 ngày.

**Thang đo:**
- 1-5 (5 = rất hài lòng) — phổ biến hơn ở PGS.
- Hoặc 0-100 (100 = tuyệt đối) — chuẩn JD Power.

→ **Quy tắc:** Mỗi đại lý phải chọn 1 thang và giữ cố định. Đổi thang giữa kỳ → mất so sánh.

### 1.2 6 điểm chạm CSI chuẩn

| Điểm chạm | Câu hỏi mẫu |
|---|---|
| **Đón tiếp** (`diem_don_tiep`) | "Anh/chị có hài lòng với cách đón tiếp khi đến xưởng?" |
| **Tư vấn** (`diem_tu_van`) | "CVDV có giải thích rõ ràng vấn đề và chi phí?" |
| **Thời gian chờ** (`diem_thoi_gian_cho`) | "Thời gian xử lý có đúng cam kết?" |
| **Chất lượng sửa** (`diem_chat_luong_sua`) | "Xe sau sửa có hoạt động tốt như mong đợi?" |
| **Giao xe lại** (`diem_giao_xe_lai`) | "Việc bàn giao xe có chuyên nghiệp?" |
| **Giá phải chăng** (`diem_gia_phai_chang`) | "Mức giá có hợp lý so với dịch vụ nhận được?" |

### 1.3 Tính CSI tổng

```python
import pandas as pd
import numpy as np

def csi_aggregate(csi_df, ky_start, ky_end, scale='1-5'):
    """
    Tính CSI tổng + theo điểm chạm trong kỳ.
    """
    df = csi_df[csi_df['ngay_khao_sat'].between(ky_start, ky_end)].copy()
    if len(df) == 0:
        return {'warning': 'Không có phản hồi CSI trong kỳ'}

    diem_chams = ['diem_don_tiep', 'diem_tu_van', 'diem_thoi_gian_cho',
                  'diem_chat_luong_sua', 'diem_giao_xe_lai', 'diem_gia_phai_chang']

    out = {
        'n_phieu': len(df),
        'csi_tong_TB': df['diem_tong'].mean(),
        'csi_tong_median': df['diem_tong'].median(),
        'csi_per_touch': {dc: df[dc].mean() for dc in diem_chams if dc in df.columns},
        'tỷ_lệ_promoter_pct': calc_promoter_rate(df, scale),
        'tỷ_lệ_detractor_pct': calc_detractor_rate(df, scale),
        'nps': calc_nps(df) if 'nps' in df.columns else None
    }
    return out

def calc_promoter_rate(df, scale='1-5'):
    """KH cho điểm cao nhất/cao."""
    if scale == '1-5':
        threshold = 5
    else:  # 0-100
        threshold = 90
    return (df['diem_tong'] >= threshold).mean() * 100

def calc_detractor_rate(df, scale='1-5'):
    """KH cho điểm thấp."""
    if scale == '1-5':
        threshold = 3   # ≤ 3 = detractor
    else:
        threshold = 70
    return (df['diem_tong'] <= threshold).mean() * 100

def calc_nps(df):
    """NPS = % promoter - % detractor (chuẩn -100 → +100)."""
    if 'nps_response' not in df.columns:
        # Tự tính từ diem_tong (1-5 scale)
        promoter = (df['diem_tong'] == 5).mean()
        detractor = (df['diem_tong'] <= 3).mean()
        return (promoter - detractor) * 100
    return df['nps_response'].mean()
```

### 1.4 Benchmark CSI

| Thang 1-5 | Đánh giá | Thang 0-100 | NPS |
|---|---|---|---|
| ≥ 4.7 | Rất tốt | ≥ 92 | > +50 |
| 4.4-4.7 | Tốt | 85-92 | +20 → +50 |
| 4.0-4.4 | Trung bình | 75-85 | 0 → +20 |
| < 4.0 | Yếu | < 75 | < 0 |

### 1.5 Phát hiện điểm chạm yếu

```python
def find_weak_touchpoints(csi_df, threshold_drop=0.3):
    """
    Tìm điểm chạm có điểm thấp hơn TB tổng > 0.3 (thang 1-5).
    """
    diem_chams = ['diem_don_tiep', 'diem_tu_van', 'diem_thoi_gian_cho',
                  'diem_chat_luong_sua', 'diem_giao_xe_lai', 'diem_gia_phai_chang']

    csi_avg = csi_df['diem_tong'].mean()
    weak = []
    for dc in diem_chams:
        if dc not in csi_df.columns:
            continue
        dc_avg = csi_df[dc].mean()
        if csi_avg - dc_avg > threshold_drop:
            weak.append({
                'touchpoint': dc,
                'avg': dc_avg,
                'csi_overall': csi_avg,
                'gap': csi_avg - dc_avg,
                'verdict': 'điểm chạm này kéo CSI tổng xuống'
            })
    return sorted(weak, key=lambda x: -x['gap'])
```

### 1.6 Phân tích phản hồi text

```python
def analyze_text_feedback(csi_df, n_keywords=10):
    """
    Đếm từ khoá trong phản hồi text (paraphrase, không trích nguyên).
    """
    if 'phan_hoi_text' not in csi_df.columns:
        return None

    # Stopwords Vietnamese cơ bản
    STOPWORDS = {'và', 'là', 'của', 'có', 'không', 'một', 'các', 'được',
                 'với', 'cho', 'tại', 'này', 'đã', 'sẽ', 'rất', 'nhưng',
                 'tôi', 'mình', 'chúng', 'thì'}

    # Negative keywords (cần action)
    NEGATIVE_KW = ['chậm', 'lâu', 'đắt', 'giá cao', 'không hài', 'tệ',
                   'hư', 'lỗi', 'sửa lại', 'comeback', 'thái độ',
                   'khó chịu', 'phàn nàn', 'không giải thích']

    text_concat = ' '.join(csi_df['phan_hoi_text'].dropna().astype(str)).lower()

    keyword_counts = {}
    for kw in NEGATIVE_KW:
        keyword_counts[kw] = text_concat.count(kw)

    top_negative = sorted(keyword_counts.items(), key=lambda x: -x[1])[:n_keywords]
    return {
        'n_phan_hoi_co_text': csi_df['phan_hoi_text'].notna().sum(),
        'top_keywords_tieu_cuc': top_negative
    }
```

### 1.7 Quy tắc paraphrase phản hồi text

Khi trích phản hồi vào báo cáo:
- **Tối đa 15 từ liên tiếp nguyên văn**.
- **Không nêu danh tính KH** (kể cả khi file có `ten_KH`).
- Tốt hơn: paraphrase + gắn `ma_RO` để truy vết.
- Nhóm các phản hồi tương tự thành theme thay vì trích từng dòng.

---

## 2. FTF — First-Time Fix (chi tiết)

### 2.1 Định nghĩa

FTF = sửa đúng ngay lần đầu, **không** phải comeback trong 14 ngày kế tiếp với cùng triệu chứng.

### 2.2 Phân biệt FTF vs Comeback

| Tình huống | FTF? | Comeback? |
|---|---|---|
| KH quay lại sau 30d cho BDĐK định kỳ tiếp theo | ✓ FTF | ✗ Không |
| KH quay lại sau 5d cho **triệu chứng khác** | ✓ FTF | ✗ Không |
| KH quay lại sau 5d **cùng triệu chứng** | ✗ Fail FTF | ✓ Comeback |
| KH gọi phàn nàn nhưng không đến lại | Có thể fail FTF | Tùy hệ thống ghi nhận |

### 2.3 FTF theo nguyên nhân fail

```python
def ftf_failure_analysis(ro_df, ky_start, ky_end):
    """
    Phân tích lý do KTV fail FTF (cần cột ly_do_comeback).
    """
    df = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
               (ro_df['comeback_flag'] == True) &
               (ro_df['ngay_dong_RO'].between(ky_start, ky_end))]

    if 'ly_do_comeback' not in df.columns:
        return None

    return df['ly_do_comeback'].value_counts(normalize=True).to_dict()

# Lý do thường gặp:
# - chan_doan_sai: chẩn đoán sai bệnh
# - sua_chua_chua_du: sửa nhưng chưa hết
# - phu_tung_kem_chat_luong: phụ tùng lỗi
# - lap_dat_sai: lắp đặt không đúng kỹ thuật
# - khong_kiem_tra_truoc_ban_giao: bỏ qua quality check
```

### 2.4 Mapping fail FTF → Module training

```python
FTF_FAIL_TO_TRAINING = {
    'chan_doan_sai':                 ['quy_trinh_chan_doan', 'su_dung_OBD'],
    'sua_chua_chua_du':              ['quy_trinh_lam_viec', 'check_list_sua_chua'],
    'phu_tung_kem_chat_luong':       [],  # không phải lỗi KTV — handoff supply chain
    'lap_dat_sai':                   ['ky_thuat_lap_dat', 'mo_men_xoan_chuan'],
    'khong_kiem_tra_truoc_ban_giao': ['quality_check', 'check_list_ban_giao']
}
```

---

## 3. Đặt hẹn (Appointment)

### 3.1 Tỷ lệ đặt hẹn / Walk-in

```
Tỷ lệ hẹn trước = RO có nguon=hen_truoc / Tổng RO
```

```python
def appointment_rate(ro_df, ky_start, ky_end):
    df = ro_df[(ro_df['trang_thai_RO'] == 'closed') &
               (ro_df['ngay_dong_RO'].between(ky_start, ky_end))]
    by_nguon = df['nguon_RO'].value_counts(normalize=True) * 100
    return by_nguon.to_dict()
```

**Benchmark:**
- Tỷ lệ hen_truoc < 40%: yếu — KH đi không có kế hoạch, khó cân tải khoang.
- 40-60%: trung bình.
- 60-80%: tốt.
- \> 80%: rất tốt — capacity planning hiệu quả.

### 3.2 No-show rate

```
No-show rate = Hẹn bị KH không đến / Tổng hẹn confirmed
```

```python
def no_show_rate(hen_df, ky_start, ky_end):
    df = hen_df[hen_df['ngay_hen'].between(ky_start, ky_end)]
    df_past = df[df['ngay_hen'] < pd.Timestamp.now()]   # chỉ tính hẹn đã qua

    n_total = len(df_past[df_past['trang_thai_hen'].isin(['confirmed', 'no_show', 'đa_den'])])
    n_no_show = (df_past['trang_thai_hen'] == 'no_show').sum()

    return {
        'no_show_rate_pct': n_no_show / max(n_total, 1) * 100,
        'n_no_show': n_no_show,
        'n_total_hen': n_total
    }
```

**Benchmark:**
| No-show | Đánh giá |
|---|---|
| < 10% | Tốt |
| 10-20% | Trung bình |
| > 20% | Yếu — cần cải thiện nhắc hẹn (Zalo OA, SMS T-1, T-2h) |

### 3.3 Phân tích no-show theo kênh đặt

```python
def no_show_by_channel(hen_df, ky_start, ky_end):
    df = hen_df[(hen_df['ngay_hen'].between(ky_start, ky_end)) &
                (hen_df['ngay_hen'] < pd.Timestamp.now())]
    grouped = df.groupby('kenh_dat')['trang_thai_hen'].apply(
        lambda x: (x == 'no_show').mean() * 100
    )
    return grouped.sort_values(ascending=False)

# Insight thường gặp:
# - web tự đặt: no-show cao nhất (KH "nghịch" form)
# - cvdv chủ động gọi: thấp nhất (đã verify cam kết)
# - zalo: trung bình
# → Action: web booking yêu cầu xác nhận lại qua Zalo trong 2h.
```

---

## 4. BDĐK Đúng hạn

### 4.1 Định nghĩa

BDĐK = bảo dưỡng định kỳ. Mỗi mốc km (1k, 5k, 10k, 20k...) có cửa sổ "đúng hạn"
(thường ±10% km hoặc ±30 ngày).

```
BDĐK đúng hạn = VIN đến BDĐK trong cửa sổ ±10% km hoặc ±30 ngày so với mốc dự kiến
```

### 4.2 Tính tỷ lệ BDĐK đúng hạn

```python
def bdđk_on_time_rate(uio_df, ro_df, ky_start, ky_end):
    """
    Trong số VIN đến BDĐK trong kỳ, bao nhiêu % đúng hạn.
    """
    bdđk_ro = ro_df[(ro_df['loai_RO'] == 'BDĐK') &
                     (ro_df['trang_thai_RO'] == 'closed') &
                     (ro_df['ngay_dong_RO'].between(ky_start, ky_end))]

    # Cần cột km_dung_han trong ro hoặc tính từ uio
    if 'mac_km_BDĐK' not in bdđk_ro.columns:
        return None

    # Đúng hạn: |km thực - mốc dự kiến| <= 10% mốc
    bdđk_ro['gap_km_pct'] = abs(bdđk_ro['km_xe_vao'] - bdđk_ro['mac_km_BDĐK']) / \
                             bdđk_ro['mac_km_BDĐK']
    bdđk_ro['on_time'] = bdđk_ro['gap_km_pct'] <= 0.10

    return {
        'on_time_rate_pct': bdđk_ro['on_time'].mean() * 100,
        'n_BDĐK': len(bdđk_ro),
        'n_on_time': bdđk_ro['on_time'].sum(),
        'avg_gap_km_pct': bdđk_ro['gap_km_pct'].mean() * 100
    }
```

### 4.3 BDĐK 1k (lần đầu sau giao xe)

BDĐK 1k đặc biệt quan trọng — là điểm bắt đầu thiết lập mối quan hệ hậu mãi.

```
Tỷ lệ BDĐK 1k đúng hạn = VIN đã giao đến BDĐK 1k trong cửa sổ / VIN đã giao đủ 30d
```

```python
def bdđk_1k_rate(uio_df, ro_df, today):
    """
    Tỷ lệ KH mới đến làm BDĐK 1k đúng hạn.
    """
    cutoff = pd.Timestamp(today) - pd.Timedelta(days=30)

    # VIN giao trong vòng 30d-90d trước
    eligible = uio_df[
        (uio_df['ngay_ban'] <= cutoff) &
        (uio_df['ngay_ban'] >= cutoff - pd.Timedelta(days=60))
    ]

    bdđk_1k = ro_df[(ro_df['loai_RO'] == 'BDĐK') &
                     (ro_df['km_xe_vao'] <= 1500)]   # gần 1k km
    vin_da_BDĐK_1k = set(bdđk_1k['vin'])

    eligible['da_BDĐK_1k'] = eligible['vin'].isin(vin_da_BDĐK_1k)
    return {
        'rate_pct': eligible['da_BDĐK_1k'].mean() * 100,
        'n_eligible': len(eligible),
        'n_done': eligible['da_BDĐK_1k'].sum()
    }
```

**Benchmark:**
| BDĐK 1k đúng hạn | Đánh giá |
|---|---|
| > 90% | Rất tốt — sales bàn giao tốt + service hậu mãi tốt |
| 75-90% | Tốt |
| 60-75% | Trung bình |
| < 60% | Yếu — KH chuyển xưởng khác hoặc bị bỏ rơi |

### 4.4 Tìm VIN sắp đến BDĐK (nhắc nhở chủ động)

```python
def find_due_bdđk(uio_df, ro_df, today, lookahead_days=30):
    """
    Trả về danh sách VIN sắp đến BDĐK trong N ngày tới.
    Dùng cho CVDV gọi nhắc.
    """
    today_ts = pd.Timestamp(today)

    # Lấy lần BDĐK gần nhất của từng VIN
    last_bdđk = (ro_df[ro_df['loai_RO'] == 'BDĐK']
                 .sort_values('ngay_dong_RO').drop_duplicates('vin', keep='last')
                 [['vin', 'ngay_dong_RO', 'km_xe_vao']])
    last_bdđk.columns = ['vin', 'last_BDĐK_date', 'last_BDĐK_km']

    merged = uio_df.merge(last_bdđk, on='vin', how='left')

    # BDĐK kế tiếp: 6 tháng sau lần cuối hoặc +5000km (chọn cái đến trước)
    merged['next_due_date'] = merged['last_BDĐK_date'] + pd.Timedelta(days=180)

    due_window = merged[
        (merged['trang_thai'] == 'active') &
        (merged['next_due_date'].between(today_ts, today_ts + pd.Timedelta(days=lookahead_days)))
    ]

    return due_window[['vin', 'sdt_KH', 'model', 'last_BDĐK_date', 'next_due_date']]
```

→ Sub-agent `vin-recaller` dùng list này để xuất file template gọi nhắc.

---

## 5. Cross-analysis: CSI × KPI

### 5.1 CSI thấp có pattern nào không?

```python
def csi_correlation(csi_df, ro_df, ky_start, ky_end):
    """
    Cross-link CSI với loại RO, KTV, CVDV để tìm pattern.
    """
    csi_window = csi_df[csi_df['ngay_khao_sat'].between(ky_start, ky_end)]
    ro_window = ro_df[ro_df['ngay_dong_RO'].between(ky_start, ky_end)]

    merged = csi_window.merge(
        ro_window[['ma_RO', 'loai_RO', 'tong_doanh_thu', 'comeback_flag', 'gio_per_RO']],
        on='ma_RO', how='left'
    )

    # CSI theo loại RO
    csi_by_loai = merged.groupby('loai_RO')['diem_tong'].agg(['mean', 'count'])

    # CSI theo có comeback hay không
    csi_by_comeback = merged.groupby('comeback_flag')['diem_tong'].mean()

    # Correlation: thời gian xử lý vs CSI
    if 'gio_per_RO' in merged.columns:
        corr_time = merged[['gio_per_RO', 'diem_tong']].corr().iloc[0, 1]
    else:
        corr_time = None

    return {
        'csi_by_loai_RO': csi_by_loai.to_dict(),
        'csi_co_comeback': csi_by_comeback.to_dict(),
        'corr_thoi_gian_vs_csi': corr_time
    }
```

### 5.2 CSI giảm bất thường — chain of investigation

```
Step 1: CSI tổng giảm → tìm điểm chạm yếu (find_weak_touchpoints)
Step 2: Điểm chạm 'thoi_gian_cho' yếu → check capacity_utilization > 95%? KTV nào chậm nhất?
Step 3: Điểm chạm 'chat_luong_sua' yếu → check FTF/comeback theo KTV
Step 4: Điểm chạm 'gia' yếu → check upsell_quality của CVDV
Step 5: Điểm chạm 'don_tiep' yếu → check CVDV nào CSI thấp
```

---

## 6. Tổng hợp cho báo cáo

```markdown
## 4. CSI & Service Metrics (kỳ T4/2026)

**CSI tổng:** 4.42/5 (n=247 phản hồi). MoM -0.08, vs benchmark "Tốt" (4.4-4.7).

**Điểm chạm yếu:**
1. `diem_thoi_gian_cho`: 4.05 (gap 0.37 vs CSI tổng) — KH phản ánh chờ lâu.
2. `diem_gia_phai_chang`: 4.18 (gap 0.24).

**Top 3 từ khoá tiêu cực trong phản hồi text:**
- "chậm" (28 lần)
- "lâu" (22 lần)
- "giá cao" (15 lần)

**FTF rate:** 91.5%. Lý do fail (n=18 RO comeback): chẩn đoán sai 38%, sửa chưa đủ 27%, lắp đặt sai 22%.

**Đặt hẹn:**
- Tỷ lệ hẹn trước: 52% (vs benchmark "Tốt" >60%) — cần đẩy mạnh đặt hẹn.
- No-show rate: 18% — cao, kênh `web` no-show 32% > kênh `cvdv_chu_dong` 6%.

**BDĐK đúng hạn:**
- BDĐK định kỳ tổng: 78% đúng hạn (n=125 RO BDĐK).
- BDĐK 1k: 82% đúng hạn (n=22 VIN đủ điều kiện) — tốt.

**Handoff đề xuất sang Training:**
- Module `quy_trinh_chan_doan` cho KTV001, KTV007.
- Module `quality_check` cho cả tổ KTV (FTF fail nhiều do "lắp đặt sai").
```

---

## 7. Quy tắc bất biến

1. **Chỉ phân tích CSI khi mẫu ≥ 30 phiếu/kỳ** — Hook H7.
2. **Phản hồi text trích ≤ 15 từ liên tiếp + paraphrase** — Hook H8.
3. **Không nêu danh tính KH trong báo cáo** — privacy.
4. **No-show rate tách theo kênh đặt** — không gộp 1 con số tổng.
5. **BDĐK đúng hạn tách BDĐK 1k riêng** — vì mức độ quan trọng khác.
6. **CSI giảm > 0.3 thang 1-5 → escalate** — không "lờ đi".
7. **Phân tích CSI luôn cross-link với KTV/CVDV/loại RO** — không CSI suông.

---

## 8. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| KH cho 5/5 mọi điểm chạm nhưng text "tệ" | Giữ điểm + flag để CVDV xác nhận; có thể KH nhầm |
| Phản hồi text chứa thông tin nhận dạng | Paraphrase + che thông tin riêng tư |
| CSI 1 phiếu cực thấp kéo TB xuống nhiều | Xét median bên cạnh mean; flag outlier |
| Phiếu CSI gửi 7+ ngày sau RO mà KH mới phản hồi | Vẫn tính, ghi rõ "delayed response" |
| KH từ chối khảo sát | Loại khỏi mẫu, không tính như "0 điểm" |
| BDĐK trễ hạn do hãng triệu hồi (recall) | Loại khỏi tỷ lệ đúng hạn |
| CSI khi RO bảo hành | Tính riêng, không gộp với SC trả phí |
