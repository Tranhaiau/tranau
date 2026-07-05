# Reference 05 — Chu kỳ Review (7 / 14 / 30 / 60 ngày) cho GP Xưởng

> **Khi nào load:** Hook H6 đến hạn tạo scheduled review xưởng; hoặc khi user hỏi
> "Review GP tuần trước", "GP TH-K01 đã hiệu quả chưa".

---

## 1. Triết lý chu kỳ review xưởng

Khác với Sales (cycle 7/30/90), Service có **cycle 7/14/30/60** vì:
- KPI xưởng (FTF, comeback) cần thời gian quan sát ngắn hơn để verify.
- KH quay lại xưởng theo chu kỳ ngắn (BDĐK 6 tháng, không phải mua xe vài năm).
- Comeback rate đo trong 7-14 ngày → review T+14 đã có dữ liệu.

```
T0 (xuất GP) ── T+7 (kick-off) ── T+14 (mid) ── T+30 (đo KPI) ── T+60 (sustained)
                ↓                  ↓             ↓                ↓
            "Đã start             "Pattern       "KPI có          "Bền vững
             chưa?"               còn không?"    cải thiện?"      sau 60d?"
```

| Chu kỳ | Hỏi gì | Hành động |
|---|---|---|
| **T+7** | Đã start? Có blocker? | Unblock, điều chỉnh nhỏ |
| **T+14** | Pattern còn xuất hiện không? | Verify hướng đúng / sai |
| **T+30** | KPI có cải thiện theo target? | Giữ / Điều chỉnh / Dừng |
| **T+60** | Sustained sau 60d? | Đóng GP / Mở rộng / Pivot |

---

## 2. Review T+7 (Kick-off)

### 2.1 Mục đích

Đảm bảo GP **đã được giao và bắt đầu** — không bị trôi.

### 2.2 Checklist

```yaml
T+7 Service Checklist:
  - GP đã được giao cho chủ thể chưa? (meeting kick-off?)
  - Chủ thể có hiểu KPI mục tiêu không?
  - Resource đầy đủ chưa? (PT, dụng cụ, ngân sách KM, slot training)
  - Blocker?
    * Chờ training schedule
    * Chờ duyệt ngân sách KM
    * Thiếu KTV thay thế khi 1 KTV đi training
  - Tiến độ baseline: 0 / <30% / 30-70% / >70%
```

### 2.3 Code prompt cho scheduled task T+7

```python
def gen_T7_review_prompt_service(gp):
    return f"""
Review T+7 cho GP Xưởng: {gp['ma_GP']}
Vấn đề: {gp['van_de']}
Giải pháp: {gp['giai_phap']}
Chủ thể: {gp['chu_the']}
KPI mục tiêu: {gp['kpi']}
Hạn: {gp['han']}

Hôm nay {gp['ngay_review_T7']}, T+7 ngày từ khi xuất GP.

Câu hỏi:
1. GP đã chính thức bắt đầu chưa? (meeting kick-off, phân công, ngân sách approve?)
2. Blocker nào đang ngăn cản? Liệt kê cụ thể.
3. Estimate % hoàn thành.
4. Có cần điều chỉnh trong tuần tới không?

Riêng GP về training: KTV/CVDV đã đăng ký lịch học chưa? Có ai chưa book được slot?

Nếu T+7 chưa bắt đầu → escalate Trưởng phòng dịch vụ + ghi vào Action Plan sheet.
"""
```

### 2.4 Diễn giải kết quả T+7

| % hoàn thành | Diễn giải | Action |
|---|---|---|
| 0% | Chưa bắt đầu | ⚠️ Cờ đỏ, escalate |
| 1-30% | Mới khởi động | OK, theo dõi |
| 30-70% | Đúng tiến độ | Tiếp tục |
| > 70% | Vượt tiến độ | Có thể đóng sớm hoặc mở rộng |

---

## 3. Review T+14 (Mid)

### 3.1 Mục đích đặc biệt cho Service

T+14 quan trọng cho GP về chất lượng kỹ thuật vì:
- Comeback định nghĩa "trong 7-14 ngày" → sau T+14 có số liệu sơ bộ.
- KTV đã thực hiện đủ ≥ 10 RO mới sau training → đo lường được.

### 3.2 Code

```python
def review_T14_service(gp, ro_data_after_T0):
    """
    Đo KPI sơ bộ sau 14 ngày — xem hướng có đúng không.
    """
    df_after = ro_data_after_T0[
        ro_data_after_T0['ngay_dong_RO'] >= gp['ngay_xuat']
    ]

    if len(df_after) < 10:
        return {'verdict': 'mau_chua_du', 'n_RO_moi': len(df_after),
                'note': 'Đợi T+30 đánh giá'}

    # Nếu là GP về KTV cụ thể
    if 'ma_KTV_target' in gp:
        ktv_data = df_after[df_after['ma_KTV_chinh'] == gp['ma_KTV_target']]
        if len(ktv_data) < 10:
            return {'verdict': 'ktv_chua_du_mau',
                    'n_RO_KTV': len(ktv_data),
                    'note': 'KTV chưa làm đủ 10 RO mới — kéo dài cửa sổ'}

        new_ftf = ktv_data['FTF_flag'].mean()
        new_comeback = ktv_data['comeback_flag'].mean()
        baseline = gp['baseline']

        # Verdict mid:
        ftf_better = new_ftf > baseline['ftf_rate'] * 1.05
        comeback_better = new_comeback < baseline['comeback_rate'] * 0.85

        if ftf_better and comeback_better:
            return {'verdict': 'on_track', 'ftf_now': new_ftf,
                    'comeback_now': new_comeback}
        elif ftf_better or comeback_better:
            return {'verdict': 'partial_progress', 'detail': '...'}
        else:
            return {'verdict': 'no_progress',
                    'note': 'Sau T+14 chưa thấy thay đổi — cân nhắc training intensive'}

    return {'verdict': 'general_review_needed'}
```

---

## 4. Review T+30 (Operational)

### 4.1 Mục đích

Đo **KPI thực tế** đã cải thiện theo mục tiêu chưa.

### 4.2 So sánh baseline → cur

```python
def review_T30_service(gp, baseline, cur_kpi, target_kpi):
    """
    Tính delta vs baseline + so sánh với target.
    Áp dụng riêng cho KPI Service.
    """
    deltas = {}
    for k in target_kpi:
        if k not in baseline or k not in cur_kpi:
            deltas[k] = {'verdict': 'no_data'}
            continue

        delta_abs = cur_kpi[k] - baseline[k]
        delta_pct = delta_abs / max(abs(baseline[k]), 0.01) * 100

        # Hướng cải thiện
        is_higher_better = (k in ['ftf_rate', 'csi_mean', 'capture_rate',
                                   'DT_RO', 'PT_RO', 'on_time_BDĐK'])
        if is_higher_better:
            improved = cur_kpi[k] > baseline[k]
            target_met = cur_kpi[k] >= target_kpi[k]
        else:  # comeback_rate, no_show_rate, gio_per_RO — thấp là tốt
            improved = cur_kpi[k] < baseline[k]
            target_met = cur_kpi[k] <= target_kpi[k]

        # Ngưỡng có ý nghĩa
        SIGNIFICANT = {
            'ftf_rate': 0.05,      # 5 điểm %
            'comeback_rate': 0.02, # 2 điểm %
            'csi_mean': 0.20,      # 0.2 điểm thang 1-5
            'capture_rate': 0.03,  # 3 điểm %
            'DT_RO': 0.10,         # 10% tương đối
            'PT_RO': 0.10,
            'gio_per_RO': 0.15,    # 15% tương đối
            'no_show_rate': 0.05
        }
        threshold = SIGNIFICANT.get(k, 0.05)
        is_significant = abs(delta_abs) >= threshold

        if not is_significant:
            verdict = 'flat'
        elif improved and target_met:
            verdict = 'target_met'
        elif improved:
            verdict = 'improving_below_target'
        else:
            verdict = 'declining'

        deltas[k] = {
            'baseline': baseline[k],
            'cur': cur_kpi[k],
            'target': target_kpi[k],
            'delta_abs': delta_abs,
            'delta_pct': delta_pct,
            'verdict': verdict
        }

    # Verdict tổng
    verdicts = [d['verdict'] for d in deltas.values() if d['verdict'] != 'no_data']
    if not verdicts:
        overall = 'insufficient_data'
    elif all(v in ('target_met', 'improving_below_target') for v in verdicts):
        overall = 'on_track'
    elif any(v == 'declining' for v in verdicts):
        overall = 'declining'
    elif all(v == 'flat' for v in verdicts):
        overall = 'flat'
    else:
        overall = 'mixed'

    return {'kpi_deltas': deltas, 'overall_verdict': overall}
```

### 4.3 Quyết định hành động sau T+30

| Verdict | Action | Lưu ý đặc biệt cho Service |
|---|---|---|
| `target_met` | Đóng GP | Chuyển sang T+60 sustained check |
| `on_track` | Tiếp tục, review T+60 | |
| `mixed` | Phân tích sâu KPI flat | Có thể GP chỉ đang sửa 1 nguyên nhân, còn nguyên nhân khác |
| `flat` | Diagnose: training chưa đủ? KPI chọn sai? | Cân nhắc training intensive thay vì chấm dứt |
| `declining` | Dừng GP, escalate | Có thể chiến lược sai hoặc có yếu tố ngoài |
| `insufficient_data` | Mở rộng cửa sổ +15d | Service cần đủ ≥ 30 RO mới của cá nhân |

### 4.4 Mẫu báo cáo T+30 cho GP về KTV

```markdown
# Review T+30 — GP TH-K01 — KTV001 (Phạm Văn A)

**Vấn đề gốc:** KTV001 FTF 0.71 vs team 0.92, comeback 11% vs team 4% (mẫu 38 RO baseline)

**Giải pháp:** Module training quy_trinh_chan_doan + quality_check + sua_dung_lan_dau + kèm cặp 4 tuần bởi KTV017

**KPI đo (5/05 → 5/06/2026, mẫu 42 RO mới):**

| KPI            | Baseline | Hiện tại | Target   | Delta  | Verdict       |
|----------------|----------|----------|----------|--------|---------------|
| ftf_rate       | 0.71     | 0.86     | ≥ 0.85   | +0.15  | target_met ✓ |
| comeback_rate  | 0.11     | 0.05     | ≤ 0.06   | -0.06  | target_met ✓ |
| gio_per_RO     | 4.2h     | 3.8h     | ≤ 4.0h   | -0.4h  | target_met ✓ |

**Verdict tổng: on_track**

**Hành động:**
- Đóng GP TH-K01 ✓
- Mở scheduled check T+60 (5/07): verify sustained
- Đề xuất Sub-Agent C (Training): xét KTV001 đủ tiêu chí ổn định L3

**Bằng chứng RO:** RO20260507-A1, RO20260512-B3, RO20260520-C7, ... (42 mã)
```

---

## 5. Review T+60 (Sustained — đặc trưng Service)

### 5.1 Mục đích

Service đặc biệt cần T+60 vì:
- Sau training, KTV có thể "diễn" trong 30 ngày đầu rồi quay về cũ.
- Comeback cần ≥ 60 ngày để có đủ mẫu KH quay lại.
- KPI sustained mới chứng minh GP thật sự hiệu quả.

### 5.2 Code T+60

```python
def review_T60_sustained(gp, baseline, kpi_T30, kpi_T60):
    """
    Verify KPI sau T+30 vẫn duy trì sau T+60.
    """
    drift_alerts = []
    for k in kpi_T30:
        if k not in kpi_T60:
            continue

        # Drift = T+60 - T+30
        drift = kpi_T60[k] - kpi_T30[k]
        is_higher_better = k in ['ftf_rate', 'csi_mean']

        if is_higher_better:
            regressed = drift < -0.03  # giảm > 3 điểm %
        else:
            regressed = drift > 0.03   # tăng > 3 điểm %

        if regressed:
            drift_alerts.append({
                'kpi': k,
                'T30': kpi_T30[k],
                'T60': kpi_T60[k],
                'drift': drift,
                'verdict': 'regressed_after_30d',
                'recommended': 'Mở booster training hoặc kiểm tra lại quy trình'
            })

    if not drift_alerts:
        return {'verdict': 'sustained', 'note': 'GP thực sự hiệu quả lâu dài'}
    else:
        return {'verdict': 'regression_detected', 'alerts': drift_alerts}
```

---

## 6. Quy tắc đặt ngày review cho `ro-analyzer` / `csi-diagnoser`

```python
def calculate_service_review_dates(today, gp_nhom, han):
    today = pd.Timestamp(today)
    han = pd.Timestamp(han)

    base_dates = {
        'T+7':  today + pd.Timedelta(days=7),
        'T+14': today + pd.Timedelta(days=14),
        'T+30': today + pd.Timedelta(days=30),
        'T+60': today + pd.Timedelta(days=60)
    }

    if gp_nhom == 'Đào tạo':
        # Training: cần T+7 (start), T+30 (đo), T+60 (sustained), T+90 (validate)
        return {**base_dates, 'T+90': today + pd.Timedelta(days=90)}

    elif gp_nhom == 'Quy trình':
        # Quy trình: audit nhanh, đo nhanh
        return {'T+3': today + pd.Timedelta(days=3),
                'T+7': base_dates['T+7'],
                'T+14': base_dates['T+14'],
                'T+30': base_dates['T+30']}

    elif gp_nhom in ('Marketing', 'Recall'):
        # Recall campaign: đo trong 30d hết, không cần T+60
        return {'T+7': base_dates['T+7'],
                'T+14': base_dates['T+14'],
                'T+30': base_dates['T+30']}

    elif gp_nhom == 'Năng lực':
        # Mở thêm ca / tuyển KTV: dài hạn
        return {'T+14': base_dates['T+14'],
                'T+30': base_dates['T+30'],
                'T+60': base_dates['T+60'],
                'T+90': today + pd.Timedelta(days=90)}

    else:
        return base_dates
```

---

## 7. Long-term memory cho Service

### 7.1 Cấu trúc file

```
pgs-service-analytics/memory/
├── baselines/
│   ├── DongNai_workshop_2026-04.json
│   └── ...
├── gp_history/
│   ├── DongNai_GP-S-001.json    # 1 GP từ T0 → T+60
│   └── ...
├── ktv_tracking/
│   ├── KTV001.json              # tracking dài hạn 1 KTV
│   └── ...
└── recall_campaigns/
    └── DongNai_2026-Q2_recall.json
```

### 7.2 Schema baseline xưởng

```json
{
  "chi_nhanh": "DongNai",
  "ky": "2026-04",
  "ngay_chot_baseline": "2026-05-05",
  "kpi_xuong": {
    "tong_doanh_thu": 4_850_000_000,
    "n_RO": 842,
    "DT_per_RO": 5_760_000,
    "capture_rate_pct": 72.0,
    "comeback_rate_pct": 4.2,
    "ftf_rate_pct": 91.5,
    "utilization_pct": 78,
    "no_show_rate_pct": 18,
    "csi_mean": 4.42
  },
  "kpi_per_ktv": {
    "KTV001": {"n_RO": 38, "ftf_rate": 0.71, "comeback_rate": 0.11, "gio_per_RO": 4.2},
    "KTV017": {"n_RO": 52, "ftf_rate": 0.95, "comeback_rate": 0.02, "gio_per_RO": 3.0},
    "...": "..."
  },
  "kpi_per_cvdv": {
    "CVDV001": {"n_RO": 165, "PT_per_RO": 2_650_000, "csi": 4.45},
    "CVDV004": {"n_RO": 148, "PT_per_RO": 3_850_000, "csi": 4.05},
    "...": "..."
  }
}
```

### 7.3 Schema GP history

```json
{
  "ma_GP": "DongNai-2026-04-GP-S-007",
  "ngay_xuat": "2026-05-05",
  "nhom": "Đào tạo + Chất lượng",
  "tinh_huong_playbook": "TH-K01",
  "van_de": "KTV001 FTF 0.71, comeback 11%",
  "giai_phap": "Module training + kèm cặp 4 tuần",
  "chu_the": "KTV001 + KTV017 + Tổ trưởng",
  "kpi_target": {"ftf_rate": ">=0.85", "comeback_rate": "<=0.06", "gio_per_RO": "<=4.0"},
  "han": "2026-06-30",
  "baseline_kpi": {"ftf_rate": 0.71, "comeback_rate": 0.11, "gio_per_RO": 4.2,
                   "n_RO_baseline": 38},
  "bang_chung_RO_baseline": ["RO20260403-A1", "...", "..."],
  "reviews": [
    {
      "ngay_review": "2026-05-12", "chu_ky": "T+7",
      "% hoan_thanh": 30, "blocker": null,
      "note": "KTV001 đăng ký 4/4 module, KTV017 nhận kèm cặp"
    },
    {
      "ngay_review": "2026-05-19", "chu_ky": "T+14",
      "kpi_so_bo": {"ftf_rate": 0.78, "n_RO_moi": 14},
      "verdict": "on_track", "note": "Pattern giảm rõ rệt"
    },
    {
      "ngay_review": "2026-06-04", "chu_ky": "T+30",
      "kpi_cur": {"ftf_rate": 0.86, "comeback_rate": 0.05, "gio_per_RO": 3.8,
                  "n_RO_moi": 42},
      "verdict": "target_met", "action": "Đóng GP, scheduled T+60"
    },
    {
      "ngay_review": "2026-07-04", "chu_ky": "T+60",
      "kpi_cur": {"ftf_rate": 0.88, "comeback_rate": 0.04, "gio_per_RO": 3.7,
                  "n_RO_moi": 79},
      "verdict": "sustained", "action": "Đề xuất KTV001 thăng L3"
    }
  ],
  "trang_thai": "Done_Sustained",
  "ngay_dong": "2026-07-04",
  "handoff_tao_ra": [
    {"ngay": "2026-07-04", "den": "pgs-training-management",
     "noi_dung": "KTV001 đủ tiêu chí thăng L3 — đề nghị Sub-Agent C đánh giá"}
  ]
}
```

---

## 8. Quy tắc bất biến

1. **Mọi GP phải có ≥ 1 ngay_review** — không có review = không Agentic Loop.
2. **Baseline phải ghi trước khi GP bắt đầu** — Hook H6 enforce.
3. **GP về KTV/CVDV bắt buộc có T+60 sustained check** — chống "diễn 30 ngày".
4. **Mỗi review có verdict cụ thể** — không "tạm tốt".
5. **GP overdue 2 chu kỳ → escalate Trưởng phòng dịch vụ** — không treo vô hạn.
6. **T+30 KPI sample < 30 RO của cá nhân → mở rộng +15d** — không vội kết luận.
7. **Sustained sau T+60 mới đề xuất thăng cấp** — không thăng vội sau T+30.

---

## 9. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| KTV target nghỉ ốm giữa kỳ | Pause GP, ghi note, không tính vào KPI |
| Hãng triệu hồi đột xuất → ảnh hưởng KPI | Loại RO recall khỏi đo lường |
| Sau T+30 KPI tốt nhưng T+60 quay lại cũ | Mở booster training, mở GP mới |
| Comeback bất thường do PT lô lỗi | Loại khỏi KPI KTV, mở GP riêng cho supply chain |
| KTV target chuyển chi nhánh giữa kỳ | Gp chuyển theo, kèm bàn giao cho tổ trưởng mới |
| GP đóng sớm vì target_met sau T+14 | Vẫn mở scheduled T+60 — chống ngược lại |
| Nhiều GP cùng chủ thể → trùng review date | Gộp review cùng ngày, không gọi nhiều lần |
