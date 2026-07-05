# Reference 06 — Chu kỳ Review +30 / +60 / +90 cho Training

> **Khi nào load:** Sub-Agent D (Reviewer) đến hạn review hiệu quả training;
> hoặc khi user hỏi "Module training X có hiệu quả không", "Sau training, KTV001 đã cải thiện chưa".

---

## 1. Triết lý: Đóng vòng lặp Agentic

Sub-Agent D là **mảnh ghép cuối** của Agentic Loop:

```
Sub-A (Composer) ─→ Sub-B (Test Builder) ─→ Sub-C (Evaluator) ─→ TRAINING ─→ Sub-D (Reviewer)
                                                                              │
              ┌────────────────────────────────────────────────────────────────┘
              ▼
   Sub-D đo: Training có cải thiện KPI thực không?
              │
              ├─ Có → ghi success vào memory, đề xuất module tương tự
              │      cho NS khác (đóng loop, lan toả)
              │
              └─ Không → ghi failure vào memory, revise module / đổi cách dạy
                          (đóng loop, học từ lỗi)
```

→ Không có Sub-D = training "bắn rồi quên" = không học được = không Agentic.

---

## 2. Chu kỳ chuẩn cho Training

```
T0 (NS hoàn thành module + test pass)
   │
   ├─ T+7   Kick-off check: NS đã ứng dụng vào việc thật chưa?
   │
   ├─ T+30  Soft-measure: KPI thực có dấu hiệu cải thiện không?
   │
   ├─ T+60  Hard-measure: KPI cải thiện rõ rệt chưa? (đủ mẫu)
   │
   └─ T+90  Sustained-measure: Cải thiện có bền vững không?
```

**Khác Service:** Training cần T+90 vì:
- Hành vi mới (sau training) cần ≥ 60 ngày để thành thói quen.
- Mẫu RO của 1 KTV cá nhân tích lũy chậm hơn xưởng tổng.
- Pass-rate test ≠ áp dụng được — phải verify thực chiến.

---

## 3. Review T+7 (Kick-off)

### 3.1 Câu hỏi

```yaml
T+7 Training Checklist:
  - Sau training, NS đã quay lại làm việc bình thường chưa?
  - NS đã có RO mới ứng dụng kiến thức module chưa? (n_RO_post >= 5?)
  - NS có gặp khó khăn khi áp dụng không? (phỏng vấn ngắn 5 phút)
  - Manager (tổ trưởng / trưởng phòng) đã observe NS làm việc chưa?
```

### 3.2 Code

```python
def review_T7_training(training_record, ro_data_after_T0):
    """
    Check NS đã bắt đầu áp dụng kiến thức chưa.
    """
    ma_NS = training_record['ma_NS']
    T0 = pd.Timestamp(training_record['ngay_pass_test'])

    # RO post-training
    df_post = ro_data_after_T0[
        (ro_data_after_T0['ma_KTV_chinh'] == ma_NS) &
        (ro_data_after_T0['ngay_mo_RO'] >= T0)
    ]

    n_RO_post = len(df_post)
    if n_RO_post == 0:
        return {'verdict': 'chua_ung_dung',
                'note': 'NS chưa có RO mới — kiểm tra: nghỉ phép? đang training tiếp?'}
    if n_RO_post < 3:
        return {'verdict': 'moi_bat_dau',
                'n_RO_post': n_RO_post,
                'note': 'Còn quá ít RO để đánh giá, đợi T+30'}
    return {'verdict': 'da_ung_dung',
            'n_RO_post': n_RO_post,
            'note': 'NS đã quay lại nhịp làm việc bình thường'}
```

### 3.3 Action sau T+7

| Verdict | Action |
|---|---|
| `chua_ung_dung` | Liên hệ tổ trưởng tìm lý do; nếu nghỉ dài → pause review |
| `moi_bat_dau` | Tiếp tục theo dõi, đến T+30 review lại |
| `da_ung_dung` | OK, scheduled T+30 |

---

## 4. Review T+30 (Soft Measure)

### 4.1 Mục đích

Đo dấu hiệu sớm KPI có cải thiện không. **Mẫu chưa đủ kết luận chắc** (≥ 30 RO mới của cá nhân hiếm trong 30 ngày), nhưng phát hiện sớm để can thiệp.

### 4.2 Code

```python
def review_T30_training(training_record, ro_post, baseline_kpi):
    """
    So sánh KPI sau 30 ngày với baseline.
    """
    ma_NS = training_record['ma_NS']
    T0 = pd.Timestamp(training_record['ngay_pass_test'])
    T30 = T0 + pd.Timedelta(days=30)

    df_post = ro_post[
        (ro_post['ma_KTV_chinh'] == ma_NS) &
        (ro_post['ngay_mo_RO'].between(T0, T30)) &
        (ro_post['trang_thai_RO'] == 'closed')
    ]

    n_post = len(df_post)
    if n_post < 10:
        return {'verdict': 'sample_too_small',
                'n_RO_post': n_post,
                'note': 'Mẫu < 10 RO, đợi T+60. KPI sơ bộ không tin cậy.'}

    cur_kpi = {
        'ftf_rate': df_post['FTF_flag'].mean(),
        'comeback_rate': df_post['comeback_flag'].mean(),
        'gio_per_RO': df_post['gio_cong_total'].sum() / n_post,
        'n_RO': n_post
    }

    # So với baseline
    deltas = compare_kpi(baseline_kpi, cur_kpi)

    # Verdict (T+30 dùng ngưỡng nới hơn T+60)
    if deltas['ftf_delta'] >= 0.05 and deltas['comeback_delta'] <= -0.02:
        verdict = 'early_improvement'
    elif deltas['ftf_delta'] >= 0.02 or deltas['comeback_delta'] <= -0.01:
        verdict = 'partial_improvement'
    elif abs(deltas['ftf_delta']) < 0.02 and abs(deltas['comeback_delta']) < 0.01:
        verdict = 'flat_too_early'
    else:
        verdict = 'declining_concern'

    return {'verdict': verdict, 'cur_kpi': cur_kpi, 'baseline_kpi': baseline_kpi,
            'deltas': deltas, 'n_post': n_post}
```

### 4.3 Action sau T+30

| Verdict | Action |
|---|---|
| `early_improvement` | OK, scheduled T+60 |
| `partial_improvement` | OK, scheduled T+60 (theo dõi sát) |
| `flat_too_early` | OK đợi T+60 (chưa đủ thời gian thấm) |
| `declining_concern` | Phỏng vấn NS + tổ trưởng — có gì cản trở không? |
| `sample_too_small` | Tiếp tục theo dõi |

---

## 5. Review T+60 (Hard Measure)

### 5.1 Mục đích

T+60 là điểm **quyết định**: training có hiệu quả không. Mẫu thường đủ (≥ 30 RO/cá nhân).

### 5.2 Code

```python
def review_T60_training(training_record, ro_post, baseline_kpi, target_kpi):
    """
    Đánh giá hiệu quả training cứng. Dùng để kết luận pass/fail của module + của NS.
    """
    ma_NS = training_record['ma_NS']
    T0 = pd.Timestamp(training_record['ngay_pass_test'])
    T60 = T0 + pd.Timedelta(days=60)

    df_post = ro_post[
        (ro_post['ma_KTV_chinh'] == ma_NS) &
        (ro_post['ngay_mo_RO'].between(T0, T60)) &
        (ro_post['trang_thai_RO'] == 'closed')
    ]

    n_post = len(df_post)
    if n_post < 30:
        return {'verdict': 'sample_insufficient_extend_to_T90',
                'n_RO_post': n_post,
                'note': 'Mẫu chưa đủ 30 RO — kéo dài cửa sổ đến T+90'}

    cur_kpi = {
        'ftf_rate': df_post['FTF_flag'].mean(),
        'comeback_rate': df_post['comeback_flag'].mean(),
        'gio_per_RO': df_post['gio_cong_total'].sum() / n_post,
        'n_RO': n_post
    }

    # So với baseline + target
    target_met = check_target(cur_kpi, target_kpi)
    improved = check_improvement(baseline_kpi, cur_kpi)

    if target_met:
        verdict = 'training_successful'
    elif improved:
        verdict = 'improving_below_target'
    else:
        verdict = 'training_not_effective'

    return {
        'verdict': verdict,
        'cur_kpi': cur_kpi,
        'baseline_kpi': baseline_kpi,
        'target_kpi': target_kpi,
        'n_post': n_post,
        'evidence_RO': df_post['ma_RO'].tolist()
    }

def check_target(cur, target):
    """Mọi KPI đạt target → True."""
    return all(
        cur[k] >= v if k in ('ftf_rate',) else cur[k] <= v
        for k, v in target.items() if k in cur
    )

def check_improvement(baseline, cur, threshold=0.05):
    """Có ≥ 1 KPI cải thiện rõ rệt."""
    if cur['ftf_rate'] - baseline['ftf_rate'] >= threshold: return True
    if baseline['comeback_rate'] - cur['comeback_rate'] >= 0.02: return True
    return False
```

### 5.3 Action sau T+60

| Verdict | Action |
|---|---|
| `training_successful` | Đóng review, scheduled T+90 sustained |
| `improving_below_target` | Booster training (1 buổi nâng cao); review T+90 |
| `training_not_effective` | **Critical:** revise module / đổi giảng viên / re-train NS |
| `sample_insufficient` | Kéo dài đến T+90 |

### 5.4 Khi `training_not_effective`

Sub-Agent D phải làm 3 việc:

```python
def handle_training_failure(training_record, kpi_result):
    """
    Khi T+60 verdict = training_not_effective:
    1. Ghi vào memory failure case
    2. Thông báo Sub-Agent A revise module
    3. Đề xuất plan cho NS
    """
    return {
        'failure_case': {
            'ma_NS': training_record['ma_NS'],
            'module_id': training_record['module_id'],
            'baseline_kpi': kpi_result['baseline_kpi'],
            'after_60d_kpi': kpi_result['cur_kpi'],
            'no_improvement_reason': 'pending_investigation'
        },
        'handoff_to_sub_A': {
            'request': 'revise_module',
            'reason': f"Module {training_record['module_id']} không cải thiện KPI cho 1 NS",
            'priority': 'medium',
            'note': 'Cần xem xét nếu nhiều NS cùng fail → revise; nếu 1 NS fail → có thể vấn đề cá nhân'
        },
        'plan_for_NS': {
            'option_1': 'Re-train (học lại module + retake test)',
            'option_2': 'Module bù song song (kèm cặp 1-1 bởi NS top)',
            'option_3': 'Đánh giá lại định hướng nghề (nếu repeat fail 2+ lần)'
        }
    }
```

---

## 6. Review T+90 (Sustained Measure)

### 6.1 Mục đích

Verify cải thiện ở T+60 **bền vững**, không phải "tăng tạm" rồi quay lại cũ.

### 6.2 Code

```python
def review_T90_training(training_record, ro_post, kpi_T60):
    """
    Check KPI duy trì sau 30 ngày tiếp theo (từ T+60 → T+90).
    """
    ma_NS = training_record['ma_NS']
    T60 = pd.Timestamp(training_record['ngay_pass_test']) + pd.Timedelta(days=60)
    T90 = T60 + pd.Timedelta(days=30)

    df_T60_T90 = ro_post[
        (ro_post['ma_KTV_chinh'] == ma_NS) &
        (ro_post['ngay_mo_RO'].between(T60, T90)) &
        (ro_post['trang_thai_RO'] == 'closed')
    ]

    n_T90 = len(df_T60_T90)
    if n_T90 < 15:
        return {'verdict': 'extend_window',
                'note': f'Chỉ {n_T90} RO trong T+60-T+90, kéo dài thêm 30d'}

    kpi_T90 = {
        'ftf_rate': df_T60_T90['FTF_flag'].mean(),
        'comeback_rate': df_T60_T90['comeback_flag'].mean(),
        'gio_per_RO': df_T60_T90['gio_cong_total'].sum() / n_T90
    }

    # So T+60 → T+90: có regress không?
    regression = []
    if kpi_T60['ftf_rate'] - kpi_T90['ftf_rate'] > 0.05:
        regression.append('ftf_regressed')
    if kpi_T90['comeback_rate'] - kpi_T60['comeback_rate'] > 0.03:
        regression.append('comeback_regressed')

    if not regression:
        verdict = 'sustained'
    elif len(regression) == 2:
        verdict = 'fully_regressed'   # quay về như chưa training
    else:
        verdict = 'partially_regressed'

    return {'verdict': verdict, 'kpi_T60': kpi_T60, 'kpi_T90': kpi_T90,
            'regression': regression, 'n_T90': n_T90}
```

### 6.3 Action sau T+90

| Verdict | Action |
|---|---|
| `sustained` | ✓ Đóng case. Ghi success vào memory. Đề xuất NS thăng cấp (nếu đủ điều kiện) |
| `partially_regressed` | Booster training nhỏ (1 buổi refresh) |
| `fully_regressed` | Critical — revise module + re-train NS |

---

## 7. Long-term Memory cho Training

### 7.1 Cấu trúc thư mục

```
pgs-training-management/memory/
├── module_effectiveness/
│   ├── KTV-L3-015_effectiveness.json
│   └── ...
├── ns_history/
│   ├── KTV001_full_history.json
│   └── ...
├── failure_cases/
│   ├── 2026-Q2_failures.json
│   └── ...
└── success_patterns/
    ├── 2026-Q2_successes.json
    └── ...
```

### 7.2 Schema module_effectiveness

```json
{
  "module_id": "KTV-L3-015",
  "version": "1.0",
  "ngay_phat_hanh": "2026-04-15",
  "n_NS_da_hoc": 12,
  "n_NS_pass_test": 11,
  "n_NS_T60_successful": 9,
  "n_NS_T90_sustained": 8,
  "ti_le_thanh_cong_thuc_te": 0.667,
  "kpi_avg_improvement": {
    "ftf_rate_delta": +0.12,
    "comeback_rate_delta": -0.04,
    "gio_per_RO_delta": -0.3
  },
  "failure_patterns": [
    "1 NS regressed sau T+90 — không có manager đôn đốc",
    "1 NS không áp dụng vào RO loại nâng cao"
  ],
  "verdict_module": "EFFECTIVE_BUT_NEEDS_MENTOR_SUPPORT",
  "recommended_changes": [
    "Bổ sung phần 'Cách áp dụng vào RO thực tế hằng ngày'",
    "Yêu cầu mentor follow-up 30d sau training"
  ]
}
```

### 7.3 Schema ns_history

```json
{
  "ma_NS": "KTV001",
  "ten": "Phạm Văn A",
  "trainings": [
    {
      "module_id": "KTV-L2-007",
      "ngay_pass": "2025-08-15",
      "test_score": 78,
      "T60_verdict": "training_successful",
      "T90_verdict": "sustained"
    },
    {
      "module_id": "KTV-L3-015",
      "ngay_pass": "2026-05-12",
      "test_score": 84,
      "T30_verdict": "early_improvement",
      "T60_verdict": "training_successful",
      "T90_verdict": "sustained",
      "evidence_RO_post": ["RO20260520-A1", "..."]
    }
  ],
  "promotion_history": [
    {"from_level": 1, "to_level": 2, "ngay": "2025-09-01", "by": "Trưởng phòng dịch vụ"},
    {"from_level": 2, "to_level": 3, "ngay": "2026-08-01", "by": "Trưởng phòng dịch vụ"}
  ],
  "agentic_loops_closed": 2
}
```

---

## 8. Đóng vòng lặp Agentic — sang skill khác

Khi T+90 sustained, Sub-Agent D **chủ động** trigger handoff:

### 8.1 Sang `pgs-service-analytics`

```yaml
# Sub-Agent D phát hiện KTV001 đã sustained sau training
handoff_to: pgs-service-analytics
context: |
  KTV001 sau khi học KTV-L3-015 + 90 ngày sustained:
  - FTF: 0.71 → 0.91 (sustained)
  - Comeback: 0.11 → 0.04 (sustained)
  - Đã đủ tiêu chí thăng L3 (xem 02-level-competency-matrix)
request:
  - "Cập nhật pattern KTV001 từ 'chat_luong_kem' về 'on_track'"
  - "Loại KTV001 khỏi danh sách 'cần can thiệp' tổ KTV"
  - "Áp dụng module KTV-L3-015 cho các KTV khác có pattern tương tự"
```

### 8.2 Lan toả module hiệu quả

```yaml
# Sub-Agent D phát hiện module KTV-L3-015 hiệu quả
handoff_to: main_agent
context: "Module KTV-L3-015 hiệu quả 67% trên 12 NS"
request:
  - "Đề xuất tổ trưởng KTV: tất cả KTV L2 trong tổ Đồng Nai có pattern 'chat_luong_kem' nên học module này"
  - "Mở campaign training Q3/2026 sử dụng module này làm tài liệu chính"
```

---

## 9. Reporting tổng hợp Q (quý)

```python
def quarterly_training_report(quarter, all_records):
    """
    Báo cáo hiệu quả training toàn quý.
    """
    return {
        'quarter': quarter,
        'n_modules_run': ...,
        'n_NS_trained': ...,
        'pass_test_rate_avg': ...,
        'T60_success_rate_avg': ...,
        'T90_sustained_rate_avg': ...,
        'top_3_modules_effective': ...,
        'bottom_3_modules_to_revise': ...,
        'failure_themes': [...],
        'success_themes': [...],
        'recommended_focus_next_quarter': [...]
    }
```

---

## 10. Quy tắc bất biến

1. **Mọi NS pass test → tự động tạo scheduled T+30/T+60/T+90** — không "quên" review.
2. **T+60 mẫu < 30 RO → kéo dài đến T+90, không kết luận vội** — Hook H7.
3. **Verdict `training_not_effective` ở T+60 → Sub-Agent D MUST handoff về Sub-Agent A revise** — không treo.
4. **T+90 sustained mới đủ căn cứ thăng cấp** — không vội ở T+60.
5. **Mọi failure phải ghi vào memory** — học từ lỗi.
6. **Mỗi module hiệu quả phải được đề xuất lan toả** — đóng vòng lặp.
7. **Sub-Agent D chủ động trigger handoff cross-skill** — không thụ động.

---

## 11. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| NS nghỉ ốm dài giữa T0-T+60 | Pause review, kéo dài cửa sổ tương ứng |
| NS chuyển bộ phận sau training | Đánh giá hiệu quả tại bộ phận cũ (mẫu RO trước chuyển) |
| Module áp dụng cho nhiều NS, đa số fail | Revise module urgent, không đổ lỗi cá nhân |
| 1 NS pass T+60 nhưng fail T+90 do hoàn cảnh (đổi tổ trưởng) | Không tính fail module, ghi note hoàn cảnh |
| Module mới chỉ có 1-2 NS học | Chưa đủ căn cứ kết luận hiệu quả module — đợi ≥ 5 NS |
| KPI cải thiện do yếu tố khác (PT chất lượng tăng) | Sub-Agent D phải kiểm tra context chi nhánh trước khi gán tín dụng cho module |
| NS từ chối cho measurement | Vẫn track qua RO data, không cần consent thêm (đây là KPI nội bộ) |
