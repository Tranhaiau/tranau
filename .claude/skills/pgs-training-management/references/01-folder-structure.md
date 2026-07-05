# Reference 01 — Cấu trúc Thư mục & Convention Đặt tên

> **Khi nào load:** Sub-Agent A (Composer) bắt đầu biên soạn module mới, cần biết
> đặt file ở đâu; hoặc khi user hỏi "Tài liệu Toyota Vios để ở đâu", "Đặt tên module thế nào".

---

## 1. Triết lý tổ chức

Tài liệu đào tạo PGS phải được tổ chức để:
1. **Tìm nhanh** — biết module ABC ở đâu trong < 10s.
2. **Truy vết nguồn** — mỗi module biên soạn từ tài liệu hãng nào, version nào.
3. **Phân quyền rõ** — KTV chỉ thấy module dành cho mình, không lẫn module CVDV.
4. **Dễ cập nhật** — hãng update tài liệu → re-compose module nhanh.
5. **Versioning** — biết module v1 vs v2 khác gì.

---

## 2. Cấu trúc thư mục gốc

```
training_root/
├── _master/                          ← Master data, không thuộc module nào
│   ├── nhan_su_master.xlsx
│   ├── module_master.xlsx
│   ├── thi_master.xlsx
│   ├── giang_vien_master.xlsx
│   └── ngan_hang_cau_hoi/
│       ├── KTV/
│       ├── PT/
│       ├── DS/
│       └── CVDV/
│
├── _hang_source/                     ← Tài liệu nguyên bản từ hãng (read-only)
│   ├── toyota/
│   │   ├── 2024/
│   │   │   ├── vios_repair_manual_v3.pdf
│   │   │   ├── corolla_cross_quick_ref_v1.pdf
│   │   │   └── ...
│   │   └── 2026/
│   ├── hyundai/
│   ├── mazda/
│   └── kia/
│
├── modules/                          ← Module đã biên soạn xong (output Sub-Agent A)
│   ├── KTV/
│   │   ├── L1/                       ← Theo level
│   │   │   ├── KTV-L1-001_quy_trinh_tiep_nhan/
│   │   │   ├── KTV-L1-002_an_toan_co_ban/
│   │   │   └── ...
│   │   ├── L2/
│   │   ├── L3/
│   │   └── ...
│   ├── PT/
│   ├── DS/
│   └── CVDV/
│
├── tests/                            ← Bài test (output Sub-Agent B)
│   ├── KTV/
│   │   ├── L2/
│   │   │   ├── KTV-L2-T001_quy_trinh_chan_doan_de_A.json
│   │   │   ├── KTV-L2-T001_quy_trinh_chan_doan_de_B.json
│   │   │   └── ...
│   │   └── ...
│   └── ...
│
├── evaluations/                      ← Đánh giá thực hiện (output Sub-Agent C)
│   ├── 2026-Q2/
│   │   ├── KTV001_DongNai_2026-05.json
│   │   └── ...
│   └── ...
│
├── reviews/                          ← Review +30/+60/+90 (output Sub-Agent D)
│   ├── 2026-Q2/
│   │   ├── KTV001_DongNai_GP-S-007_T30.json
│   │   ├── KTV001_DongNai_GP-S-007_T60.json
│   │   └── ...
│   └── ...
│
└── archive/                          ← Module/test cũ đã thay thế
    └── 2025/
```

---

## 3. Naming convention

### 3.1 Module ID

```
<BO_PHAN>-L<LEVEL>-<SEQ>_<ten_short>

Ví dụ:
- KTV-L1-001_quy_trinh_tiep_nhan
- KTV-L3-015_chan_doan_OBD_nang_cao
- CVDV-L2-007_xu_ly_phan_nan_KH
- PT-L4-003_quan_ly_kho_an_toan
- DS-L2-009_pha_son_chinh_xac
```

**Quy tắc:**
- BO_PHAN: `KTV` / `PT` / `DS` / `CVDV` (4 phòng).
- LEVEL: `L1` → `L7` (7 bậc).
- SEQ: 3 chữ số (001-999), unique trong mỗi (BO_PHAN, LEVEL).
- ten_short: snake_case Vietnamese không dấu, ≤ 40 ký tự.

### 3.2 Test ID

```
<MODULE_ID>_<de>_v<version>

Ví dụ:
- KTV-L3-015_de_A_v1.json
- KTV-L3-015_de_B_v1.json    (đề song song, Hook H4 Pass-Rate-Lock)
- KTV-L3-015_de_A_v2.json    (sửa lỗi, version mới)
```

### 3.3 Evaluation file

```
<ma_NS>_<chi_nhanh>_<YYYY-MM>.json

Ví dụ:
- KTV001_DongNai_2026-05.json
- CVDV004_LongKhanh_2026-05.json
```

### 3.4 Review file

```
<ma_NS>_<chi_nhanh>_<ma_GP>_T<chu_ky>.json

Ví dụ:
- KTV001_DongNai_GP-S-007_T30.json
- KTV001_DongNai_GP-S-007_T60.json
- KTV001_DongNai_GP-S-007_T90.json
```

---

## 4. Cấu trúc bên trong 1 module

```
modules/KTV/L3/KTV-L3-015_chan_doan_OBD_nang_cao/
├── README.md                         ← metadata + outline
├── content.md                        ← nội dung chính (text + ảnh embed)
├── slides.pptx                       ← slide trình chiếu (optional)
├── handouts/
│   ├── checklist_chan_doan.pdf
│   └── bang_ma_loi_OBD.pdf
├── images/
│   ├── obd_connector_position.jpg
│   └── ...
├── videos/                           ← link YouTube/Vimeo private (không lưu file lớn)
│   └── _link_videos.md
├── source_links.md                   ← link đến _hang_source/ đã dùng
└── _changelog.md                     ← lịch sử version
```

### 4.1 README.md template

```yaml
---
module_id: KTV-L3-015
title: "Chẩn đoán OBD nâng cao"
bo_phan: KTV
level: 3
version: "1.0"
ngay_bien_soan: "2026-04-15"
nguoi_bien_soan: "Sub-Agent A (Composer)"
nguoi_review_lan_cuoi: "Trưởng phòng dịch vụ"
ngay_review_cuoi: "2026-04-20"
trang_thai: "active"   # draft / active / archived

thoi_luong_du_kien_h: 6
hinh_thuc:
  - "ly_thuyet": 2h
  - "thuc_hanh": 4h
hoc_phi_noi_bo: 0     # nội bộ thường free

prerequisites:
  - "KTV-L2-008_doc_ban_ve_ma_xe"
  - "KTV-L2-012_su_dung_dong_ho_van_nang"

competencies:
  - "Sử dụng máy OBD đúng cách"
  - "Đọc và diễn giải mã lỗi DTC"
  - "Phân biệt mã lỗi tạm thời vs cố hữu"
  - "Truy vết nguyên nhân từ mã lỗi"

source_documents:
  - path: "_hang_source/toyota/2024/obd_diagnostic_manual_v3.pdf"
    pages_used: [12, 13, 14, 18, 19, 25-30]
  - path: "_hang_source/hyundai/2024/dtc_master_list.pdf"
    pages_used: [5-8]
---

## Outline
1. Giới thiệu OBD-II và lịch sử
2. Cấu tạo và vị trí cổng OBD theo từng dòng xe
3. ...

## Lưu ý quan trọng
- Module này chỉ dành cho KTV đã có chứng nhận L2.
- Phải làm bài test KTV-L3-T015 đạt ≥ 80% mới được thực hành.
```

### 4.2 content.md template

```markdown
# Chẩn đoán OBD nâng cao

## 1. Giới thiệu OBD-II

[paraphrase từ tài liệu hãng — KHÔNG copy nguyên ≥ 15 từ liên tiếp]

OBD-II (On-Board Diagnostics II) là chuẩn chẩn đoán...

> 🔍 **Lưu ý paraphrase:** Hook H1 Copyright kiểm tra ≤ 15 từ liên tiếp nguyên văn.
> Mọi đoạn trích dài hơn phải paraphrase + dẫn nguồn.

**Nguồn:** Toyota OBD Diagnostic Manual v3, p.12-13.

---

## 2. Cấu tạo cổng OBD

[Hình ảnh `images/obd_connector_position.jpg`]

Cổng OBD có 16 chân...

### 2.1 Vị trí cổng theo từng dòng xe Toyota

| Dòng xe | Vị trí cổng OBD |
|---|---|
| Vios (2014-2024) | Dưới vô-lăng bên trái |
| Camry (2015-2024) | Dưới hốc cốc bên phụ |
| ... | ... |

**Nguồn:** Toyota OBD Diagnostic Manual v3, p.18-19.

---

## 3. Quy trình chẩn đoán chuẩn

```
Bước 1: Kết nối máy OBD vào cổng (đảm bảo xe ở vị trí ON)
Bước 2: Khởi động máy OBD và chọn năm/dòng xe
Bước 3: Đọc tất cả mã lỗi (DTC) — cả lưu trữ và tạm thời
Bước 4: Ghi chép mã + freeze frame data
Bước 5: ...
```

[và tiếp tục]
```

### 4.3 source_links.md (truy vết nguồn)

```markdown
# Tài liệu nguồn đã dùng

## Toyota OBD Diagnostic Manual v3 (PDF)
- Path: `_hang_source/toyota/2024/obd_diagnostic_manual_v3.pdf`
- Trang đã trích/paraphrase: 12, 13, 14, 18, 19, 25-30
- Ngày kiểm tra license: 2026-04-15
- Ghi chú: tài liệu nội bộ Toyota Việt Nam, dùng cho training nội bộ PGS

## Hyundai DTC Master List
- Path: `_hang_source/hyundai/2024/dtc_master_list.pdf`
- Trang đã trích: 5-8
- Đã paraphrase 100%, không quote nguyên văn.

## Lưu ý
- Hook H1 Copyright đã chạy: PASS.
- Không có đoạn nào > 15 từ liên tiếp nguyên văn từ source.
```

---

## 5. Master files

### 5.1 nhan_su_master.xlsx

| Cột | Kiểu | Mô tả |
|---|---|---|
| `ma_NS` | string | unique (KTV001, CVDV004, PT012, DS003) |
| `ten` | string | |
| `chi_nhanh` | string | |
| `bo_phan` | enum | KTV/PT/DS/CVDV |
| `level_hien_tai` | int | 1-7 |
| `ngay_dat_level` | date | ngày lên level hiện tại |
| `target_level_quy_nay` | int | mục tiêu |
| `ngay_vao_PGS` | date | thâm niên |
| `trang_thai` | enum | active/nghi_phep/nghi_om/da_nghi |
| `quan_ly_truc_tiep` | string | tên/mã trưởng phòng |
| `ghi_chu` | string | |

### 5.2 module_master.xlsx

| Cột | Mô tả |
|---|---|
| `module_id` | unique |
| `title` | |
| `bo_phan` | KTV/PT/DS/CVDV |
| `level` | 1-7 |
| `version` | hiện tại |
| `trang_thai` | active/draft/archived |
| `ngay_cap_nhat_cuoi` | |
| `n_mat_test` | số đề test có sẵn |
| `prerequisites` | list module_id phải hoàn thành trước |

### 5.3 thi_master.xlsx (đã thi)

| Cột | Mô tả |
|---|---|
| `phieu_thi_id` | unique |
| `ma_NS` | thi sinh |
| `module_id` | |
| `de` | A/B/C |
| `version_de` | |
| `ngay_thi` | |
| `diem` | |
| `pass_fail` | |
| `nguoi_cham` | trắc nghiệm = auto, tự luận/thực hành = giảng viên |
| `note` | |

### 5.4 ngan_hang_cau_hoi/

Mỗi câu hỏi 1 file YAML/JSON:

```
ngan_hang_cau_hoi/KTV/L3/
├── Q-KTV-L3-001.yaml          # 1 câu trắc nghiệm
├── Q-KTV-L3-002.yaml
├── ...
├── EX-KTV-L3-001.yaml         # bài tự luận
├── PR-KTV-L3-001.yaml         # bài thực hành
└── ...
```

Schema chi tiết xem `04-test-template.md`.

---

## 6. Permissions & Access

### 6.1 Read access

| Vai trò | Có thể đọc |
|---|---|
| KTV | Module bộ phận KTV của level mình + level dưới |
| CVDV | Module CVDV của level mình + level dưới |
| Tổ trưởng | Toàn bộ module bộ phận mình quản lý |
| Trưởng phòng | Toàn bộ module bộ phận mình + reports |
| GĐ ĐL | Toàn bộ |

### 6.2 Write access

| Vai trò | Có thể ghi |
|---|---|
| Sub-Agent A | `modules/` (tạo/cập nhật module) |
| Sub-Agent B | `tests/`, `_master/ngan_hang_cau_hoi/` |
| Sub-Agent C | `evaluations/` |
| Sub-Agent D | `reviews/` |
| Trưởng phòng | Approve/reject module trước khi `trang_thai = active` |
| Hệ thống | `archive/` (auto-move khi version mới) |

---

## 7. Versioning

### 7.1 Khi nào lên version mới

- Module: lên `+0.1` khi sửa nội dung nhỏ; `+1.0` khi đổi outline lớn.
- Test: lên `+1` khi câu hỏi sửa; tạo `_de_C` khi bổ sung đề mới (giữ nguyên A, B).

### 7.2 Quy trình thay version

```
1. Sub-Agent A tạo content mới ở `modules/<old>/_v2_draft/`
2. Trưởng phòng review
3. Approved → đổi tên `_v2_draft/` → thay thư mục cũ; thư mục cũ chuyển vào `archive/`
4. Cập nhật `_changelog.md` ghi rõ thay đổi
5. Cập nhật `module_master.xlsx`: version, ngay_cap_nhat_cuoi
6. Trigger re-evaluate cho tất cả NS đã học version cũ trong 6 tháng qua (Sub-Agent C)
```

### 7.3 Schema _changelog.md

```markdown
# Changelog — KTV-L3-015 Chẩn đoán OBD nâng cao

## v2.0 — 2026-08-12
- Thay đổi: Cập nhật theo Toyota DTC Master List 2026 (mã lỗi mới P3450-P3499).
- Thêm: Mục 5 — Chẩn đoán xe hybrid Camry HV.
- Sửa: Outline mục 2 từ "16 chân" sang "16-pin connector" cho chính xác.
- Source mới: Toyota Hybrid Diagnostic Guide 2026 v1.

## v1.1 — 2026-05-10
- Sửa: Lỗi typo p.18 (mã lỗi P0420 chứ không phải P4020).
- Bổ sung: Câu trả lời cho FAQ KTV ở phụ lục.

## v1.0 — 2026-04-15
- Phát hành lần đầu.
```

---

## 8. Backup & Sync

### 8.1 Lịch backup

| Thư mục | Tần suất | Đích |
|---|---|---|
| `modules/` | Hằng ngày | Cloud backup |
| `tests/` | Hằng ngày | Cloud + offline (USB) |
| `evaluations/`, `reviews/` | Hằng tuần | Cloud |
| `_hang_source/` | Khi có file mới | Local + cloud |
| `_master/` | Real-time | Cloud (Google Drive shared) |

### 8.2 Sync giữa các chi nhánh

- Trưởng phòng dịch vụ tổng (cấp đại lý PGS) là chủ thư mục `modules/`.
- Mỗi chi nhánh có thư mục `chi_nhanh/<ten_chi_nhanh>/` riêng cho:
  - `evaluations/` của NS chi nhánh đó.
  - `reviews/` của GP chi nhánh đó.
  - Module customize riêng (nếu có): `modules_local/`.

---

## 9. Quy tắc bất biến

1. **Mọi module phải có README.md với YAML frontmatter đầy đủ** — Sub-Agent A enforce.
2. **Mọi module phải có source_links.md trỏ về _hang_source/** — Hook H1 Copyright check.
3. **Tài liệu trong `_hang_source/` là READ-ONLY** — không sửa, không xoá.
4. **Module `trang_thai = active` không được sửa trực tiếp** — phải tạo version mới.
5. **Test phải có ≥ 2 đề song song (A, B)** — Hook H4 Pass-Rate-Lock.
6. **Đặt tên file đúng convention** — không có file `final_v2_FINAL_use_this.docx`.
7. **Mọi thay đổi module → ghi changelog** — không thay version mà không ghi.

---

## 10. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| Hãng update tài liệu nhưng không thay nhiều | Vẫn lưu version mới trong `_hang_source/`, kiểm tra module nào dùng → có cần re-compose không |
| Module dành cho 2 bộ phận (vd KTV + DS) | Tạo trong bộ phận chính, copy README + link content vào bộ phận thứ 2 |
| Có module được chia sẻ giữa các đại lý PGS | Lưu ở `modules/_shared/` (chỉ cho phép read, không write) |
| File hãng quá lớn (> 100MB) | Lưu link cloud trong `_hang_source/<TH>/_links.md`, không upload nguyên file |
| Module bị reject sau review | Không xoá, chuyển vào `modules/_rejected/` để học bài học |
| NS thay đổi bộ phận (KTV → CVDV) | Lịch sử module cũ giữ ở `evaluations/`, mở sheet mới ở bộ phận mới |
| Hãng yêu cầu xoá tài liệu | Xoá `_hang_source/`, mark module dùng tài liệu đó là `archived` ngay |
