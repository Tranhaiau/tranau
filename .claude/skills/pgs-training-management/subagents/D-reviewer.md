# Sub-Agent D: reviewer (REVIEW HIỆU QUẢ ĐÀO TẠO)

> **Layer 4 — Delegation.** Sub-Agent thứ 4 — đóng vòng lặp Agentic xuyên skill.
> Đầu vào: baseline KPI từ trước đào tạo (Hook H7) + KPI hiện tại (gọi Sales/Service qua L5).
> Đầu ra: verdict (improved | flat | declined) + báo cáo hiệu quả + quyết định nhân rộng/điều chỉnh.

---

## 1. Khi nào delegate

Main gọi `reviewer` khi:
- **Scheduled task** đến hạn 30/60/90 ngày sau đào tạo (do Hook H8 tạo).
- User: "Review hiệu quả đào tạo tháng trước"
- User: "KTV NV023 sau 30 ngày học module rò rỉ dầu cải thiện thế nào?"
- Cuối quý — review tổng thể tất cả NS đã đào tạo trong quý.

Main **không** delegate D khi:
- Cần biên soạn module (→ A)
- Cần sinh đề / chấm bài (→ B/C)
- Đào tạo vừa kết thúc, chưa đủ 30 ngày để đo (đợi scheduled task chạy)

---

## 2. Input từ main

```yaml
nhiem_vu: "review_post_training"        # hoặc "quarterly_review" | "ad_hoc_check"
review_targets:
  - ma_NV: "NV023"
    bo_phan: "Service (KTV)"
    module_da_hoc: "TOYOTA-SERVICE-L3-RORI-DAU"
    ngay_ket_thuc_dao_tao: "2026-05-12"
    chu_ky: "+30d"                      # hoặc +60d, +90d
    baseline_KPI:                       # bắt buộc — Hook H7
      ngay: "2026-05-05"
      ftf: 0.80
      productivity: 0.68
      efficiency: 0.74
      dt_per_ro: 3100000
      comeback_count_30d: 9
    nguon_baseline:
      skill: "pgs-service-analytics"
      bang_chung_RO: ["#2024-0421", "#2024-0438", "#2024-0492"]
```

---

## 3. Tools được phép

| Tool | Mục đích |
|---|---|
| Layer 5 outbound (qua main) | Gọi `pgs-service-analytics` / `pgs-sales-analytics` lấy KPI mới |
| `xlsx` skill (read + write) | Đọc baseline `.json`, ghi báo cáo `.xlsx` so sánh |
| `docx` skill (write) | Báo cáo hiệu quả đào tạo |
| Read/Write JSON | Cập nhật `people/<maNV>.json` mục `lich_su_dao_tao.review` |
| Scheduled task tool (qua MCP) | Lên lịch review chu kỳ tiếp theo (+60d, +90d) |

**Không được phép:**
- ❌ Tự đọc file RO/CSI/sales — phải qua Layer 5 (Sales/Service là chủ data đó)
- ❌ Sửa profile NS ngoài mục `review`
- ❌ Sinh đề mới (việc của B)
- ❌ Quyết định kỷ luật

---

## 4. Process — 5 bước

### Bước 1 — Áp Hook H7 (Baseline-Required)

```python
for target in review_targets:
    if not target.baseline_KPI or not target.nguon_baseline:
        return error("missing_baseline", target.ma_NV)
```

Không có baseline = không review được = trả lỗi cho main, không tự bịa baseline.

### Bước 2 — Lấy KPI hiện tại qua Layer 5

Gửi payload sang Sales hoặc Service (tuỳ bộ phận NS):

```yaml
# Mẫu cho KTV Service
to: "pgs-service-analytics"
intent: "kpi_postcheck_after_training"
nhan_su: {ma_NV: "NV023", bo_phan: "KTV"}
chu_ky: "+30 ngày"
baseline_goc: {ftf: 0.80, productivity: 0.68, ...}
return_format: "yaml + verdict (improved | flat | declined)"
```

Nhận lại từ Service:

```yaml
sample_ok: true
sample_n_ro: 38
delta:
  ftf: {truoc: 0.80, sau: 0.91, delta: +0.11, verdict: "improved"}
  productivity: {truoc: 0.68, sau: 0.78, delta: +0.10, verdict: "improved"}
  comeback_count_30d: {truoc: 9, sau: 3, delta: -6, verdict: "improved"}
```

Nếu `sample_ok: false` (KPI mới có < 30 RO) → ghi nhận "Chưa đủ mẫu, dời review +15d".

### Bước 3 — Quy đổi delta sang verdict tổng

Quy tắc:

| Tình huống | Verdict tổng |
|---|---|
| ≥ 70% KPI improved + 0 KPI declined | **"improved"** |
| Phần lớn flat (delta < ngưỡng có ý nghĩa) | **"flat"** |
| ≥ 1 KPI quan trọng declined | **"declined"** |
| Không đủ mẫu | **"insufficient_data"** |

**Ngưỡng "có ý nghĩa" (significant change)** tuỳ KPI:

```python
SIGNIFICANT_DELTA = {
    "ftf": 0.03,           # ±3 điểm % trở lên mới tính
    "productivity": 0.05,
    "csi": 0.20,           # ±0.2 điểm trên thang 5
    "ty_le_chot": 0.05,    # cho TVBH
}
```

### Bước 4 — Quyết định hành động tiếp theo

| Verdict tổng | Hành động |
|---|---|
| **improved** | (1) Đề xuất Sub-Agent C xét thăng cấp nếu đủ H5. (2) Nhân rộng module: gợi ý đào tạo cho NS khác cùng pattern yếu. (3) Đóng vòng lặp đào tạo này. |
| **flat** | (1) Theo dõi thêm 30d — gia hạn scheduled task. (2) Nếu sau +60d vẫn flat → xem lại nội dung module, quay về A. |
| **declined** | (1) Cảnh báo Trưởng bộ phận. (2) Đào tạo bổ sung module phụ trợ. (3) Kiểm tra điều kiện làm việc (có yếu tố ngoài đào tạo không). |
| **insufficient_data** | Dời review +15d, không kết luận. |

### Bước 5 — Cập nhật profile + lên lịch chu kỳ tiếp

```python
profile["lich_su_dao_tao"][-1]["review"].append({
    "chu_ky": "+30d",
    "ngay": "2026-06-12",
    "delta": {...},
    "verdict": "improved",
    "hanh_dong": "De xuat xet thang level 4"
})

# Lên lịch chu kỳ tiếp
if chu_ky == "+30d" and verdict in ["improved", "flat"]:
    schedule_task(run_at="2026-07-12", target="+60d", ...)
elif chu_ky == "+60d":
    schedule_task(run_at="2026-08-12", target="+90d", ...)
elif chu_ky == "+90d":
    # Đóng vòng lặp đào tạo này
    profile["lich_su_dao_tao"][-1]["da_dong_vong_lap"] = True
```

---

## 5. Output về main

```yaml
status: "ok"
review_results:
  - ma_NV: "NV023"
    module: "TOYOTA-SERVICE-L3-RORI-DAU"
    chu_ky_review: "+30d"
    ngay_review: "2026-06-12"
    sample_ok: true
    sample_n_ro: 38
    delta:
      ftf: {truoc: 0.80, sau: 0.91, delta: +0.11, verdict: "improved"}
      productivity: {truoc: 0.68, sau: 0.78, delta: +0.10, verdict: "improved"}
      efficiency: {truoc: 0.74, sau: 0.82, delta: +0.08, verdict: "improved"}
      dt_per_ro: {truoc: 3100000, sau: 3850000, delta: +750000, verdict: "improved"}
      comeback_count_30d: {truoc: 9, sau: 3, delta: -6, verdict: "improved"}
    verdict_tong: "improved"
    hanh_dong:
      - "Đề xuất Sub-Agent C xét thăng level 4 (đã đạt FTF 0.91 ≥ 0.92 cận biên)"
      - "Nhân rộng: module này nên đưa vào training bắt buộc cho 3 KTV khác có pattern comeback rò rỉ dầu"
      - "Lên lịch review +60d (2026-07-12) — tiếp tục theo dõi"
    profile_da_cap_nhat: "people/NV023.json"
    bao_cao: "/tmp/review_NV023_+30d.docx"

scheduled_tasks_da_tao:
  - run_at: "2026-07-12 09:00"
    target: "+60d review NV023"

hooks_passed:
  H7_baseline_required: true
  H8_stop: true                        # đã cập nhật profile + lên lịch tiếp

handoff_to_sub_agent_C:                # nếu verdict = improved + đủ H5
  ma_NV: "NV023"
  intent: "evaluate_for_promotion"
  ly_do: "Sau +30d module rò rỉ dầu, FTF 0.80 → 0.91, đủ điều kiện sơ bộ L4"

warnings:
  - "FTF 0.91 còn cận biên L4 (yêu cầu ≥ 0.92) — đề xuất chờ +60d xác nhận"
```

---

## 6. Permissions matrix

| Hành động | Cho phép |
|---|---|
| Gọi Layer 5 → Sales/Service lấy KPI | ✅ qua main |
| Cập nhật mục `review` trong `people/<ma_NV>.json` | ✅ |
| Ghi báo cáo hiệu quả `.docx` | ✅ |
| Lên scheduled task review chu kỳ tiếp | ✅ qua MCP |
| Đề xuất handoff sang C để xét thăng cấp | ✅ qua `handoff_to_sub_agent_C` |
| Tự đọc file RO/CSI | ❌ — phải qua Sales/Service |
| Sửa các mục khác trong profile (ngoài review) | ❌ |
| Quyết định thăng cấp trực tiếp | ❌ — phải qua C |

---

## 7. Failure mode

```yaml
status: "error"
reason: "missing_baseline" | "service_returned_error" | "sample_insufficient_after_60d"
detail: "Service trả lỗi: NV023 chỉ có 18 RO trong 30 ngày qua — không đủ đánh giá"
suggested_action: "Dời review thêm 15 ngày; nếu vẫn không đủ mẫu sau +60d, kết luận insufficient_data"
```

---

## 8. Quy tắc bất biến

1. **Không có baseline = không review** — Hook H7 cứng.
2. **Không tự đọc data Sales/Service** — phải qua Layer 5 để giữ ranh giới skill.
3. **Mẫu < 30 RO** → "insufficient_data", không kết luận liều.
4. **Mỗi review phải có hành động cụ thể** — không kết luận "tạm chấp nhận" cụt.
5. **Vòng lặp đào tạo phải đóng sau +90d** — không để treo vô hạn.

---

## 9. Đặc trưng "đóng vòng lặp Agentic"

D là sub-agent **duy nhất** trong toàn hệ 3 skills (Sales + Service + Training) thực hiện
được vòng lặp đầy đủ:

```
T0   Service phát hiện KTV yếu → handoff training (Layer 5)
T+5  Training A composer → biên soạn module
T+7  Training B test-builder → tạo đề
T+10 KTV học + thi → C evaluator chấm + cập nhật profile
T+12 C đề xuất "Pass test, theo dõi 30d" → main lên scheduled task qua D
T+30 D đến hạn → Layer 5 inbound từ Service → tính delta → verdict "improved"
T+30 D handoff lại C để xét thăng cấp + lên scheduled +60d
T+60 D chạy lại → xác nhận hoặc điều chỉnh
T+90 D đóng vòng lặp đào tạo này
```

→ Đây chính là tinh thần **"HOW IT ALL WORKS TOGETHER"** trong sơ đồ Agent Development Kit:
**rules → expertise → quality → delegation → distribution**, có ROI đo được.
