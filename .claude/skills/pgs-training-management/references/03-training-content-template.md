# Reference 03 — Template Biên soạn Module Đào tạo

> **Khi nào load:** Sub-Agent A (Composer) bắt đầu biên soạn module mới từ tài liệu hãng;
> hoặc khi user yêu cầu "biên soạn module X từ tài liệu Y", "tạo bài giảng từ PDF hãng".

---

## 1. Triết lý biên soạn

Biên soạn module ≠ copy tài liệu hãng. Phải:
1. **Paraphrase 100%** — Hook H1 Copyright chặn ≥ 15 từ liên tiếp nguyên văn.
2. **Đơn giản hoá** — tài liệu hãng tiếng Anh / quá kỹ thuật → dễ hiểu cho NS Việt Nam level tương ứng.
3. **Bổ sung context PGS** — quy trình thực tế của đại lý, không chỉ lý thuyết hãng.
4. **Có hands-on** — không chỉ lý thuyết, phải có thực hành / case study.
5. **Truy vết nguồn** — mỗi đoạn phải biết lấy từ trang nào của tài liệu nào.

---

## 2. Workflow biên soạn 1 module (Sub-Agent A)

```
Input: tài liệu hãng (PDF/Word/PPT) + module_id target (vd KTV-L3-015)
   │
   ├─ Step 1: Đọc tài liệu hãng → outline raw
   │
   ├─ Step 2: Map outline → competencies của level (xem 02-level-competency-matrix)
   │
   ├─ Step 3: Tạo cấu trúc module theo template (mục 3)
   │
   ├─ Step 4: Paraphrase từng section (Hook H1 check)
   │
   ├─ Step 5: Bổ sung context PGS (quy trình, ví dụ thực)
   │
   ├─ Step 6: Tạo handouts + thực hành
   │
   ├─ Step 7: Tự kiểm tra Hook H1 (≤ 15 từ liên tiếp)
   │
   └─ Output: thư mục module hoàn chỉnh + suggested_handoff sang Sub-Agent B (test)
```

---

## 3. Template cấu trúc module

### 3.1 README.md (metadata) — chuẩn mục 4.1 của 01-folder-structure.md

### 3.2 content.md outline chuẩn

```markdown
# <Tên module>

## 0. Mục đích & Đối tượng
- **Module này giải quyết vấn đề gì:** ...
- **Đối tượng học:** <bộ phận> Level <X>
- **Sau khi học, học viên có thể:** (5-7 competencies cụ thể, đo lường được)
  - [ ] Năng lực 1
  - [ ] Năng lực 2
  - ...

## 1. Tổng quan
[Giới thiệu chủ đề ở mức độ phù hợp level]

## 2. Lý thuyết
[Chia 3-5 section nhỏ, mỗi section ≤ 2 trang]
### 2.1 ...
### 2.2 ...

## 3. Quy trình PGS chuẩn
[Bước-by-bước quy trình thực hiện tại đại lý PGS, có thể khác hơi tài liệu hãng]
### 3.1 Bước 1: ...
### 3.2 Bước 2: ...

## 4. Sai lầm thường gặp
[3-5 sai lầm phổ biến + cách phòng tránh]

## 5. Hands-on / Thực hành
[Bài tập cụ thể, có thể đo lường]
### 5.1 Bài tập 1: ...
### 5.2 Bài tập 2: ...

## 6. Case study
[1-2 case thực tế từ lịch sử PGS, ẩn danh thông tin KH]

## 7. FAQ
[Câu hỏi học viên thường gặp + trả lời]

## 8. Tài liệu tham khảo thêm
[Link đến module liên quan + tài liệu hãng]

## 9. Đánh giá
- **Bài test:** <mã test ID, vd KTV-L3-T015>
- **Pass-rate yêu cầu:** <theo level, vd L3 = 80%>
- **Thực hành đánh giá bởi:** <chức danh>

---
**Nguồn biên soạn:**
- [ ] <tài liệu 1>, trang <X-Y>
- [ ] <tài liệu 2>, trang <X-Y>

**Hook H1 Copyright check:** PASS (đã quét ≤ 15 từ liên tiếp).
```

### 3.3 _changelog.md template (đã có ở 01-folder-structure)

### 3.4 source_links.md template (đã có ở 01-folder-structure)

---

## 4. Template paraphrase (Hook H1)

### 4.1 Quy tắc paraphrase

**Bad (vi phạm Hook H1):**

```
> Tài liệu hãng (Toyota Manual, p.12):
> "When connecting the OBD-II scan tool, ensure that the ignition is in the ON position
> but the engine is not running. The OBD-II port is located beneath the steering wheel..."

> Bài giảng (sai — copy 22 từ liên tiếp):
> "Khi kết nối máy OBD, hãy đảm bảo công tắc ở vị trí ON nhưng động cơ không chạy.
> Cổng OBD-II nằm dưới vô-lăng..."
```

→ Vi phạm: dịch từng từ, vẫn coi là quote.

**Good (paraphrase đúng):**

```
> Bài giảng (đúng — diễn đạt lại):
> Trước khi cắm máy OBD, KTV phải bật chìa khoá đến vị trí ON (nhưng KHÔNG nổ máy).
> Trên hầu hết xe Toyota, cổng OBD nằm ở khu vực chân vô-lăng phía dưới — xem
> hình minh hoạ images/obd_position.jpg.
>
> Lưu ý PGS: nếu xe Vios trước 2018, cổng có thể bị che bởi panel nhựa,
> phải tháo nhẹ trước khi tiếp cận.
>
> [Nguồn: Toyota Manual p.12, đã paraphrase + bổ sung context PGS]
```

### 4.2 Code check Hook H1

```python
def check_copyright_violation(content_text, source_text, max_consecutive_words=15):
    """
    Check xem có đoạn nào ≥ max_consecutive_words từ liên tiếp giống nguồn.
    Return: (pass: bool, violations: list)
    """
    import re

    def normalize(text):
        # Bỏ punctuation, lowercase, collapse whitespace
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return ' '.join(text.split())

    content_norm = normalize(content_text)
    source_norm = normalize(source_text)

    content_words = content_norm.split()
    violations = []

    for i in range(len(content_words) - max_consecutive_words + 1):
        window = ' '.join(content_words[i:i + max_consecutive_words])
        if window in source_norm:
            violations.append({
                'position': i,
                'text': window,
                'length_words': max_consecutive_words
            })

    return len(violations) == 0, violations
```

### 4.3 Whitelist (cho phép giống nguồn)

Một số đoạn được phép giống nguồn:
- **Mã lỗi DTC:** "P0420" không thể paraphrase.
- **Tên phụ tùng đặc biệt:** "Throttle Position Sensor (TPS)" — giữ nguyên.
- **Mô-men xoắn chuẩn:** "10.5 N·m ± 0.5" — số liệu cứng.
- **Câu lệnh / mã code:** giữ nguyên.

```python
WHITELIST_PATTERNS = [
    r'P\d{4}',                           # mã lỗi DTC
    r'\d+\.?\d*\s*N[·.]m',              # mô-men xoắn
    r'\d+\.?\d*\s*kg/cm[2²]',           # áp suất
    r'(SAE\s+\d+W-\d+|0W-\d+|\d+W-\d+)' # tiêu chuẩn dầu
]
```

---

## 5. Bổ sung context PGS

Mỗi section nên có ít nhất 1 đoạn "Lưu ý PGS" — chú thích thực tế đại lý:

```markdown
## 2.3 Vị trí cổng OBD theo từng dòng xe

[Bảng từ tài liệu hãng]

> **🚗 Lưu ý PGS Đồng Nai:**
> Trong nửa đầu năm 2026, ~40% xe Vios đời 2017-2019 vào xưởng có cổng OBD bị che
> bởi panel nhựa. KTV cần tháo panel theo quy trình KTV-L2-008 trước khi cắm máy.
> Tránh dùng vật cứng cạy → trầy xước nội thất → CSI giảm.
```

---

## 6. Hands-on template

### 6.1 Bài tập đo lường được

```markdown
## 5.1 Bài tập 1: Đọc & diễn giải mã lỗi DTC

**Tình huống:** Xe Camry 2020 vào xưởng với triệu chứng "đèn check engine sáng,
không có triệu chứng khác".

**Yêu cầu:**
1. Học viên cắm máy OBD và đọc mã lỗi (15 phút).
2. Ghi lại tất cả mã lỗi (lưu trữ + tạm thời) vào `bai_tap_template.docx`.
3. Diễn giải ý nghĩa từng mã (tham khảo bảng ma_loi_DTC.pdf).
4. Đề xuất bước kiểm tra tiếp theo.

**Tiêu chí đánh giá:**
- ✓ Đọc đúng mã (auto-check bằng máy OBD).
- ✓ Diễn giải đúng ≥ 3/4 mã.
- ✓ Đề xuất bước kiểm tra hợp lý (đánh giá bởi giảng viên).

**Thời gian:** 30 phút.
**Người chấm:** Giảng viên (KTV L5+).
```

### 6.2 Tránh bài tập "đọc bài rồi viết tóm tắt"

Bài tập kém hiệu quả:
- "Tóm tắt nội dung mục 2"
- "Liệt kê 5 điểm chính"

Bài tập tốt:
- "Cho tình huống X, em sẽ làm gì?"
- "Phân tích lỗi Y trong xe mẫu"
- "Thực hiện thao tác Z trong 15 phút"

---

## 7. Case study template

```markdown
## 6.1 Case study 1: Sai chẩn đoán → comeback

**Bối cảnh (ẩn danh):**
- Xe Innova 2021, KH gọi báo "máy nổ rung và đèn check sáng".
- KTV001 đọc OBD: P0301 (misfire xy-lanh 1).
- KTV001 sửa: thay bugi xy-lanh 1 → KH ra về.
- 5 ngày sau KH quay lại với cùng triệu chứng.

**Phân tích:**
- KTV001 đã xử lý hệ quả (misfire) chứ không phải nguyên nhân.
- Mã P0301 có thể do: bugi, dây cao áp, kim phun, cuộn cao áp, áp suất nén.
- Quy trình chẩn đoán chuẩn yêu cầu loại trừ từng nguyên nhân, không phải sửa cái đầu tiên nghĩ đến.

**Bài học:**
- Mã DTC chỉ ra triệu chứng, không phải nguyên nhân.
- Quy trình phải kiểm tra cả 5 yếu tố theo thứ tự (xem mục 3.2).
- Test drive sau sửa để verify trước khi giao xe.

**Kết quả sau training:**
- KTV001 sau khi học module này, comeback rate giảm từ 11% → 5% trong 30 ngày.
```

---

## 8. FAQ template

Sub-Agent A nên thu thập câu hỏi học viên thường gặp từ:
- Kết quả thi (câu sai nhiều = học viên hay nhầm).
- Phản hồi sau buổi học.
- Forum nội bộ / Slack.

```markdown
## 7. FAQ

**Q1: Mã P0420 và P0430 khác nhau thế nào?**
A: P0420 là hiệu suất bộ chuyển hoá xúc tác bank 1 thấp; P0430 là bank 2.
Trên xe V-engine có 2 bộ catalytic, mỗi bank có mã riêng. Trên I-engine chỉ có P0420.

**Q2: Nếu OBD đọc không có mã nhưng KH vẫn báo có triệu chứng?**
A: Có 3 khả năng: (1) Lỗi tạm thời chưa lưu, (2) Lỗi không thuộc hệ thống OBD giám sát
(vd hệ thống treo), (3) KH cảm nhận chủ quan. Quy trình: test drive cùng KH để xác nhận
triệu chứng + reset DTC + chạy lại 50km xem có lưu mã không.
```

---

## 9. Sub-Agent A workflow output

```yaml
# output sau khi composer xong 1 module
module_id: KTV-L3-015
status: draft
ngay_tao: 2026-04-15

files_created:
  - modules/KTV/L3/KTV-L3-015_chan_doan_OBD_nang_cao/README.md
  - modules/KTV/L3/KTV-L3-015_chan_doan_OBD_nang_cao/content.md
  - modules/KTV/L3/KTV-L3-015_chan_doan_OBD_nang_cao/source_links.md
  - modules/KTV/L3/KTV-L3-015_chan_doan_OBD_nang_cao/handouts/checklist_chan_doan.pdf
  - modules/KTV/L3/KTV-L3-015_chan_doan_OBD_nang_cao/handouts/bang_ma_loi_OBD.pdf

hook_h1_check: PASS
  - n_violations: 0
  - max_consecutive_words_found: 11
  - whitelist_matches: 18 (mã DTC + N·m + tiêu chuẩn dầu)

handoff_internal:
  - to: Sub-Agent B (Test Builder)
    payload:
      module_id: KTV-L3-015
      pass_rate_required: 80   # L3 = 80%
      n_questions_min: 30      # ≥30 câu trắc nghiệm
      n_essay_min: 2           # ≥2 câu tự luận
      n_practice_min: 1        # ≥1 bài thực hành
      competencies: [list từ README]

review_required_by: Trưởng phòng dịch vụ
review_deadline: 2026-04-22
```

---

## 10. Quy tắc bất biến

1. **Paraphrase ≤ 15 từ liên tiếp** — Hook H1 chặn cứng.
2. **Mọi module có source_links.md** — truy vết nguồn.
3. **Có ít nhất 1 hands-on + 1 case study** — không lý thuyết suông.
4. **README có YAML frontmatter đầy đủ** — Sub-Agent A enforce.
5. **Module draft phải pass Trưởng phòng review** — không tự động active.
6. **Có handoff sang Sub-Agent B** — module nào cũng phải có test.
7. **Bổ sung context PGS** — không chỉ copy lý thuyết hãng.

---

## 11. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| Tài liệu hãng tiếng Anh, NS không đọc được | Sub-Agent A dịch + paraphrase trong content.md |
| Tài liệu hãng có nhiều ảnh độc quyền | Vẽ lại sơ đồ tương đương, không screenshot |
| Module yêu cầu thiết bị không có ở đại lý | Sub-Agent A flag, không tạo module mà liên hệ trưởng phòng |
| Hãng cập nhật tài liệu giữa lúc biên soạn | Pause, đợi tài liệu mới, không trộn 2 version |
| 1 module quá dài (> 50 trang) | Tách thành 2-3 module nhỏ, có prerequisites lẫn nhau |
| Tài liệu có ngôn ngữ phức tạp (legal/technical) | Paraphrase đơn giản hoá theo level học viên |
| Học viên phản hồi module khó | Sub-Agent D ghi nhận, Sub-Agent A revise version mới |
