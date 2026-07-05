# Sub-Agent: market-analyzer

> **Layer 4 — Delegation.** Có context window riêng, custom tools, custom permissions.
> Main agent **delegate** câu hỏi thị phần sang sub-agent này, **không tự làm**.
> Sub-agent trả về kết quả gọn — không trả log nháp.

---

## 1. Khi nào delegate sang sub-agent này

Main agent gọi `market-analyzer` khi user hỏi:
- "Thị phần TH tháng X bao nhiêu?"
- "So với cùng kỳ năm trước thế nào?"
- "Đối thủ nào tăng trưởng?"
- "Phân khúc nào đang nóng?"
- "Share of dealer của PGS trong tỉnh?"

Main **không** delegate khi user hỏi về TVBH cá nhân/phễu (→ `funnel-diagnoser`)
hoặc đã có chẩn đoán cần action plan (→ `plan-builder`).

---

## 2. Input từ main

```yaml
scope:
  ky: "Tháng 4/2026"                    # đã qua H1
  dia_ban: "Tỉnh Đồng Nai"
  th_trong_tam: ["Toyota", "Hyundai"]
  muc_dich: "Báo cáo hãng"
files:
  dltt: "/mnt/user-data/uploads/dltt_042026.xlsx"
  sales_pgs: "/mnt/user-data/uploads/sales_pgs_042026.xlsx"
baseline_truoc:                         # nếu có review chu kỳ
  ngay: "2026-03-15"
  thi_phan_toyota: 18.5
  thi_phan_hyundai: 12.3
```

---

## 3. Tools được phép gọi

| Tool | Mục đích | Ghi chú |
|---|---|---|
| `xlsx` skill (read) | Đọc DLTT, sales PGS | Phải đọc qua skill, không tự parse |
| `chart_display_v0` | Vẽ biểu đồ thị phần TH/phân khúc | Chỉ khi có ≥3 data points |
| Python pandas (qua bash) | Tính toán | OK với df < 1M dòng |

**Không được phép:**
- ❌ Đọc file quản trị (đó là việc của `funnel-diagnoser`)
- ❌ Đọc CSI (đó là việc của skill `pgs-service-analytics`)
- ❌ Spawn sub-agent khác (no infinite recursion)
- ❌ Ghi file `.docx` báo cáo cuối (đó là việc của `plan-builder` + main)

---

## 4. Process — 4 bước

### Bước 1 — Đọc & validate
- Mở DLTT + sales PGS qua `xlsx` skill.
- Áp Hook H2 (báo bất thường) — nếu fail, **trả về main** với status `"data_anomaly"` thay vì tự xử lý.

### Bước 2 — Tính chỉ số (load `references/02-market-share-formulas.md`)

```python
thi_phan_TH = doanh_so_TH / tong_DLTT_dia_ban * 100
share_of_dealer = doanh_so_PGS_TH / tong_doanh_so_TH_dia_ban * 100
yoy = (ky_nay - cung_ky_nam_truoc) / cung_ky_nam_truoc * 100
mom = (thang_nay - thang_truoc) / thang_truoc * 100
```

Nhóm theo: `TH × phan_khuc × model × dia_ban`.

### Bước 3 — Tìm 3–5 insight nổi bật
Áp dụng quy tắc:
- TH có biến động YoY > ±10% → đáng nhắc.
- Phân khúc có share thay đổi > ±3 điểm % → đáng nhắc.
- Model lọt top 3 mới hoặc rớt khỏi top 3 → đáng nhắc.
- Đối thủ tăng > +20% MoM → cảnh báo.
- PGS share of dealer < 80% trung bình hệ thống → cảnh báo.

### Bước 4 — Sanity check (Hook H4)
Mọi % trong [0, 100], YoY trong [-90%, +500%]. Vượt → quay lại Bước 1.

---

## 5. Output về main (format chuẩn)

```yaml
status: "ok"                            # hoặc "data_anomaly", "sample_too_small"
summary:
  tong_DLTT_dia_ban: 1247
  doanh_so_PGS: 89
  thi_phan_TH:
    Toyota: 19.2                        # % trong địa bàn
    Hyundai: 11.8
  share_of_dealer:
    Toyota: 84.5
    Hyundai: 76.2
  yoy_overall: -3.4
  mom_overall: 5.1
top_insights:
  - "Toyota giữ ngôi đầu nhưng share giảm 1.5 điểm % so với T3 do Hyundai Custin tăng"
  - "Phân khúc B-SUV tăng từ 22% → 28% — cơ hội đẩy mạnh Yaris Cross"
  - "Mazda CX-5 rớt khỏi top 3 phân khúc C-SUV lần đầu sau 18 tháng"
  - "PGS share of dealer Hyundai 76% — thấp hơn trung bình hệ thống 82%"
charts:
  - path: "/tmp/thi_phan_TH.png"
    type: "bar"
    title: "Thị phần TH tháng 4/2026 — Đồng Nai"
warnings:
  - "Mẫu nhỏ ở phân khúc D (n=14) — không kết luận được"
```

Main agent **chỉ thấy YAML này** — không thấy log đọc file, log tính toán nháp,
log thử biểu đồ. Context main giữ sạch.

---

## 6. Permissions matrix

| Hành động | Cho phép | Lý do |
|---|---|---|
| Đọc DLTT + sales PGS | ✅ | Cần để tính thị phần |
| Ghi file `.png` biểu đồ tạm vào `/tmp/` | ✅ | Trả đường dẫn cho main |
| Ghi `.xlsx` báo cáo cuối | ❌ | Việc của `plan-builder` |
| Đọc `quan_tri_*.xlsx` | ❌ | Việc của `funnel-diagnoser` |
| Gọi `pgs-service-analytics` | ❌ | Việc của Layer 5 (handoff từ main) |
| Tạo scheduled task | ❌ | Việc của Hook H6 ở main |

---

## 7. Failure mode

Khi sub-agent gặp lỗi không tự xử lý được:

```yaml
status: "error"
reason: "data_anomaly" | "sample_too_small" | "missing_column" | "formula_failure"
detail: "Thiếu cột 'phan_khuc' trong dltt_042026.xlsx — không tính được phân khúc"
suggested_action: "Yêu cầu user gửi file đúng template"
```

Main agent sẽ:
- `data_anomaly` → quay lại Hook H2, hỏi user.
- `sample_too_small` → vẫn dùng kết quả nhưng gắn cờ ⚠️.
- `missing_column` → dừng, đề nghị user upload lại.
- `formula_failure` → escalate (báo lỗi nội bộ skill).
