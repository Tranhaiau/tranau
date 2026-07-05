# Hooks — Sales Analytics Guardrails

> **Layer 3 — Deterministic. Not AI.** Không có hook nào "hơi đúng" — chỉ có **pass** hoặc **fail**.
> Khi fail, dừng workflow tại chỗ và sửa, không vượt qua.
>
> Mỗi hook gồm: **Event** (kích hoạt khi nào) → **Matcher** (điều kiện check) → **Command** (làm gì).

---

## H1 — PreFetch · Xác nhận phạm vi

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi gọi tool đọc file Excel/CSV (`xlsx` skill) |
| **Matcher** | User chưa nêu đủ 4 yếu tố: kỳ phân tích / địa bàn / TH trọng tâm / mục đích |
| **Command** | Gọi `ask_user_input_v0` với 4 câu hỏi single_select hoặc multi_select |
| **Pass** | User trả lời đủ → ghi vào context "Scope đã xác định: …" |
| **Fail** | Không hỏi đủ → main agent **không được** đọc file |

**Mẫu câu hỏi:**

```json
[
  {"question": "Kỳ phân tích?", "options": ["Tháng này", "Tháng trước", "Quý này", "YTD"]},
  {"question": "Phạm vi địa bàn?", "options": ["Toàn quốc", "Vùng", "Tỉnh", "Huyện/CN PGS"]},
  {"question": "TH trọng tâm?", "options": ["Toyota", "Hyundai", "Mazda", "Kia", "Đa TH"]},
  {"question": "Mục đích?", "options": ["Review nội bộ", "Báo cáo hãng", "Plan tháng tới"]}
]
```

---

## H2 — PostFetch · Báo cáo bất thường dữ liệu

| Mục | Giá trị |
|---|---|
| **Event** | Sau khi đọc xong file Excel, trước khi tính chỉ số |
| **Matcher** | Có ≥1 trong các bất thường sau |
| **Command** | Liệt kê bất thường + dừng + chờ user xác nhận xử lý |

**Danh sách bất thường bắt buộc check:**

| Bất thường | Cách phát hiện | Hành động đề xuất |
|---|---|---|
| Thiếu cột bắt buộc (số khung, ngày đăng ký, mã TH) | `set(required_cols) - set(df.columns)` | Yêu cầu user gửi file đúng template |
| Dòng tổng/tổng cộng lẫn vào dữ liệu | Cell có chuỗi "Tổng", "Total", merged cells | Lọc ra trước khi tính |
| VIN/số khung trùng (khi không nên trùng) | `df.duplicated('vin').sum() > 0` | Hỏi: giữ bản đầu / cuối / tất cả? |
| Ngày đăng ký nằm ngoài kỳ phân tích | `~df['ngay'].between(start, end)` | Có thể là dữ liệu lệch tháng |
| Doanh số = 0 hoặc âm | `df['doanh_so'] <= 0` | Thường là dòng rỗng — bỏ |
| Model lạ không có trong danh mục TH | left join với master model | Có thể là model xe nhập tư nhân |

**Pass:** không có bất thường, hoặc user đã xác nhận xử lý.
**Fail:** chưa báo cáo cho user → không được tính KPI.

---

## H3 — PreReason · Sample size check

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi tính tỷ lệ chuyển đổi phễu / share of dealer ở đơn vị nhỏ |
| **Matcher** | Mẫu số (denominator) < 30 |
| **Command** | Gắn cờ "⚠️ Mẫu nhỏ — độ tin cậy thống kê thấp" vào kết quả |

**Ví dụ:**
- TVBH có 8 KHTN tiếp cận trong tháng → tính tỷ lệ chốt 25% **không có ý nghĩa**.
- Phân khúc D có 12 xe DLTT trong huyện → không kết luận được thị phần.

**Pass:** mẫu ≥ 30, hoặc đã gắn cờ cảnh báo và **không** dùng số này để ra quyết định nhân sự/đầu tư.
**Fail:** dùng tỷ lệ mẫu nhỏ để đánh giá TVBH/đề xuất sa thải → **chặn cứng**.

---

## H4 — PostReason · Sanity check số liệu

| Mục | Giá trị |
|---|---|
| **Event** | Sau khi tính xong KPI, trước khi viết báo cáo |
| **Matcher** | Có ≥1 con số phi lý |
| **Command** | Quay lại H2 (kiểm tra bất thường file) — không xuất báo cáo |

**Bảng phi lý cứng:**

| Chỉ số | Khoảng hợp lý | Nếu vượt |
|---|---|---|
| Thị phần TH | 0%–100% | Sai công thức hoặc sai mẫu số |
| Share of dealer | 0%–100% | Sai công thức |
| YoY tăng trưởng | -90% đến +500% | Có thể đúng nhưng phải có chú thích |
| Tỷ lệ chốt phễu | 0%–100% | Sai logic Cold/Warm/Hot |
| DT/HĐ trung bình | Trong khoảng giá xe của TH ±30% | Có thể có dòng outlier (xe sang/fleet lớn) |

**Pass:** mọi KPI nằm trong khoảng hợp lý hoặc có giải thích.
**Fail:** Sửa từ Layer 2 (`02-market-share-formulas.md`) → tính lại.

---

## H5 — PreImplement · Mọi giải pháp phải có Chủ thể + KPI + Hạn

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi viết phần 4 báo cáo (Giải pháp triển khai) |
| **Matcher** | Bất kỳ dòng GP nào thiếu 1 trong 3 trường |
| **Command** | Hoặc bổ sung đủ, hoặc xoá khỏi báo cáo |

**Schema bắt buộc của mỗi GP:**

```yaml
- van_de: "TVBH Nguyễn Văn A có tỷ lệ chốt 8% (trung bình team 22%)"
  giai_phap: "Đào tạo lại module xử lý từ chối + kèm cặp 2 tuần"
  chu_the: "Trưởng phòng KD + TVBH A"        # BẮT BUỘC — tên/mã NS cụ thể
  kpi: "Tỷ lệ chốt ≥ 18% trong tháng tới"     # BẮT BUỘC — có ngưỡng số
  han: "30/05/2026"                            # BẮT BUỘC — ngày cụ thể
  ngay_review: "12/05/2026 (review giữa kỳ)"   # BẮT BUỘC — đẩy vào Hook H6
```

**Cấm các cụm mơ hồ:**
- ❌ "Cải thiện sớm" → ✅ "Trước 30/05/2026"
- ❌ "Phòng KD chịu trách nhiệm" → ✅ "Trưởng phòng KD: Trần Văn B"
- ❌ "Tăng doanh số" → ✅ "Doanh số tháng 5 ≥ 45 xe (+15% MoM)"

**Pass:** tất cả GP đủ 5 trường.
**Fail:** GP nào thiếu → bỏ khỏi báo cáo (không "ghi tạm").

---

## H6 — Stop · Đề xuất scheduled review

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi kết thúc phiên (đã xuất báo cáo) |
| **Matcher** | Báo cáo có ≥1 GP với `ngay_review` |
| **Command** | Hỏi user có tạo scheduled task không, gọi `mcp__scheduled-tasks__create_scheduled_task` nếu đồng ý |

**Mẫu task chuẩn:**

```
Title: "Review GP Sales tuần — <chi nhánh> — kỳ <tháng>"
Run at: <ngay_review> 09:00
Prompt:
  Đọc quan_tri_<chi_nhanh>_mới_nhất.xlsx và sales_pgs_<tháng>.xlsx.
  So baseline ngày <X> đã ghi trong báo cáo trước.
  Với mỗi GP:
    - KPI đạt ≥ ngưỡng → ghi "giữ" + tiếp tục theo dõi
    - KPI chưa đạt → đề xuất điều chỉnh GP
  Cập nhật action plan, gửi lại báo cáo ngắn 1 trang.
```

**Pass:** user đồng ý → task đã tạo, hoặc user từ chối → ghi log "user opted out".
**Fail:** kết thúc phiên mà không hỏi → vi phạm vòng lặp Agentic.

---

## Tóm tắt thứ tự thực thi

```
[USER UPLOAD FILE]
        ↓
    H1 PreFetch       → ask_user_input_v0 nếu thiếu scope
        ↓
   [đọc file Excel]
        ↓
    H2 PostFetch      → liệt kê bất thường, chờ user
        ↓
    H3 PreReason      → flag mẫu nhỏ
        ↓
   [tính KPI]
        ↓
    H4 PostReason     → sanity check, quay lại H2 nếu phi lý
        ↓
    H5 PreImplement   → enforce schema GP (Chủ thể + KPI + Hạn)
        ↓
   [xuất báo cáo .docx/.xlsx]
        ↓
    H6 Stop           → đề xuất scheduled review
        ↓
   [END]
```

**Nguyên tắc:** một hook fail → quay lại đúng vị trí trong workflow trên, không "vá tạm" để đi tiếp.
