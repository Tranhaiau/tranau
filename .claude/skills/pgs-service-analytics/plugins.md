# Plugins — Layer 5 Distribution & Handoff Matrix

> **Layer 5.** Skill `pgs-service-analytics` ở vị trí **trung tâm** trong hệ sinh thái PGS:
> nó vừa nhận handoff từ sales (kiểm tra hậu mãi), vừa gửi handoff sang training
> (KTV/CVDV cần đào tạo) và sang sales (cơ hội bán xe mới từ UIO im ắng).
>
> Đây cũng là skill **cung cấp baseline KPI** cho training đo hiệu quả sau 30/60/90 ngày.

---

## 1. Outbound — Service gửi đi

### 1.1 → `pgs-training-management` (KTV cần đào tạo)

**Khi nào:**
- `ro-analyzer` phát hiện KTV bottom 20% có pattern lặp (low_productivity_low_dt, comeback_kỹ_thuật, …).
- `csi-diagnoser` phát hiện KTV/CVDV có CSI thấp với mẫu ≥ 30 phiếu.

**Payload chuẩn:**

```yaml
from: "pgs-service-analytics"
to: "pgs-training-management"
intent: "training_request"
nhan_su:
  ma_NV: "NV023"
  ten: "Phạm Văn E"
  bo_phan: "Service (KTV)"
  level_hien_tai: 3
  TH_chuyen: "Toyota"
ly_do:
  pattern: "comeback_kỹ_thuật"
  mo_ta: "FTF 80% (TB team 92%), 9/45 RO comeback trong 30 ngày, lỗi lặp 'rò rỉ dầu'"
  bang_chung_RO: ["#2024-0421", "#2024-0438", "#2024-0492"]
module_de_xuat:
  - "ro_ri_dau_chuan_doan"
  - "kiem_tra_sau_sua_chua"
baseline_KPI_truoc_dao_tao:
  ngay: "2026-05-05"
  ftf: 0.80
  productivity: 0.68
  efficiency: 0.74
  dt_per_ro: 3100000
  comeback_count_30d: 9
review_sau:
  thoi_diem: ["+30 ngày", "+60 ngày", "+90 ngày"]
  field_can_lay: ["ftf", "productivity", "comeback_count_30d", "dt_per_ro"]
```

### 1.2 → `pgs-training-management` (CVDV cần đào tạo)

```yaml
from: "pgs-service-analytics"
to: "pgs-training-management"
intent: "training_request"
nhan_su:
  ma_NV: "NV012"
  ten: "Trần Văn C"
  bo_phan: "Service (CVDV)"
ly_do:
  pattern: "tu_van_yeu"
  mo_ta: "CSI 'tư vấn' 3.65/5 (TB team 4.30), 87 phiếu, phản hồi điển hình: không giải thích báo giá"
  bang_chung_RO: ["#2024-0438", "#2024-0521", "#2024-0612"]
module_de_xuat:
  - "tu_van_dich_vu_chuyen_sau"
  - "giai_thich_bao_gia_phu_tung"
baseline_KPI_truoc_dao_tao:
  csi_avg: 3.65
  csi_tu_van: 3.82
  ro_per_day: 8.2
  ty_le_goi_nhac_hen: 0.45
review_sau:
  thoi_diem: ["+30 ngày", "+60 ngày", "+90 ngày"]
```

---

### 1.3 → `pgs-sales-analytics` (cơ hội bán xe mới)

**Khi nào:**
- `uio-explorer` phát hiện nhiều VIN cũ chưa quay lại xưởng → có thể đã bán/chuyển nhượng → cơ hội tiếp cận chủ xe để bán xe mới.
- Phân khúc xe ≥ 5 năm tuổi đông → cơ hội trade-in.

**Payload chuẩn:**

```yaml
from: "pgs-service-analytics"
to: "pgs-sales-analytics"
intent: "sales_opportunity"
co_hoi:
  loai: "VIN cũ chưa quay lại xưởng > 12 tháng + xe ≥ 5 năm tuổi"
  so_VIN: 287
  phan_loai_xe:
    "Toyota Vios 2018-2020": 94
    "Hyundai Accent 2019-2020": 62
    "Mazda 3 2018": 38
    "Khác": 93
de_xuat:
  - "Chiến dịch gọi lại + ưu đãi đổi xe (trade-in)"
  - "Sự kiện 'Đổi xe — định giá ngay'"
  - "Combo: kiểm tra xe miễn phí → định giá thu cũ → quote xe mới"
file_VIN_dinh_kem: "/tmp/uio_im_ang_>12thang_>=5nam.xlsx"
context_bo_sung:
  ty_le_quay_lai_TB: 0.42
  uio_total: 12480
```

---

### 1.4 → `pgs-bi-report` (báo cáo tổng hợp)

```yaml
from: "pgs-service-analytics"
to: "pgs-bi-report"
intent: "consolidate_for_dealer_report"
contribution:
  uio: 12480
  ty_le_quay_lai: 0.42
  dt_dich_vu_thang: 3625000000
  dt_per_ro: 4250000
  csi: 4.31
  ftf: 0.87
  ty_le_dat_hen: 0.58
  bddk_1k_dung_han: 0.73
  hot_action_items:
    - "Đào tạo KTV NV023 (FTF kém)"
    - "Đào tạo CVDV NV012 (CSI tư vấn yếu)"
    - "Chiến dịch gọi BDĐK 1k cho 33 VIN còn cơ hội"
```

---

## 2. Inbound — Service nhận về

### 2.1 ← `pgs-sales-analytics` (kiểm tra hậu mãi)

**Khi nào sales trigger:**
- Doanh số sales sụt mà thị phần TH địa bàn ổn định → nghi ngờ KH cũ không quay lại / hậu mãi kém.

**Payload nhận:**

```yaml
from: "pgs-sales-analytics"
to: "pgs-service-analytics"
intent: "service_check"
ly_do: "Doanh số PGS giảm 8% MoM trong khi DLTT địa bàn ổn — nghi do hậu mãi"
yeu_cau:
  - "Lấy CSI 3 tháng gần nhất + so cùng kỳ"
  - "Lấy danh sách VIN PGS bán ≥ 3 năm chưa quay lại xưởng 12 tháng"
  - "Lấy FTF & comeback rate tháng vừa rồi"
return_format: "yaml summary, không cần báo cáo .docx"
```

**Service xử lý:**
- Main delegate sang `csi-diagnoser` (CSI 3 tháng).
- Main delegate sang `uio-explorer` (VIN PGS bán ≥ 3 năm chưa quay lại).
- Main delegate sang `ro-analyzer` (FTF + comeback).
- Tổng hợp → trả YAML summary cho sales.

---

### 2.2 ← `pgs-training-management` (lấy KPI sau đào tạo)

**Khi nào training trigger:**
- Sub-Agent D (reviewer) đến hạn 30/60/90 ngày sau đào tạo → cần lấy KPI mới của KTV/CVDV.

**Payload nhận:**

```yaml
from: "pgs-training-management"
to: "pgs-service-analytics"
intent: "kpi_postcheck_after_training"
nhan_su:
  ma_NV: "NV023"
  bo_phan: "KTV"
chu_ky: "+30 ngày"
yeu_cau:
  - "Lấy ftf, productivity, efficiency, dt_per_ro, comeback_count_30d của NV023 trong kỳ +30 ngày"
  - "So với baseline đính kèm bên dưới"
baseline_goc:
  ngay: "2026-05-05"
  ftf: 0.80
  productivity: 0.68
  efficiency: 0.74
  dt_per_ro: 3100000
  comeback_count_30d: 9
return_format: "yaml + verdict (improved | flat | declined)"
```

**Service xử lý:**
- Main delegate `ro-analyzer` filter `ma_KTV: NV023` trong cửa sổ +30 ngày.
- Cảnh báo nếu mẫu KPI sau đào tạo < 30 RO (Hook H4).
- Trả delta + verdict.

**Mẫu output trả về training:**

```yaml
status: "ok"
nhan_su: "NV023"
chu_ky: "+30 ngày (2026-06-05)"
ky_so_sanh: "2026-05-06 → 2026-06-05"
sample_ok: true
sample_n_ro: 38
delta:
  ftf: {truoc: 0.80, sau: 0.91, delta: +0.11, verdict: "improved"}
  productivity: {truoc: 0.68, sau: 0.78, delta: +0.10, verdict: "improved"}
  efficiency: {truoc: 0.74, sau: 0.82, delta: +0.08, verdict: "improved"}
  dt_per_ro: {truoc: 3100000, sau: 3850000, delta: +750000, verdict: "improved"}
  comeback_count_30d: {truoc: 9, sau: 3, delta: -6, verdict: "improved"}
overall_verdict: "improved"
note: "Cải thiện rõ rệt sau module rò rỉ dầu — đề xuất xét thăng level 4"
```

---

### 2.3 ← `csi-diagnoser` (qua main, không trực tiếp)

`csi-diagnoser` xác định KH bất mãn → main truyền sang `vin-recaller` (cùng skill, không phải Layer 5):

```yaml
internal_handoff:                       # nội bộ skill, không phải Layer 5
  from: "csi-diagnoser"
  to: "vin-recaller"
  intent: "build_callback_list_for_unhappy_customers"
  vin_list:
    - vin: "VIN12345"
      ro_id: "#2024-0438"
      cvdv_phu_trach: "NV012"
      diem_yeu: "tu_van"
      reason: "CSI 2/5 — phản hồi 'không giải thích báo giá'"
```

---

## 3. Cấu trúc skill bundle

```
pgs-service-analytics/
├── SKILL.md                     ← Layer 1 + bản đồ
├── references/                  ← Layer 2
│   ├── 01-data-schema.md
│   ├── 02-workshop-kpis.md
│   ├── 03-csi-and-service-metrics.md
│   ├── 04-action-playbook.md
│   ├── 05-review-cycle.md
│   └── 06-uio-revenue-analysis.md
├── hooks/                       ← Layer 3
│   └── checkpoints.md
├── subagents/                   ← Layer 4
│   ├── uio-explorer.md
│   ├── ro-analyzer.md
│   ├── csi-diagnoser.md
│   └── vin-recaller.md
├── memory/                      ← Layer 1 long-term
│   └── baselines/
│       └── <chi_nhanh>_<kỳ>.json
└── plugins.md                   ← Layer 5 (file này)
```

---

## 4. Quy tắc handoff bất biến (chung 3 skills)

1. **Mọi handoff đều qua main agent** — sub-agent không tự gọi skill khác.
2. **Payload phải có schema chuẩn** — không gửi text tự do.
3. **Mỗi handoff có `intent` rõ ràng**.
4. **Có baseline + ngày review** khi handoff training/sales — để đo hiệu quả vòng lặp.
5. **Không gửi file gốc — gửi đường dẫn** đã được validate qua Hook H2.
6. **Bên nhận có quyền từ chối** — không ép buộc.
7. **Service đặc biệt: mọi outbound training PHẢI kèm `bang_chung_RO`** (Hook H6 — Agentic RAG).

---

## 5. Vòng lặp Agentic xuyên skill — ví dụ thực tế (KTV NV023)

```
T0    Service: ro-analyzer phát hiện KTV NV023 FTF 80% — bottom 20%
                csi-diagnoser cross-check: KH phản hồi "rò rỉ dầu sau bảo dưỡng"
                Kết luận: pattern "comeback_kỹ_thuật"
      ↓
      Hook H7  → bằng chứng RO #2024-0421/-0438/-0492 đính kèm
      Hook H8  → ghi baseline NV023.ftf=0.80 vào memory/baselines/
                 + tạo scheduled review +12 ngày
      Layer 5  outbound → pgs-training-management
                          (training_request, baseline đầy đủ)

T+5   Training: Sub-Agent A composer → biên soạn module "rò rỉ dầu chuẩn đoán"
                Sub-Agent B test     → tạo test pass 80% (level 3)
                NV023 học + pass

T+30  Training: Sub-Agent D đến hạn 30 ngày
       Layer 5  inbound ← pgs-service-analytics
                         (kpi_postcheck_after_training)
       Service: ro-analyzer chạy filter NV023, kỳ T0+1 → T+30
                Sample n=38 RO → đủ điều kiện H4
                Trả về training:
                  ftf 0.80 → 0.91 (+0.11) ✓
                  productivity 0.68 → 0.78 (+0.10) ✓
                  comeback_30d 9 → 3 (-6) ✓
                Verdict: improved
       Training: cập nhật profile NV023, đề xuất xét thăng level 4

T+30  Đồng thời, scheduled review T0+12 đã chạy ở T0+12:
       Đọc ro mới + appointment + csi mới → so baseline trong memory
       → đánh giá GP "đào tạo KTV NV023" còn hiệu lực
       → đẩy báo cáo 1 trang cho Trưởng xưởng
```

→ Vòng lặp Agentic Loop đầy đủ giữa Service ↔ Training, có baseline rõ ràng,
có ngày review tự động, có verdict đo lường được — đúng tinh thần
**"CLAUDE.md sets the rules → Skills provide expertise → Hooks enforce quality →
Subagents delegate work → Plugins distribute capabilities"**.
