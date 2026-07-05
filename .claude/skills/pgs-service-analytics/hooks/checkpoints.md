# Hooks — Service Analytics Guardrails

> **Layer 3 — Deterministic. Not AI.** Đặc thù skill Service: dữ liệu là **VIN × RO × timeline**.
> Một sai sót về VIN integrity → toàn bộ chẩn đoán quay lại / FTF / comeback đều sai.
> Hooks ở đây nghiêm ngặt hơn Sales vì kéo theo quyết định nhân sự (đánh giá KTV/CVDV).

---

## H1 — PreFetch · Xác nhận scope

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi gọi `xlsx` skill đọc file UIO/RO/Phụ tùng |
| **Matcher** | User chưa nêu đủ 4 yếu tố: kỳ / chi nhánh / có gồm đồng sơn không / TH trọng tâm |
| **Command** | Gọi `ask_user_input_v0` với 4 câu hỏi |
| **Pass** | Đã ghi context "Scope: kỳ X, CN Y, đồng sơn ✓/✗, TH …" |
| **Fail** | Không được đọc file |

**Mẫu câu hỏi:**

```json
[
  {"question": "Kỳ phân tích?", "options": ["Tháng này", "Tháng trước", "Quý này", "YTD"]},
  {"question": "Phạm vi chi nhánh?", "options": ["Toàn hệ thống PGS", "Một chi nhánh", "So sánh nhiều CN"]},
  {"question": "Có gồm xưởng đồng sơn không?", "options": ["Có", "Chỉ dịch vụ chung", "Chỉ đồng sơn"]},
  {"question": "TH trọng tâm?", "options": ["Toyota", "Hyundai", "Mazda", "Kia", "Đa TH"]}
]
```

---

## H2 — PostFetch · Báo bất thường file

| Mục | Giá trị |
|---|---|
| **Event** | Sau khi đọc xong UIO + RO + Phụ tùng + (Hẹn) + (CSI) |
| **Matcher** | Có ≥1 bất thường |
| **Command** | Liệt kê + dừng + chờ user xác nhận |

**Bảng bất thường bắt buộc check:**

| Bất thường | Cách phát hiện | Ảnh hưởng nếu bỏ qua |
|---|---|---|
| RO thiếu số khung (VIN) | `df['vin'].isna().sum() > 0` | Không cross-ref được với UIO |
| VIN trong RO không có trong UIO | `set(ro.vin) - set(uio.vin)` | Có thể là xe vãng lai — phải đánh dấu |
| Doanh thu RO âm hoặc = 0 | `df['doanh_thu'] <= 0` | Có thể là RO bảo hành/khiếu nại — phân loại riêng |
| Ngày RO ngoài kỳ phân tích | `~df['ngay_ro'].between(start, end)` | Lệch tháng |
| KTV không có trong master NS | left join `ktv_master` → null | Có thể là KTV thử việc / đã nghỉ |
| BDĐK 1k mà ngày RO < ngày giao xe | logic check | Sai dữ liệu |
| Cột `loai_RO` không thuộc {BDĐK, SC, ĐS, BH} | `df['loai_RO'].unique()` ngoài tập | Phân loại sai |
| RO trùng (cùng VIN cùng ngày cùng KTV) | `df.duplicated(['vin','ngay','ktv'])` | Đếm gấp đôi |

**Pass:** không có bất thường, hoặc user đã xác nhận xử lý từng case.
**Fail:** chưa báo cáo → cấm bước sang H3.

---

## H3 — VIN-Integrity · Cross-reference VIN×RO

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi `uio-explorer` hoặc `vin-recaller` chạy cross-ref |
| **Matcher** | Tỷ lệ VIN khớp UIO ↔ RO < 95% |
| **Command** | Phân loại VIN bất khớp + báo user trước khi tính tỷ lệ quay lại |

**Phân loại VIN bất khớp:**

```yaml
vin_chi_co_trong_RO:                    # vào xưởng PGS nhưng không phải xe lưu thông địa bàn
  - "Xe vãng lai (KH ngoài địa bàn)"   # → tách ra, không tính vào tỷ lệ quay lại địa bàn
  - "Xe đã chuyển nhượng/ngoài tỉnh"
vin_chi_co_trong_UIO:                   # xe ở địa bàn nhưng chưa từng vào xưởng PGS
  - "Cơ hội tiếp cận (UIO ngoại)"      # → đầu vào cho vin-recaller
vin_co_ca_2:                            # đối tượng tính KPI quay lại
  - "Tính tỷ lệ quay lại trên tập này"
```

**Pass:** đã phân loại + user xác nhận cách xử lý.
**Fail:** Tính tỷ lệ quay lại trên dữ liệu chưa làm sạch → **chặn cứng**.

---

## H4 — Sample-Size · Mẫu nhỏ

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi tính KPI cá nhân (KTV/CVDV) hoặc tỷ lệ chuyên biệt (BDĐK 1k, đồng sơn) |
| **Matcher** | Mẫu số < 30 |
| **Command** | Gắn cờ ⚠️ + cấm dùng để ra quyết định nhân sự |

**Trường hợp điển hình:**

| Chỉ số | Mẫu cần ≥ | Nếu < |
|---|---|---|
| FTF cá nhân của KTV | 30 RO/KTV/tháng | Không đánh giá năng lực, chỉ ghi nhận |
| Tỷ lệ BDĐK 1k đúng hạn | 30 xe đến hạn/tháng | Cảnh báo |
| Tỷ lệ đồng sơn của 1 KTV ĐS | 20 RO ĐS/KTV/tháng | Không xếp hạng |
| CSI theo điểm chạm | 30 phiếu/điểm chạm | Cảnh báo độ tin cậy |

**Pass:** ≥ ngưỡng, hoặc đã gắn cờ và **không** dùng để đề xuất kỷ luật/thưởng.
**Fail:** Dùng tỷ lệ mẫu nhỏ để đánh giá KTV → chặn cứng.

---

## H5 — Sanity-Check · Số liệu phi lý

| Mục | Giá trị |
|---|---|
| **Event** | Sau khi tính xong KPI, trước khi viết báo cáo |
| **Matcher** | Có KPI vượt khoảng hợp lý |
| **Command** | Quay lại H2/H3 — không xuất báo cáo |

**Bảng phi lý cứng:**

| Chỉ số | Khoảng hợp lý | Thường do |
|---|---|---|
| Tỷ lệ quay lại | 0%–100% | Sai mẫu số (UIO vs filtered UIO) |
| FTF | 0%–100% | Sai logic comeback 30 ngày |
| CSI | 0–5 hoặc 0–100 (tùy thang) | Lẫn 2 thang đo |
| DT/RO | 200K – 50M VND | Outlier RO đại tu / sai đơn vị |
| Productivity KTV | 0%–150% | OK > 100% (làm thêm giờ); > 150% nghi sai |
| Tỷ lệ BDĐK đúng hạn | 0%–100% | Sai cửa sổ ±7 ngày & ±500km |
| Comeback rate | 0%–100% | OK; cao thường = chất lượng kém |

---

## H6 — RAG-Provenance · Chẩn đoán phải neo VIN/RO cụ thể

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi `csi-diagnoser` hoặc `ro-analyzer` viết câu chẩn đoán |
| **Matcher** | Câu chẩn đoán không có VIN/RO/mã KTV cụ thể đính kèm |
| **Command** | Bắt buộc bổ sung — nếu không có → bỏ chẩn đoán đó |

**Đây là đặc trưng Agentic RAG:** không chỉ nói "CSI giảm" mà phải truy được về phiếu nào.

**Mẫu đúng:**
- ✅ "CSI điểm 'tư vấn' giảm 0.4 điểm — bằng chứng: 7/12 phiếu CSI ≤ 3 thuộc CVDV NV012 (Trần Văn C), điển hình RO #2024-0438 phản hồi 'không giải thích báo giá'"
- ❌ "CSI giảm do CVDV làm chưa tốt" → reject

**Mẫu đúng:**
- ✅ "FTF tổng 87% (TB hệ thống 92%) — comeback tập trung ở KTV NV023 (Lê Văn D): 9/45 RO của KTV này quay lại trong 30 ngày, lỗi lặp 'rò rỉ dầu'"
- ❌ "Một số KTV làm chưa đạt" → reject

---

## H7 — PreImplement · Schema giải pháp đầy đủ

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi viết phần 5 báo cáo (Giải pháp triển khai) |
| **Matcher** | Bất kỳ GP nào thiếu Chủ thể / KPI / Hạn |
| **Command** | Bổ sung hoặc xoá khỏi báo cáo |

**Schema GP:**

```yaml
- van_de: "FTF KTV NV023 = 80%, comeback 9 RO lỗi 'rò rỉ dầu'"
  giai_phap: "Đào tạo lại module rò rỉ dầu + kèm cặp 2 tuần bởi KTV L5"
  chu_the: "Trưởng xưởng + KTV NV023"
  kpi: "FTF NV023 ≥ 92% trong 30 ngày tới; 0 RO comeback lỗi rò rỉ dầu"
  han: "31/05/2026"
  ngay_review: "12/05/2026"
  bang_chung_RO: ["#2024-0421", "#2024-0438", "#2024-0492"]   # ★ thêm so với Sales
```

Service GP **bắt buộc** có thêm field `bang_chung_RO` để truy vết — đặc trưng RAG.

---

## H8 — Stop · Baseline + scheduled review

| Mục | Giá trị |
|---|---|
| **Event** | Trước khi kết thúc phiên |
| **Matcher** | Đã xuất báo cáo, có ≥1 GP |
| **Command** | (1) Ghi baseline `memory/baselines/<chi_nhanh>_<kỳ>.json` (2) Hỏi user tạo scheduled review |

**Mẫu baseline file:**

```json
{
  "chi_nhanh": "PGS_DongNai",
  "ky": "2026-04",
  "ngay_chot": "2026-05-05",
  "kpi": {
    "uio": 12480,
    "ty_le_quay_lai": 0.42,
    "dt_per_ro": 4250000,
    "csi": 4.31,
    "ftf": 0.87,
    "ty_le_dat_hen": 0.58,
    "bddk_1k_dung_han": 0.74
  },
  "kpi_ktv": {
    "NV023": {"ftf": 0.80, "ro_count": 45},
    "NV017": {"ftf": 0.95, "ro_count": 52}
  },
  "kpi_cvdv": {
    "NV012": {"csi_avg": 3.8, "ro_per_day": 8.2}
  }
}
```

**Mẫu scheduled task:**

```
Title: "Review KPI xưởng tuần — <chi nhánh> — <kỳ>"
Run at: <ngay_review> 09:00
Prompt:
  Đọc ro_<chi_nhanh>_mới_nhất.xlsx + appointment_*.xlsx + csi_service_mới_nhất.xlsx.
  So với baseline file: memory/baselines/<chi_nhanh>_<kỳ>.json (đã ghi ngày X).
  Với mỗi GP có ngay_review == hôm nay:
    - KPI cá nhân (NV023.ftf, NV012.csi_avg, …) ≥ ngưỡng → giữ
    - Chưa đạt → đề xuất điều chỉnh GP
  Cập nhật action plan, gửi báo cáo 1 trang.
```

**Pass:** baseline đã ghi + user đã được hỏi.
**Fail:** Thiếu baseline → review chu kỳ sau không có gì để so → vi phạm Agentic Loop.

---

## Tóm tắt thứ tự thực thi

```
[USER UPLOAD UIO/RO/PHỤ TÙNG/HẸN/CSI]
        ↓
    H1 PreFetch         → ask_user_input_v0 nếu thiếu scope
        ↓
   [đọc file Excel]
        ↓
    H2 PostFetch        → liệt kê bất thường file
        ↓
    H3 VIN-Integrity    → phân loại VIN bất khớp UIO×RO  ★ đặc trưng Service
        ↓
    H4 Sample-Size      → flag mẫu nhỏ KTV/CVDV
        ↓
   [tính KPI]
        ↓
    H5 Sanity-Check     → khoảng hợp lý
        ↓
    H6 RAG-Provenance   → mỗi chẩn đoán phải neo VIN/RO   ★ đặc trưng Service (Agentic RAG)
        ↓
    H7 PreImplement     → schema GP đủ + bằng chứng RO
        ↓
   [xuất báo cáo .docx/.xlsx]
        ↓
    H8 Stop             → ghi baseline + scheduled review
        ↓
   [END]
```

**So với Sales**, Service có thêm 2 hook đặc trưng:
- **H3 VIN-Integrity** — vì dữ liệu xương sống là VIN×RO timeline, không có integrity là vứt.
- **H6 RAG-Provenance** — đặc trưng Agentic RAG, mọi chẩn đoán phải truy được về phiếu/VIN cụ thể.
