# Reference 08 — Chu kỳ Review (7 / 30 / 90 ngày)

> **Khi nào load:** Hook H6 đến hạn tạo scheduled review; hoặc Sub-agent `plan-builder` cần
> đặt `ngay_review` chuẩn; hoặc user hỏi "Review giải pháp tuần trước".

---

## 1. Triết lý chu kỳ review

Mỗi GP cần **3 mốc review** để đảm bảo Agentic Loop:

```
T0 (xuất GP) ──── T+7 (tactical) ──── T+30 (operational) ──── T+90 (strategic)
                  ↓                    ↓                        ↓
              "Đang chạy đúng       "Có cải thiện              "Có ROI thực sự
               hướng không?"        KPI đo được không?"        không? Nhân rộng?"
```

| Chu kỳ | Hỏi gì | Hành động |
|---|---|---|
| **T+7** (Tactical) | Đã bắt đầu? Có blocker không? | Unblock, điều chỉnh nhỏ |
| **T+30** (Operational) | KPI có cải thiện theo target không? | Giữ / Điều chỉnh / Dừng GP |
| **T+90** (Strategic) | ROI có rõ ràng? Có thể nhân rộng? | Đóng vòng lặp / Scale-up / Pivot |

---

## 2. Review T+7 (Tactical)

### 2.1 Mục đích

Đảm bảo GP đã được **bắt đầu thực sự** — không bị trôi.

### 2.2 Checklist

```yaml
T+7 Review Checklist:
  - GP đã được giao cho chủ thể chưa? (có meeting kick-off?)
  - Chủ thể có hiểu rõ KPI mục tiêu không?
  - Có resource cần thiết chưa? (ngân sách, công cụ, người)
  - Có blocker nào? (chờ phê duyệt, chờ training, chờ KPI cũ)
  - Tiến độ baseline so với plan: 0% / <30% / 30-70% / >70%
```

### 2.3 Code Python — sinh prompt cho scheduled task T+7

```python
def gen_T7_review_prompt(gp):
    """
    Sinh prompt cho scheduled task review T+7.
    """
    return f"""
Review T+7 cho GP: {gp['ma_GP']}

Vấn đề: {gp['van_de']}
Giải pháp: {gp['giai_phap']}
Chủ thể: {gp['chu_the']}
KPI mục tiêu: {gp['kpi']}
Hạn: {gp['han']}

Hôm nay {gp['ngay_review_T7']}, đã T+7 ngày từ khi xuất GP.

Câu hỏi cần trả lời:
1. GP đã chính thức bắt đầu chưa? (meeting kick-off, phân công NS, ngân sách approve?)
2. Có blocker nào đang ngăn cản? Liệt kê cụ thể.
3. Estimate % hoàn thành tới giờ.
4. Có cần điều chỉnh gì trong tuần tới không?

Nếu GP chưa bắt đầu sau T+7 → escalate cho GĐ ĐL (cờ đỏ).
Nếu có blocker → mở GP phụ để giải quyết blocker.

Cập nhật Sheet 3 (Action Plan) trong file_quan_tri_<chi_nhanh>_<thang>.xlsx
với % hoàn thành mới + ghi chú.
"""
```

### 2.4 Diễn giải kết quả T+7

| % hoàn thành | Diễn giải | Action |
|---|---|---|
| 0% | Chưa bắt đầu | ⚠️ Cờ đỏ, escalate |
| 1-30% | Mới khởi động | Bình thường, theo dõi |
| 30-70% | Đúng tiến độ | OK, tiếp tục |
| > 70% | Vượt tiến độ | Có thể đóng sớm hoặc mở rộng scope |

---

## 3. Review T+30 (Operational)

### 3.1 Mục đích

Đo **KPI thực tế** đã cải thiện theo mục tiêu chưa.

### 3.2 So sánh baseline → cur — code

```python
def review_T30(gp, baseline, cur_kpi, target_kpi):
    """
    Tính delta vs baseline + so sánh với target.
    """
    deltas = {}
    for k in target_kpi:
        if k not in baseline or k not in cur_kpi:
            deltas[k] = {'verdict': 'no_data'}
            continue

        delta_abs = cur_kpi[k] - baseline[k]
        delta_pct = delta_abs / baseline[k] * 100 if baseline[k] != 0 else None

        # Hướng cải thiện (tăng hay giảm là tốt)
        is_higher_better = (k in ['ty_le_chot', 'cold_to_warm', 'warm_to_hot',
                                  'hot_to_HD', 'doanh_so', 'csi'])
        if is_higher_better:
            improved = cur_kpi[k] > baseline[k]
            target_met = cur_kpi[k] >= target_kpi[k]
        else:
            improved = cur_kpi[k] < baseline[k]
            target_met = cur_kpi[k] <= target_kpi[k]

        # Ngưỡng "có ý nghĩa"
        SIGNIFICANT = {
            'ty_le_chot': 0.03, 'cold_to_warm': 0.05,
            'warm_to_hot': 0.05, 'hot_to_HD': 0.05,
            'csi': 0.20, 'doanh_so': 0.10  # 10% tương đối
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

### 3.3 Quyết định hành động sau T+30

| Verdict tổng | Action |
|---|---|
| `target_met` (đã đạt) | Đóng GP, ghi vào "đã hoàn thành" |
| `on_track` (đang cải thiện đúng hướng) | Tiếp tục, review T+90 |
| `mixed` (vài KPI tốt, vài KPI flat) | Phân tích sâu KPI flat, có thể bổ sung GP phụ |
| `flat` (không cải thiện) | Diagnose: GP triển khai sai, KPI sai, hay vấn đề ngoài tầm? |
| `declining` (kém đi) | ⚠️ Dừng GP, escalate, có thể chiến lược sai |
| `insufficient_data` | Mở rộng cửa sổ đo +15d |

### 3.4 Mẫu báo cáo T+30 (1 trang)

```markdown
# Review T+30 — GP TH-B01 — TVBH NV001

**Vấn đề gốc:** TVBH NV001 CR Cold→Warm 0.32 (TB team 0.61)

**Giải pháp:** Module training "khai_thac_nhu_cau" + kèm cặp 4 tuần

**KPI đo (5/05 → 5/06/2026):**

| KPI            | Baseline | Hiện tại | Target   | Delta  | Verdict       |
|----------------|----------|----------|----------|--------|---------------|
| ty_le_chot     | 0.08     | 0.19     | ≥ 0.18   | +0.11  | target_met ✓ |
| cold_to_warm   | 0.32     | 0.58     | ≥ 0.55   | +0.26  | target_met ✓ |
| warm_to_hot    | 0.50     | 0.51     | —        | +0.01  | flat          |

**Verdict tổng: on_track (target_met chính)**

**Hành động:**
- Đóng GP TH-B01 ✓
- Đề xuất Sub-Agent C (Training): xét NV001 đủ điều kiện ổn định ở Level 2
- Mở GP mới TH-B01.01: nhân rộng module cho 2 TVBH khác cùng pattern
- Lên scheduled review T+60 cho NV001 (theo dõi sustained)

**Bằng chứng:** 38 KHTN mới của NV001 trong T5/2026, RO mã KHTN-...
```

---

## 4. Review T+90 (Strategic)

### 4.1 Mục đích

Đánh giá **ROI** của cả nhóm GP trong quý + quyết định chiến lược dài hạn.

### 4.2 Câu hỏi T+90

```
1. Tổng số GP đóng / tổng GP đã mở: %
2. Trong số GP "target_met", có bao nhiêu sustained sau T+60 → T+90?
3. KPI cấp đại lý (doanh số, share, CSI) có chuyển biến không?
4. Có pattern hệ thống (vd: phần lớn TVBH đều yếu cùng stage)?
5. Có cần điều chỉnh strategy quý sau (vd: training group thay vì cá nhân)?
```

### 4.3 ROI calculation

```python
def calculate_roi_T90(gp_list, baseline_doanh_so, cur_doanh_so, total_cost):
    """
    Tính ROI tổng quý.
    total_cost = chi phí training + sự kiện + thưởng nóng + opportunity cost.
    """
    delta_doanh_so = cur_doanh_so - baseline_doanh_so
    revenue_uplift = delta_doanh_so * AVG_HD_VALUE
    profit_uplift = revenue_uplift * AVG_GROSS_MARGIN_PCT  # ~6-8% cho ô-tô

    roi = (profit_uplift - total_cost) / total_cost * 100

    return {
        'delta_doanh_so': delta_doanh_so,
        'revenue_uplift': revenue_uplift,
        'profit_uplift': profit_uplift,
        'total_cost': total_cost,
        'roi_pct': roi,
        'verdict': 'strong' if roi > 200 else 'moderate' if roi > 50
                    else 'weak' if roi > 0 else 'negative'
    }
```

### 4.4 Báo cáo T+90 (3-5 trang)

Cấu trúc:

```
1. Tổng quan kỳ:
   - Số GP đã mở / đóng / cancelled / overdue
   - Tỷ lệ thành công (% target_met)

2. KPI cấp đại lý:
   - Doanh số kỳ này vs cùng kỳ năm trước
   - Thị phần TH theo địa bàn
   - Share of dealer
   - CSI

3. Top 5 GP hiệu quả nhất (kèm bằng chứng KPI)

4. Top 5 GP kém hiệu quả + lessons learned

5. Đề xuất quý sau:
   - Tiếp tục: ...
   - Dừng: ...
   - Mới: ...

6. Phụ lục: chi tiết từng GP
```

---

## 5. Quy tắc đặt `ngay_review` cho `plan-builder`

```python
def calculate_review_dates(today, gp_nhom, han):
    """
    Tính ngay_review tự động dựa vào nhóm GP và hạn.
    """
    today = pd.Timestamp(today)
    han = pd.Timestamp(han)

    # T+7 luôn là (today + 7) hoặc giữa today và han / 4 — chọn cái nhỏ hơn
    t7 = min(today + pd.Timedelta(days=7), today + (han - today) / 4)

    # T+30 thường là 30 ngày sau today
    t30 = today + pd.Timedelta(days=30)

    # T+90 thường là 90 ngày sau today
    t90 = today + pd.Timedelta(days=90)

    # Nhưng tùy nhóm GP, lịch khác:
    if gp_nhom == 'Quy trình':
        # Quy trình cần audit sớm hơn
        return {'T+7': today + pd.Timedelta(days=7),
                'T+14': today + pd.Timedelta(days=14),
                'T+30': t30}

    elif gp_nhom == 'Đào tạo':
        # Đào tạo: T+7 (kiểm tra đã start), T+30 (đo KPI), T+60, T+90 (sustained)
        return {'T+7': t7, 'T+30': t30,
                'T+60': today + pd.Timedelta(days=60), 'T+90': t90}

    elif gp_nhom in ('Sự kiện', 'Marketing'):
        # Sự kiện: review trước event (1 tuần) + sau event (2 tuần) + đo HĐ (30d)
        han_event = han  # giả định han là ngày sự kiện
        return {'T-7': han_event - pd.Timedelta(days=7),
                'T+14_post_event': han_event + pd.Timedelta(days=14),
                'T+30_HD_check': han_event + pd.Timedelta(days=30)}

    else:
        return {'T+7': t7, 'T+30': t30, 'T+90': t90}
```

---

## 6. Tích hợp với scheduled task system

### 6.1 Tạo task qua MCP

```python
def create_review_scheduled_task(gp, review_date, prompt):
    """
    Gọi MCP scheduled task tool (giả định available qua main agent).
    """
    payload = {
        'title': f'Review GP {gp["ma_GP"]} — {review_date.strftime("%d/%m/%Y")}',
        'run_at': review_date.strftime('%Y-%m-%d 09:00:00'),
        'prompt': prompt,
        'tags': ['sales-review', f'gp-{gp["ma_GP"]}', f'cn-{gp["chi_nhanh"]}']
    }
    # main agent gọi tool tương ứng
    return payload
```

### 6.2 Tránh duplicate task

```python
def check_existing_review(gp_ma, review_date):
    """Kiểm tra đã có task review này chưa, tránh duplicate."""
    existing = get_scheduled_tasks(tag=f'gp-{gp_ma}')
    for task in existing:
        if abs((task['run_at'] - review_date).days) <= 1:
            return task  # đã có
    return None
```

---

## 7. Long-term memory: lưu baseline + history

### 7.1 Cấu trúc file

```
pgs-sales-analytics/memory/
├── baselines/
│   ├── DongNai_2026-04.json
│   ├── DongNai_2026-05.json
│   └── ...
├── gp_history/
│   ├── DongNai_GP-001.json    # lịch sử 1 GP từ T0 → T+90
│   └── ...
└── patterns/
    └── tvbh_yeu_cold_to_warm_NV001.json   # tracking dài hạn 1 NS
```

### 7.2 Schema baseline

```json
{
  "chi_nhanh": "DongNai",
  "ky": "2026-04",
  "ngay_chot_baseline": "2026-05-05",
  "kpi_team": {
    "doanh_so_thang": 28,
    "thi_phan_toyota_pct": 19.2,
    "share_of_dealer_pct": 84.5,
    "cr_cold_to_warm": 0.61,
    "cr_warm_to_hot": 0.47,
    "cr_hot_to_HD": 0.68,
    "cr_cold_to_HD_overall": 0.20,
    "csi_sales": 4.42
  },
  "kpi_per_tvbh": {
    "NV001": {"n_KHTN": 38, "ty_le_chot": 0.08, "cold_to_warm": 0.32},
    "NV004": {"n_KHTN": 52, "ty_le_chot": 0.31, "cold_to_warm": 0.72},
    "...": "..."
  }
}
```

### 7.3 Schema GP history

```json
{
  "ma_GP": "DongNai-2026-04-GP-003",
  "ngay_xuat": "2026-05-05",
  "nhom": "Đào tạo",
  "tinh_huong_playbook": "TH-B01",
  "van_de": "TVBH NV001 CR Cold→Warm 0.32",
  "giai_phap": "Module training + kèm cặp 4 tuần",
  "chu_the": "NV001 + NV017 + Trưởng phòng KD",
  "kpi": {"cold_to_warm": ">=0.55", "ty_le_chot": ">=0.18"},
  "han": "2026-05-31",
  "baseline_kpi": {"cold_to_warm": 0.32, "ty_le_chot": 0.08},
  "reviews": [
    {
      "ngay_review": "2026-05-12",
      "chu_ky": "T+7",
      "% hoan_thanh": 30,
      "blocker": null,
      "note": "Module đã bắt đầu, NV001 dự 2/4 buổi"
    },
    {
      "ngay_review": "2026-06-04",
      "chu_ky": "T+30",
      "kpi_cur": {"cold_to_warm": 0.58, "ty_le_chot": 0.19},
      "verdict": "target_met",
      "action": "Đóng GP, mở GP-003.01 nhân rộng"
    }
  ],
  "trang_thai": "Done",
  "ngay_dong": "2026-06-04"
}
```

---

## 8. Quy tắc bất biến

1. **Mọi GP phải có ≥ 1 ngay_review** — không có review = không có Agentic Loop.
2. **Baseline phải được ghi lại trước khi GP bắt đầu** — Hook H6 enforce.
3. **T+7 không phải cứng — tùy nhóm GP** — quy trình review sớm hơn (T+3 audit).
4. **Mỗi review phải có verdict cụ thể** — không "tạm tốt" cụt.
5. **GP overdue 2 chu kỳ liên tiếp → escalate GĐ ĐL** — không để "treo" vô hạn.
6. **T+90 ROI < 0 → ghi lessons learned công khai** — học từ thất bại quý này.
7. **Không tự động đóng GP nếu KPI mẫu nhỏ** — cần > 30 mẫu để verdict đáng tin.

---

## 9. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| Người đi review T+30 không phải người tạo GP | Đọc gp_history + baseline, không hỏi lại |
| GP có nhiều KPI và lệch verdict | Verdict tổng = verdict của KPI quan trọng nhất (KPI đầu tiên trong target) |
| KPI đo bị missing data | Mở rộng cửa sổ +15d, không kết luận sớm |
| Baseline cũ > 6 tháng | Tính lại baseline từ data thực, không dùng cũ |
| GP ăn hiệu quả từ GP khác (confounding) | Ghi note + giảm trọng số khi tính ROI |
