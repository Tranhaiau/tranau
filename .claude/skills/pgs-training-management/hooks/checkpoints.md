# Hooks — Training Management Guardrails

> **Layer 3 — Deterministic. Not AI.** Đặc thù Training: liên quan đến **bản quyền hãng**
> (Toyota/Hyundai/Mazda/Kia) và **quyết định nhân sự** (thăng cấp, đào tạo lại).
> Hooks ở đây là tấm chắn pháp lý + chuẩn nghiệp vụ — không phải gợi ý.

---

## H1 — Copyright-Check · Bản quyền tài liệu hãng

| Mục | Giá trị |
|---|---|
| **Event** | Sau khi `Sub-Agent A composer` biên soạn xong module, trước khi ghi `.docx` |
| **Matcher** | Có ≥1 đoạn trùng > 15 từ liên tiếp với tài liệu nguồn |
| **Command** | Reject — yêu cầu Sub-Agent A paraphrase lại đoạn đó |

**Quy tắc cứng:**
- ≤ 15 từ liên tiếp được phép trích nguyên văn (như quy tắc copyright của Claude).
- ≤ 1 quote nguyên văn trong toàn module (không nhiều quotes ngắn từ cùng nguồn).
- **Bắt buộc** ghi nguồn ở cuối module: `Nguồn: Toyota Service Manual chương X, mục Y, 2024`.
- **Cấm** copy nguyên trang, sơ đồ kỹ thuật, hình ảnh có watermark hãng.

**Cách kiểm tra:**

```python
def check_copyright(module_text, source_text):
    # Sliding window 15 từ
    module_ngrams = set(get_ngrams(module_text, n=15))
    source_ngrams = set(get_ngrams(source_text, n=15))
    overlap = module_ngrams & source_ngrams
    return len(overlap) == 0   # 0 đoạn 15-gram trùng = pass
```

**Pass:** không có đoạn 15-gram trùng + có ghi nguồn.
**Fail:** Reject module — không cho ghi vào `training/brands/...`.

---

## H2 — Module-Tagging · 1 level + 1 bộ phận + 1 TH

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi lưu module vào `training/brands/<brand>/<dept>/L<level>/modules/` |
| **Matcher** | YAML frontmatter của module thiếu hoặc sai tag |
| **Command** | Trả về Sub-Agent A bổ sung |

**Schema YAML bắt buộc của mỗi module `.docx`:**

```yaml
# Trong YAML frontmatter của module
title: "Chẩn đoán rò rỉ dầu động cơ 1.5L"
brand: "toyota"                       # bắt buộc 1 trong: toyota|hyundai|mazda|kia|...
department: "service"                 # bắt buộc 1 trong: service|parts|body-paint|csa
level: 3                              # bắt buộc 1 trong: 1..7
duration_hours: 8                     # số giờ học chuẩn
prerequisites: ["L2-baseline-engine"] # các module phải học trước
learning_objectives:
  - "Nhận diện 5 vị trí rò rỉ dầu phổ biến"
  - "Quy trình kiểm tra trong 30 phút"
  - "Phân biệt rò rỉ với hơi nước ngưng tụ"
practical_evidence:                   # bắt buộc — bằng chứng thực hành cần có
  - "Hoàn thành 3 RO chẩn đoán rò rỉ dầu dưới giám sát L5+"
safety_warnings: ["Mặc đồ bảo hộ khi nâng xe"]
source: "Toyota Service Manual 2024, Ch.5 §3.2"
```

**Cấm trộn:**
- ❌ Module "Toyota + Hyundai" — phải tách thành 2 module riêng.
- ❌ Module "Service + Parts" — phải tách.
- ❌ Module "L3-L4" — phải chọn 1 level (có thể tham chiếu module level kế cận qua `prerequisites`).

**Pass:** YAML đủ và đúng tập giá trị.
**Fail:** Trả Sub-Agent A bổ sung. Không cho lưu file.

---

## H3 — Test-Quality · Chất lượng đề test

| Mục | Giá trị |
|---|---|
| **Event** | Sau khi `Sub-Agent B test-builder` sinh xong đề |
| **Matcher** | Có ≥1 vi phạm chất lượng |
| **Command** | Quay lại sinh lại các câu vi phạm |

**Bảng vi phạm:**

| Vi phạm | Cách phát hiện |
|---|---|
| Câu hỏi trùng nội dung | Cosine similarity > 0.85 giữa 2 câu |
| Đáp án lộ rõ trong câu hỏi | Đáp án xuất hiện nguyên văn trong câu hỏi |
| Đáp án "tất cả đều đúng" / "không đáp án nào đúng" > 5% câu | Lười, không phân biệt năng lực |
| Câu hỏi quá dễ (đáp án hiển nhiên với KTV L1) cho test L4+ | Manual review hoặc keyword check |
| Đáp án sai (mâu thuẫn với module nguồn) | Cross-check đáp án ↔ nội dung module |
| Câu hỏi không có ID hoặc không có nguồn module | Schema check |
| Tỷ lệ trắc nghiệm/tự luận/thực hành lệch 70/20/10 ±5% | Đếm tỷ trọng |

**Pass:** không vi phạm.
**Fail:** Sub-Agent B sinh lại các câu fail. Lặp tối đa 3 lần — sau 3 lần vẫn fail thì escalate cho main báo user.

---

## H4 — Pass-Rate-Lock · Pass rate đúng theo level

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi xuất `.docx` đề thi |
| **Matcher** | `pass_rate` trong YAML đề không khớp bảng cứng |
| **Command** | Tự động cập nhật theo bảng |

**Bảng cứng (không user-config được):**

| Level | Pass rate trắc nghiệm | Pass rate tự luận | Pass rate thực hành |
|---|---|---|---|
| L1 | 70% | 60% | Quan sát có hướng dẫn |
| L2 | 75% | 65% | Hỗ trợ một phần |
| L3 | 80% | 70% | Độc lập với checklist |
| L4 | 80% | 75% | Độc lập + chẩn đoán |
| L5 | 85% | 80% | Độc lập + đào tạo người khác |
| L6 | 90% | 85% | Master craft |
| L7 | 90% | 90% | Master + R&D quy trình |

**Pass:** đề có `pass_rate` đúng bảng.
**Fail:** Tự động sửa, không cần user can thiệp.

---

## H5 — Promotion-Evidence · Không thăng cấp chỉ qua điểm test

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi `Sub-Agent C evaluator` đề xuất "Đủ điều kiện thăng cấp" |
| **Matcher** | Profile NS chỉ có điểm test pass, **thiếu** bằng chứng thực hành |
| **Command** | Đổi đề xuất sang "Cần bổ sung bằng chứng thực hành: …" |

**Bằng chứng thực hành bắt buộc theo level (cho KTV Service):**

| Lên Level | Yêu cầu |
|---|---|
| L1 → L2 | ≥ 50 RO dưới giám sát; ≥ 200 giờ tích lũy |
| L2 → L3 | ≥ 150 RO độc lập (BDĐK + SC cơ bản); FTF cá nhân ≥ 90% |
| L3 → L4 | ≥ 300 RO; ≥ 30 RO chẩn đoán phức tạp; FTF ≥ 92% |
| L4 → L5 | ≥ 500 RO; ≥ 50 RO chẩn đoán phức tạp; FTF ≥ 94%; CSI 'sửa chữa' ≥ 4.3 |
| L5 → L6 | ≥ 800 RO; đã kèm cặp ≥ 2 KTV junior pass |
| L6 → L7 | Đã đóng góp ≥ 1 quy trình cải tiến được áp dụng |

**Cho CVDV:** RO/ngày, CSI 'tư vấn', tỷ lệ đặt hẹn.
**Cho TVBH:** Tỷ lệ chốt, doanh số HĐ, CSI 'mua xe'.
**Cho Parts:** Doanh số PT, tỷ lệ tồn kho lành, độ chính xác chẩn đoán linh kiện.

**Pass:** profile đủ điểm test + đủ bằng chứng theo bảng.
**Fail:** Reject đề xuất thăng cấp. Sub-Agent C ghi vào profile dòng:
```
verdict: "Cần bổ sung: <list các yêu cầu thiếu>"
```

---

## H6 — Safety-First · Module rủi ro phải có cảnh báo

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi xuất module thuộc nhóm rủi ro |
| **Matcher** | Module có keyword rủi ro nhưng thiếu phần `safety_warnings` + checklist |
| **Command** | Sub-Agent A bổ sung trước khi lưu |

**Keyword rủi ro bắt buộc trigger hook:**

```
nâng_xe / cẩu / lift, hệ_thống_điện_cao_áp, túi_khí_airbag,
hệ_thống_xăng / nhiên_liệu, ắc_quy_lithium, hệ_thống_phanh / ABS,
hơi_lạnh / điều_hòa, sơn / dung_môi / hóa_chất,
hàn / mài / cắt, áp_suất_cao
```

**Yêu cầu khi trigger:**
1. Phần `safety_warnings` ≥ 3 cảnh báo cụ thể.
2. Checklist an toàn (PPE, kiểm tra trước, isolate năng lượng, …) gắn ở đầu module.
3. Nêu rõ "Module này yêu cầu giám sát của KTV L5+ khi thực hành lần đầu".

**Pass:** đủ 3 yếu tố.
**Fail:** Trả về Sub-Agent A bổ sung. Không cho ghi file.

---

## H7 — Baseline-Required · Phải có baseline KPI để đo hiệu quả

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi `Sub-Agent D reviewer` lên lịch review 30/60/90 ngày |
| **Matcher** | Profile NS không có baseline KPI ngày bắt đầu đào tạo |
| **Command** | Lùi lịch review — yêu cầu lấy baseline trước |

**Vì sao quan trọng:** không có baseline = không đo được hiệu quả = lãng phí đào tạo.

**Baseline phải có:**

```yaml
ma_NV: "NV023"
bo_phan: "Service (KTV)"
ngay_bat_dau_dao_tao: "2026-05-05"
baseline_KPI:
  ftf: 0.80
  productivity: 0.68
  efficiency: 0.74
  dt_per_ro: 3100000
  comeback_count_30d: 9
  csi_thanh_phan_lien_quan: 4.10
nguon_baseline:
  skill: "pgs-service-analytics"
  truy_van: "ro-analyzer filter ma_KTV=NV023, kỳ T0-30 → T0"
  bang_chung_RO: ["#2024-0421", "#2024-0438", "#2024-0492"]
```

**Pass:** baseline đầy đủ + nguồn trace được.
**Fail:** Sub-Agent D **không** lên lịch review — main phải gọi service/sales lấy baseline trước. Đây là ràng buộc cứng của vòng lặp Agentic xuyên skill.

---

## H8 — Stop · Lưu profile + scheduled review

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi kết thúc phiên làm việc |
| **Matcher** | Có ≥1 NS đã hoàn thành test/đào tạo trong phiên |
| **Command** | (1) Cập nhật `people/<maNS>.json` (2) Tạo scheduled task +30/+60/+90 ngày qua MCP |

**Schema `people/<maNS>.json`:**

```json
{
  "ma_NV": "NV023",
  "ten": "Phạm Văn E",
  "bo_phan": "Service (KTV)",
  "TH_chuyen": "Toyota",
  "level_hien_tai": 3,
  "ngay_len_level_hien_tai": "2024-08-15",
  "lich_su_test": [
    {
      "ngay": "2026-05-12",
      "module_id": "TOYOTA-SERVICE-L3-RORI-DAU",
      "loai": "trac_nghiem+tu_luan+thuc_hanh",
      "diem": {"trac_nghiem": 0.84, "tu_luan": 0.78, "thuc_hanh": "pass"},
      "verdict": "pass"
    }
  ],
  "lich_su_dao_tao": [
    {
      "ngay_bat_dau": "2026-05-05",
      "ngay_ket_thuc": "2026-05-12",
      "module": "TOYOTA-SERVICE-L3-RORI-DAU",
      "ly_do": "FTF 80% < TB team 92%, comeback rò rỉ dầu",
      "baseline_KPI": {"ftf": 0.80, "productivity": 0.68},
      "nguon_handoff": "pgs-service-analytics"
    }
  ],
  "lich_review_da_len":
    [
      {"ngay": "2026-06-12", "chu_ky": "+30d", "trang_thai": "scheduled"},
      {"ngay": "2026-07-12", "chu_ky": "+60d", "trang_thai": "scheduled"},
      {"ngay": "2026-08-12", "chu_ky": "+90d", "trang_thai": "scheduled"}
    ]
}
```

**Mẫu scheduled task:**

```
Title: "Review +30d KPI sau đào tạo — NV023 — module TOYOTA-SERVICE-L3-RORI-DAU"
Run at: 2026-06-12 09:00
Prompt:
  Gọi pgs-service-analytics với intent kpi_postcheck_after_training.
  Truyền ma_NV=NV023, baseline_goc đính kèm trong people/NV023.json.
  Nhận lại verdict (improved | flat | declined).
  Cập nhật profile NV023.lich_su_dao_tao + ghi reviews/.
  Nếu improved + đủ bằng chứng thực hành (Hook H5) → đề xuất xét thăng level.
  Nếu declined → đề xuất đào tạo bổ sung module liên quan.
```

**Pass:** profile đã cập nhật + 3 task đã tạo.
**Fail:** Vi phạm vòng lặp Agentic — đào tạo không có review = không đo được ROI.

---

## Tóm tắt thứ tự thực thi (theo từng Sub-Agent)

```
[Sub-Agent A composer biên soạn module]
      ↓
   H1 Copyright-Check         → reject nếu trùng > 15 từ
      ↓
   H2 Module-Tagging          → 1 level + 1 bộ phận + 1 TH
      ↓
   H6 Safety-First            → cảnh báo + checklist nếu rủi ro
      ↓
[Lưu module vào training/brands/...]


[Sub-Agent B test-builder sinh đề]
      ↓
   H3 Test-Quality            → kiểm trùng, đáp án lộ, …
      ↓
   H4 Pass-Rate-Lock          → đúng theo bảng level
      ↓
[Lưu đề + đáp án vào tests/]


[Sub-Agent C evaluator chấm + đề xuất]
      ↓
   H5 Promotion-Evidence      → bằng chứng thực hành đủ chưa
      ↓
[Cập nhật profile NS]


[Sub-Agent D reviewer lên lịch review]
      ↓
   H7 Baseline-Required       → phải có baseline KPI
      ↓
   H8 Stop                    → tạo scheduled task +30/+60/+90d
      ↓
[END]
```

**So với Sales/Service**, Training có:
- **H1 Copyright** — đặc trưng (xử lý tài liệu hãng).
- **H4 Pass-Rate-Lock** — deterministic theo bảng cứng.
- **H5 Promotion-Evidence** — chống thăng cấp ép.
- **H6 Safety-First** — đặc trưng nội dung kỹ thuật.
- **H7 Baseline-Required** — ràng buộc cứng vòng lặp xuyên skill.
