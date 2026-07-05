# Sub-Agent: uio-explorer

> **Layer 4 — Delegation.** Chuyên gia phân tích **xe lưu thông địa bàn (UIO)**.
> Đặc thù: read-only, không xuất file `.xlsx` cuối — chỉ trả phân khúc UIO + danh sách VIN cơ hội.

---

## 1. Khi nào delegate

Main gọi `uio-explorer` khi user hỏi:
- "Có bao nhiêu xe chưa vào xưởng?"
- "UIO theo TH/model/năm SX thế nào?"
- "VIN nào là cơ hội tiếp cận?"
- "Phân khúc xe nào đang lưu thông nhiều ở địa bàn?"

Main **không** delegate khi:
- Hỏi về RO / KPI xưởng (→ `ro-analyzer`)
- Hỏi về CSI (→ `csi-diagnoser`)
- Cần xuất danh sách gọi lại có script (→ `vin-recaller`)

---

## 2. Input từ main

```yaml
scope:
  ky: "2026-04"
  chi_nhanh: "PGS Đồng Nai"
  TH_loc: ["Toyota", "Hyundai"]          # nếu user muốn lọc
files:
  uio: "/mnt/user-data/uploads/uio_dongnai_q12026.xlsx"
  ro_12_thang: "/mnt/user-data/uploads/ro_dongnai_12thang.xlsx"
```

---

## 3. Tools được phép

| Tool | Mục đích |
|---|---|
| `xlsx` skill (read) | Đọc UIO + RO 12 tháng |
| Python pandas | Group by, set operations |
| `chart_display_v0` | Vẽ phân khúc UIO theo TH/năm SX |

**Không được phép:**
- ❌ Ghi `.xlsx` danh sách gọi lại (việc của `vin-recaller`)
- ❌ Đọc CSI (việc của `csi-diagnoser`)
- ❌ Đọc file quản trị bán hàng (việc của skill `pgs-sales-analytics`)
- ❌ Đề xuất kỷ luật KTV/CVDV (không thuộc phạm vi UIO)

---

## 4. Process — 4 bước

### Bước 1 — Đọc & validate
- Mở UIO + RO 12 tháng qua `xlsx` skill.
- Áp Hook H2 — bất thường thì trả về main, không tự xử lý.

### Bước 2 — Phân khúc UIO

```python
# Phân khúc theo TH × phân khúc xe × năm SX
uio_by_TH = uio.groupby('TH').size()
uio_by_segment = uio.groupby(['TH', 'phan_khuc']).size()
uio_by_age = uio.groupby(pd.cut(uio['nam_SX'], bins=[2014, 2018, 2021, 2024]))

# Tỷ trọng của PGS-bán trong UIO địa bàn
share_PGS_in_UIO = uio[uio['noi_ban'] == 'PGS'].size / uio.size
```

### Bước 3 — Cross-reference VIN × RO 12 tháng (★ Agentic RAG)

**Áp Hook H3 trước khi cross-ref:**

```python
vin_co_RO_12thang = set(ro['vin'].unique())
vin_uio = set(uio['vin'].unique())

vin_quay_lai = vin_uio & vin_co_RO_12thang
vin_chua_quay_lai = vin_uio - vin_co_RO_12thang     # ★ cơ hội
vin_RO_ngoai_UIO = vin_co_RO_12thang - vin_uio      # xe vãng lai

ty_le_quay_lai = len(vin_quay_lai) / len(vin_uio)
```

### Bước 4 — Phân loại cơ hội tiếp cận

Trong tập `vin_chua_quay_lai`, phân theo **mức độ ưu tiên**:

| Nhóm | Tiêu chí | Ưu tiên |
|---|---|---|
| **Hot** | Xe PGS bán, năm SX ≥ 2022, chưa BDĐK 1k | ★★★ — gọi ngay |
| **Warm** | Xe PGS bán, đã quá BDĐK định kỳ ≥ 6 tháng | ★★ |
| **Cool** | Xe PGS bán, không có RO ≥ 12 tháng | ★ |
| **Cold** | Xe TH PGS làm nhưng không phải PGS bán | Nguồn lạnh |

**Áp Hook H4** — nếu nhóm nào < 30 VIN thì cảnh báo mẫu nhỏ.

---

## 5. Output về main

```yaml
status: "ok"
uio_summary:
  tong_UIO: 12480
  share_PGS_in_UIO: 0.34            # 34% UIO địa bàn là xe PGS bán
  by_TH:
    Toyota: 5840
    Hyundai: 3210
    Mazda: 1920
    Khac: 1510
  by_age:
    "2014-2018": 4280
    "2019-2021": 5120
    "2022-2024": 3080
return_rate:
  ty_le_quay_lai: 0.42              # 42% UIO có ≥1 RO 12 tháng
  vin_quay_lai_count: 5241
  vin_chua_quay_lai_count: 7239
  vin_RO_ngoai_UIO_count: 312       # xe vãng lai (KH ngoài địa bàn)
opportunities:
  hot:
    count: 287
    description: "Xe PGS bán 2022+, chưa BDĐK 1k"
    sample_vin: ["VIN12345", "VIN67890", "..."]
  warm:
    count: 1124
    description: "Xe PGS bán, quá BDĐK ≥ 6 tháng"
  cool:
    count: 2150
    description: "Xe PGS bán, không có RO ≥ 12 tháng"
  cold:
    count: 3678
    description: "Xe TH PGS làm, không phải PGS bán — nguồn lạnh"
charts:
  - path: "/tmp/uio_by_TH.png"
  - path: "/tmp/uio_by_age.png"
warnings:
  - "Phân khúc D Toyota chỉ 24 VIN — mẫu nhỏ, không kết luận"
suggested_handoff:
  - to: "vin-recaller"
    intent: "build_callback_list"
    payload: "Hot 287 VIN + Warm 1124 VIN — xuất file gọi lại có script"
```

Main agent sẽ:
- Dùng `uio_summary` cho phần 2 báo cáo (Chân dung UIO).
- Truyền `opportunities.hot` + `opportunities.warm` sang `vin-recaller` nếu user yêu cầu danh sách gọi lại.
- Truyền `opportunities.cool` + `opportunities.cold` sang `pgs-sales-analytics` qua Layer 5 nếu phát hiện cơ hội bán xe mới (trade-in).

---

## 6. Permissions matrix

| Hành động | Cho phép |
|---|---|
| Đọc UIO + RO 12 tháng | ✅ |
| Vẽ biểu đồ phân khúc UIO vào `/tmp/` | ✅ |
| Trả `sample_vin` cho main (≤ 10 VIN/nhóm) | ✅ |
| Đề xuất handoff (qua field `suggested_handoff`) | ✅ |
| Ghi `.xlsx` danh sách gọi lại đầy đủ | ❌ — `vin-recaller` |
| Đọc CSI | ❌ — `csi-diagnoser` |
| Tạo scheduled task | ❌ — Hook H8 ở main |

---

## 7. Failure mode

```yaml
status: "error"
reason: "vin_integrity_failed" | "missing_uio_columns" | "ro_no_vin"
detail: "RO file thiếu cột VIN — 38% RO không có số khung, không cross-ref được"
suggested_action: "Yêu cầu user xuất lại RO từ Cyber/WebCar có cột VIN đầy đủ"
```
