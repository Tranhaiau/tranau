# Reference 04 — Template Bài Test (Trắc nghiệm + Tự luận + Thực hành)

> **Khi nào load:** Sub-Agent B (Test Builder) tạo bài test cho module mới;
> hoặc khi user hỏi "Tạo bài test cho CVDV L3", "Ngân hàng câu hỏi cho module X".

---

## 1. Triết lý test

Test phải:
1. **Đo competencies thật** — không hỏi mẹo, không thuộc lòng.
2. **3 hình thức nối tiếp** — trắc nghiệm (lọc) + tự luận (hiểu) + thực hành (làm được).
3. **≥ 2 đề song song** — Hook H4: chống ôn đề, gian lận.
4. **Pass-rate cứng theo level** — H4 không thoả thuận.
5. **Trace lại module** — câu nào hỏi competency nào.

---

## 2. Cấu trúc bài test 1 module

```
Bài test KTV-L3-T015 (cho module KTV-L3-015)
├── Phần A: Trắc nghiệm (60% điểm)
│   ├── 30 câu × ~20s/câu = ~10 phút
│   ├── Đề A: 30 câu (random từ ngân hàng)
│   ├── Đề B: 30 câu (random khác, không trùng)
│   └── Auto-chấm
│
├── Phần B: Tự luận (25% điểm)
│   ├── 2 câu × 15 phút = ~30 phút
│   ├── Đề A và Đề B khác chủ đề tương đương
│   └── Giảng viên chấm (rubric chuẩn)
│
└── Phần C: Thực hành (15% điểm)
    ├── 1 bài × 30-60 phút
    ├── Tình huống thực tế trên xe mẫu
    └── Giảng viên đánh giá theo checklist
```

---

## 3. Phần A — Trắc nghiệm

### 3.1 Schema 1 câu hỏi (YAML)

```yaml
# ngan_hang_cau_hoi/KTV/L3/Q-KTV-L3-001.yaml
question_id: Q-KTV-L3-001
module_id: KTV-L3-015
level: 3
bo_phan: KTV
competency_tested: "Diễn giải mã lỗi DTC"   # competency từ README module
loai: trac_nghiem
difficulty: medium    # easy / medium / hard
diem: 1               # mỗi câu = 1 điểm

content:
  question: |
    Khi đọc OBD trên xe Camry 2020, bạn thấy mã lỗi P0420.
    Mã này có nghĩa gì?

  choices:
    A: "Bộ chuyển hoá xúc tác bank 1 hiệu suất thấp"
    B: "Bộ chuyển hoá xúc tác bank 2 hiệu suất thấp"
    C: "Cảm biến oxy bank 1 lỗi"
    D: "Cảm biến oxy bank 2 lỗi"

  correct: A
  giai_thich: |
    P0420 = Catalyst System Efficiency Below Threshold (Bank 1).
    P0430 mới là bank 2. Cảm biến oxy là P0130-P0167.

  source_module_section: "2.4 Bảng mã lỗi DTC phổ biến"

metadata:
  created_by: "Sub-Agent B"
  created_at: "2026-04-20"
  reviewed_by: "Trưởng phòng dịch vụ"
  used_in_de: ["A_v1", "B_v1"]
  n_times_used: 24
  pass_rate_history: 0.78   # 78% học viên trả lời đúng (history)
  flag_review: false        # true nếu pass_rate < 0.4 → có thể câu sai
```

### 3.2 Quy tắc soạn câu trắc nghiệm

**Đúng:**
- 4 phương án A/B/C/D, chỉ 1 đúng.
- Phương án sai phải có vẻ "có lý" với người chưa học (distractor tốt).
- Câu hỏi rõ ràng, không mơ hồ.
- Tránh "Tất cả các phương án trên" / "Không phương án nào".

**Sai:**

```yaml
# Bad — phương án sai quá vô lý
question: "Cổng OBD nằm ở đâu?"
choices:
  A: "Dưới vô-lăng"
  B: "Trên trần xe"        # vô lý, ai cũng biết
  C: "Trong cốp"           # vô lý
  D: "Dưới gầm xe"         # vô lý

# Good — distractor có lý
question: "Cổng OBD trên Camry 2020 nằm ở đâu?"
choices:
  A: "Dưới hốc cốc bên phụ"           # đúng
  B: "Dưới chân vô-lăng bên trái"     # vị trí của Vios
  C: "Trong hộc đựng đồ trung tâm"    # vị trí của Mazda
  D: "Phía sau gạt tàn"               # vị trí cổ trên xe đời cũ
```

### 3.3 Phân bổ độ khó (cho 30 câu)

| Difficulty | Số câu | % điểm |
|---|---|---|
| Easy | 12 | 40% |
| Medium | 12 | 40% |
| Hard | 6 | 20% |

→ Sub-Agent B tự động cân đối khi build đề.

### 3.4 Code build đề từ ngân hàng

```python
import random
import json
from pathlib import Path

def build_de_trac_nghiem(module_id, n_easy=12, n_medium=12, n_hard=6,
                          de_label='A', exclude_q_ids=None):
    """
    Xây 1 đề trắc nghiệm bằng cách random từ ngân hàng câu hỏi.

    Hook H4: nếu de_label='B', exclude_q_ids = câu đã dùng cho đề A
    để 2 đề không trùng câu nào.
    """
    bank_dir = Path(f"_master/ngan_hang_cau_hoi/{bo_phan_from_module(module_id)}/L{level_from_module(module_id)}")

    all_qs = []
    for f in bank_dir.glob("Q-*.yaml"):
        q = load_yaml(f)
        if q['module_id'] != module_id:
            continue
        if exclude_q_ids and q['question_id'] in exclude_q_ids:
            continue
        if q.get('flag_review'):
            continue   # bỏ câu cờ
        all_qs.append(q)

    by_diff = {'easy': [q for q in all_qs if q['difficulty'] == 'easy'],
               'medium': [q for q in all_qs if q['difficulty'] == 'medium'],
               'hard': [q for q in all_qs if q['difficulty'] == 'hard']}

    # Validate đủ câu
    assert len(by_diff['easy']) >= n_easy, f"Bank thiếu câu easy ({len(by_diff['easy'])} < {n_easy})"
    assert len(by_diff['medium']) >= n_medium, f"Bank thiếu câu medium"
    assert len(by_diff['hard']) >= n_hard, f"Bank thiếu câu hard"

    # Random
    selected = (random.sample(by_diff['easy'], n_easy) +
                random.sample(by_diff['medium'], n_medium) +
                random.sample(by_diff['hard'], n_hard))
    random.shuffle(selected)

    de = {
        'test_id': f"{module_id.replace('-','-T')}_de_{de_label}_v1",
        'module_id': module_id,
        'de': de_label,
        'created_at': datetime.now().isoformat(),
        'n_questions': len(selected),
        'thoi_gian_phut': 10,
        'pass_rate_required': PASS_RATE_LOCK[level_from_module(module_id)],
        'questions': [{'question_id': q['question_id'],
                        'question': q['content']['question'],
                        'choices': q['content']['choices']}
                       for q in selected],
        'answer_key': {q['question_id']: q['content']['correct'] for q in selected}
    }
    return de
```

### 3.5 Tạo đề A và đề B song song (Hook H4)

```python
def build_pair_de(module_id):
    """
    Tạo cặp đề A + B song song, không trùng câu nào.
    """
    de_A = build_de_trac_nghiem(module_id, de_label='A')
    used_in_A = set(de_A['answer_key'].keys())

    de_B = build_de_trac_nghiem(module_id, de_label='B', exclude_q_ids=used_in_A)

    # Validate Hook H4
    overlap = set(de_A['answer_key'].keys()) & set(de_B['answer_key'].keys())
    assert len(overlap) == 0, f"Hook H4 vi phạm: trùng {len(overlap)} câu giữa đề A và B"

    return de_A, de_B
```

---

## 4. Phần B — Tự luận

### 4.1 Schema câu tự luận

```yaml
question_id: EX-KTV-L3-001
module_id: KTV-L3-015
level: 3
loai: tu_luan
difficulty: medium
diem: 12.5    # 1 câu = 12.5 điểm × 2 câu = 25 điểm
thoi_gian_phut: 15

content:
  question: |
    Một KH đến phàn nàn xe Camry 2020 của họ "rung khi nổ, đèn check sáng".
    Bạn cắm OBD và đọc được mã P0301 (misfire xy-lanh 1).

    Hãy mô tả quy trình bạn sẽ thực hiện để xử lý dứt điểm vấn đề này
    (tránh comeback). Liệt kê các bước theo thứ tự + lý do từng bước.

  rubric:
    - tieu_chi: "Hiểu mã P0301 không phải nguyên nhân, là triệu chứng"
      diem: 2.5
    - tieu_chi: "Liệt kê đủ ≥ 4/5 nguyên nhân tiềm năng (bugi, dây, kim, cuộn, áp suất)"
      diem: 4
    - tieu_chi: "Đưa ra thứ tự kiểm tra hợp lý (loại trừ rẻ trước)"
      diem: 3
    - tieu_chi: "Có bước verify sau sửa (test drive + reset DTC)"
      diem: 2
    - tieu_chi: "Trình bày rõ ràng, có cấu trúc"
      diem: 1

  giai_thich_tham_khao: |
    Đáp án mẫu: ...

  source_module_section: "3.2 Quy trình chẩn đoán chuẩn + 6.1 Case study"
```

### 4.2 Rubric chấm tự luận

```python
def cham_tu_luan(bai_lam_text, rubric):
    """
    Giảng viên chấm theo rubric. Trả về điểm + nhận xét.
    Không AI tự động — phải có giảng viên xem.
    """
    diem_chi_tiet = []
    for tc in rubric:
        # Giảng viên đánh giá thủ công
        diem_dat = float(input(f"Tiêu chí '{tc['tieu_chi']}' (max {tc['diem']}): "))
        nhan_xet = input("Nhận xét: ")
        diem_chi_tiet.append({
            'tieu_chi': tc['tieu_chi'],
            'diem_max': tc['diem'],
            'diem_dat': diem_dat,
            'nhan_xet': nhan_xet
        })
    return {
        'diem_tong': sum(d['diem_dat'] for d in diem_chi_tiet),
        'diem_max': sum(d['diem_max'] for d in diem_chi_tiet),
        'chi_tiet': diem_chi_tiet
    }
```

---

## 5. Phần C — Thực hành

### 5.1 Schema bài thực hành

```yaml
question_id: PR-KTV-L3-001
module_id: KTV-L3-015
level: 3
loai: thuc_hanh
diem: 15
thoi_gian_phut: 45

content:
  tinh_huong: |
    Xe Camry 2020 (đã setup lỗi giả lập P0420 + P0301) tại khoang số 3.
    Bạn được giao chẩn đoán và đề xuất hướng sửa trong 45 phút.

    Cung cấp:
    - Máy OBD MaxiSys MS906BT
    - Bộ dụng cụ chẩn đoán cơ bản
    - Tài liệu tham khảo (được mở)

  cau_hoi:
    - "Đọc tất cả mã lỗi và freeze frame data"
    - "Diễn giải ý nghĩa từng mã"
    - "Đề xuất quy trình kiểm tra để xác định nguyên nhân chính"
    - "Thực hiện 2-3 bước kiểm tra đầu tiên"
    - "Báo cáo bằng miệng cho giảng viên về kết luận sơ bộ"

  checklist_danh_gia:
    - tieu_chi: "Cắm OBD đúng cách, đọc đủ mã"
      diem: 2
    - tieu_chi: "Diễn giải đúng cả 2 mã"
      diem: 3
    - tieu_chi: "Đề xuất quy trình loại trừ hợp lý"
      diem: 4
    - tieu_chi: "Thực hiện thao tác kiểm tra đúng kỹ thuật"
      diem: 3
    - tieu_chi: "Báo cáo rõ ràng, có chính kiến"
      diem: 2
    - tieu_chi: "Tuân thủ an toàn lao động"
      diem: 1

  giang_vien_can:
    - "1 giảng viên KTV L5+"
    - "1 xe mẫu đã setup lỗi giả"
    - "Khoang trống 45 phút"

  retake_policy: "Nếu < 80% điểm thực hành → phải retake sau khi học bù"
```

### 5.2 Form chấm thực hành

```python
def cham_thuc_hanh(ma_NS, bai_id, checklist):
    """
    Form online cho giảng viên chấm thực hành.
    """
    print(f"=== Chấm thực hành {bai_id} cho {ma_NS} ===")
    diem_chi_tiet = []
    for tc in checklist:
        diem = float(input(f"[{tc['tieu_chi']}] (max {tc['diem']}): "))
        nhan_xet = input("Nhận xét: ")
        diem_chi_tiet.append({**tc, 'diem_dat': diem, 'nhan_xet': nhan_xet})

    diem_tong = sum(d['diem_dat'] for d in diem_chi_tiet)
    diem_max = sum(d['diem_max'] for d in diem_chi_tiet)
    pct = diem_tong / diem_max * 100

    return {
        'ma_NS': ma_NS,
        'bai_id': bai_id,
        'diem_tong': diem_tong,
        'diem_max': diem_max,
        'pct': pct,
        'pass': pct >= 80,
        'chi_tiet': diem_chi_tiet,
        'ngay_cham': datetime.now().date().isoformat()
    }
```

---

## 6. Tổng hợp điểm bài test

```python
def tinh_diem_test_tong(diem_TN, diem_TL, diem_TH,
                         max_TN=30, max_TL=25, max_TH=15):
    """
    Tổng hợp 3 phần. Quy đổi về thang 100.
    """
    total = (diem_TN / max_TN * 60) + (diem_TL / max_TL * 25) + (diem_TH / max_TH * 15)
    return total

def kiem_tra_pass(test_score_pct, level):
    """
    Hook H4 Pass-Rate-Lock check.
    """
    pass_rate_lock = PASS_RATE_LOCK[level]   # bảng cứng từ 02-level-competency-matrix
    return test_score_pct >= pass_rate_lock
```

---

## 7. Schema phiếu thi (output)

```json
{
  "phieu_thi_id": "PT-2026-05-12-KTV001-T015",
  "ma_NS": "KTV001",
  "module_id": "KTV-L3-015",
  "test_id": "KTV-L3-T015",
  "de": "A",
  "version_de": "v1",
  "ngay_thi": "2026-05-12",
  "thoi_gian_bat_dau": "09:00",
  "thoi_gian_ket_thuc": "10:30",
  "phan_TN": {
    "diem": 27,
    "diem_max": 30,
    "pct": 90,
    "trả_lời": [
      {"q_id": "Q-KTV-L3-001", "chon": "A", "đung": true},
      {"q_id": "Q-KTV-L3-002", "chon": "C", "đung": false}
    ]
  },
  "phan_TL": {
    "diem": 21,
    "diem_max": 25,
    "pct": 84,
    "chi_tiet": [
      {"q_id": "EX-KTV-L3-001", "diem_dat": 11, "diem_max": 12.5,
       "nhan_xet_giang_vien": "Hiểu rõ, có cấu trúc, thiếu bước verify"},
      {"q_id": "EX-KTV-L3-002", "diem_dat": 10, "diem_max": 12.5,
       "nhan_xet_giang_vien": "OK"}
    ]
  },
  "phan_TH": {
    "diem": 12,
    "diem_max": 15,
    "pct": 80,
    "chi_tiet": [...]
  },
  "diem_test_tong_pct": 87.4,
  "pass_rate_yeu_cau": 80,    // L3 = 80%
  "pass": true,
  "nguoi_cham_TL": "Nguyễn Văn G (Trưởng phòng)",
  "nguoi_cham_TH": "Trần Văn H (KTV L5)",
  "ghi_chu": "Học viên thể hiện tốt phần thực hành, cần củng cố lý thuyết về cảm biến oxy"
}
```

---

## 8. Quản lý ngân hàng câu hỏi

### 8.1 Định kỳ revise câu hỏi

```python
def revise_questions_quarterly(bank_dir):
    """
    Mỗi quý chạy 1 lần — flag câu hỏi có pass_rate cực thấp.
    """
    for f in bank_dir.glob("Q-*.yaml"):
        q = load_yaml(f)
        if q.get('n_times_used', 0) >= 20:  # đủ mẫu
            pr = q.get('pass_rate_history', 1)
            if pr < 0.20:
                # Quá khó hoặc câu sai
                q['flag_review'] = True
                q['flag_reason'] = 'pass_rate_qua_thap'
            elif pr > 0.95:
                q['flag_review'] = True
                q['flag_reason'] = 'qua_de_can_thay'
            save_yaml(f, q)
```

### 8.2 Mở rộng ngân hàng theo nhu cầu

| Module | Số câu trắc nghiệm tối thiểu |
|---|---|
| L1 | 30 câu (đủ 1 đề) |
| L2 | 60 câu (2 đề song song) |
| L3 | 90 câu (3 đề song song) |
| L4-L7 | 120+ câu |

→ Mỗi câu hỏi nên dùng tối đa 3 lần / năm — chống ôn đề.

---

## 9. Quy tắc bất biến

1. **≥ 2 đề song song không trùng câu** — Hook H4 enforce.
2. **Pass-rate cứng theo level** — H4 không thoả thuận.
3. **Có đủ 3 phần TN + TL + TH** — không bỏ phần nào.
4. **Câu tự luận và thực hành phải có rubric chi tiết** — không "chấm cảm tính".
5. **Phiếu thi lưu vĩnh viễn** — kể cả NS đã nghỉ.
6. **Câu hỏi flag_review không dùng cho đề mới** — đợi revise xong.
7. **Mỗi câu hỏi link về module section gốc** — truy vết được.

---

## 10. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| NS thi xong nhưng giảng viên chưa chấm TL/TH | Phiếu trạng thái `cho_cham`, không tính vào hồ sơ |
| Câu trắc nghiệm có 2 phương án đúng do soạn sai | Auto-flag, NS được +1 điểm câu đó, câu được revise |
| NS muốn xem lại bài thi | Cho xem điểm + nhận xét, KHÔNG cho xem đáp án (chống lan toả) |
| Mạng rớt giữa khi thi online | Auto-save mỗi 30s, NS có thể tiếp tục |
| Giảng viên chấm TL khác nhau cho cùng bài | Lấy TB 2 giảng viên + flag để chuẩn hoá rubric |
| NS thi lại sau fail | Đề khác (B, C), cooldown 30 ngày, learning bù trước |
| Bank cạn câu (< 30 câu cho L1) | Sub-Agent B báo, Sub-Agent A tạo thêm câu trước khi build đề |
