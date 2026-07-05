# Plugins — Layer 5 Distribution & Handoff Matrix

> **Layer 5.** Skill này không tồn tại biệt lập — nó **gửi và nhận** payload từ
> các skill khác. File này định nghĩa **mọi đường handoff** đi/đến `pgs-sales-analytics`.
>
> Ví dụ: TVBH yếu → handoff sang training để đào tạo → 30 ngày sau training trả KPI mới về sales.
> Đây chính là vòng lặp Agentic xuyên skill (cross-skill loop).

---

## 1. Outbound — sales gửi đi

### 1.1 → `pgs-training-management`

**Khi nào:**
- `funnel-diagnoser` phát hiện TVBH có pattern năng lực yếu (Cold→Warm yếu, Warm→Hot yếu, …).
- User trực tiếp yêu cầu: "TVBH A cần training gì?"

**Payload chuẩn:**

```yaml
from: "pgs-sales-analytics"
to: "pgs-training-management"
intent: "training_request"
nhan_su:
  ma_NV: "NV001"
  ten: "Nguyễn Văn A"
  bo_phan: "Sales (TVBH)"
  level_hien_tai: 2                     # nếu biết
  TH_chuyen: "Toyota"
ly_do:
  pattern: "Cold_to_Warm_yeu"
  mo_ta: "Tỷ lệ Cold→Warm 0.32 (TB team 0.61), tỷ lệ chốt 8% (TB 20%)"
  bang_chung:
    so_KHTN_thang: 38
    so_lai_thu: 11
    so_HD: 3
module_de_xuat:                         # gợi ý, training quyết cuối cùng
  - "khai_thac_nhu_cau"
  - "xu_ly_tu_choi"
baseline_KPI_truoc_dao_tao:             # quan trọng cho Sub-Agent D bên training
  ngay: "2026-05-05"
  ty_le_chot: 0.08
  cold_to_warm: 0.32
  warm_to_hot: 0.50
  ngay_TB_cold_to_HD: 24
review_sau:                             # hẹn lấy KPI mới
  thoi_diem: ["+30 ngày", "+60 ngày", "+90 ngày"]
  field_can_lay: ["ty_le_chot", "cold_to_warm", "warm_to_hot"]
```

**Kỳ vọng nhận lại:**
- Training trả về `module_id` đã được phân công + ngày dự kiến hoàn thành.
- Sau 30 ngày, training gọi `pgs-sales-analytics` để lấy KPI mới so baseline.

---

### 1.2 → `pgs-service-analytics`

**Khi nào:**
- Doanh số sụt mà thị phần TH địa bàn không sụt → nghi ngờ KH cũ không quay lại.
- Cần kiểm tra UIO → cơ hội bán xe thay thế cho KH có xe sắp cũ.

**Payload chuẩn:**

```yaml
from: "pgs-sales-analytics"
to: "pgs-service-analytics"
intent: "service_check"
ly_do: "Doanh số PGS giảm 8% MoM trong khi DLTT địa bàn ổn định — nghi do hậu mãi"
yeu_cau:
  - "Lấy CSI 3 tháng gần nhất + so cùng kỳ"
  - "Lấy danh sách VIN PGS bán ≥ 3 năm chưa quay lại xưởng 12 tháng (cơ hội bán xe mới)"
  - "Lấy FTF & comeback rate tháng vừa rồi"
return_format: "yaml summary, không cần báo cáo .docx"
```

---

### 1.3 → `pgs-bi-report`

**Khi nào:**
- Cần báo cáo tổng hợp toàn đại lý (sales + service + training) cho Dealer Principal.

**Payload chuẩn:**

```yaml
from: "pgs-sales-analytics"
to: "pgs-bi-report"
intent: "consolidate_for_dealer_report"
contribution:                           # phần do sales đóng góp vào báo cáo tổng
  thi_phan_TH: {Toyota: 19.2, Hyundai: 11.8}
  doanh_so: 89
  yoy: -3.4
  pipeline_du_bao_HD_14_ngay: 34
  hot_action_items:
    - "Sự kiện lái thử B-SUV"
    - "Đào tạo TVBH A"
```

---

## 2. Inbound — sales nhận về

### 2.1 ← `pgs-service-analytics`

**Khi nào service trigger:**
- Service phát hiện UIO cao nhưng tỷ lệ quay lại thấp → cơ hội bán xe mới cho KH cũ.

**Payload nhận:**

```yaml
from: "pgs-service-analytics"
to: "pgs-sales-analytics"
intent: "sales_opportunity"
co_hoi:
  loai: "VIN cũ chưa quay lại xưởng 12 tháng"
  so_VIN: 287
  phan_loai_xe:
    "Toyota Vios 2018-2020": 94
    "Hyundai Accent 2019-2020": 62
de_xuat:
  - "Chiến dịch gọi lại + ưu đãi đổi xe (trade-in)"
  - "Sự kiện 'Đổi xe nhân dịp đại lý 5 năm'"
file_VIN: "/mnt/data/uio_chua_quay_lai.xlsx"
```

**Sales xử lý:**
- `plan-builder` đưa cơ hội này vào nhóm "Marketing/Sự kiện" của plan tháng tới.

---

### 2.2 ← `pgs-training-management`

**Khi nào training trigger:**
- Sub-Agent D (reviewer) đến hạn 30/60/90 ngày sau đào tạo → lấy KPI mới của TVBH.

**Payload nhận:**

```yaml
from: "pgs-training-management"
to: "pgs-sales-analytics"
intent: "kpi_postcheck_after_training"
nhan_su:
  ma_NV: "NV001"
chu_ky: "+30 ngày"
yeu_cau:
  - "Lấy ty_le_chot, cold_to_warm, warm_to_hot, ngay_TB_cold_to_HD"
  - "So với baseline trong payload gốc (đính kèm bên dưới)"
baseline_goc:
  ngay: "2026-05-05"
  ty_le_chot: 0.08
  cold_to_warm: 0.32
return_format: "yaml + verdict (improved | flat | declined)"
```

**Sales xử lý:**
- `funnel-diagnoser` chạy lại nhưng chỉ filter theo `ma_NV: NV001` trong kỳ +30 ngày.
- Trả về delta + verdict.

---

## 3. Cấu trúc skill bundle (giống npm package)

```
pgs-sales-analytics/
├── SKILL.md                    ← entry point (Layer 1 + bản đồ)
├── references/                 ← Layer 2
├── hooks/                      ← Layer 3
├── subagents/                  ← Layer 4
└── plugins.md                  ← Layer 5 (file này)

# Khi cài qua marketplace:
# 1. Skill bundle được copy vào /mnt/skills/user/pgs-sales-analytics/
# 2. Description trong SKILL.md được index vào tool registry
# 3. Khi user nói câu trigger (xem description), skill auto-invoke
# 4. Layer 4 subagents được spawn theo nhu cầu, không tự động
# 5. Layer 5 handoff thực hiện qua main agent — không sub-agent gọi cross-skill
```

---

## 4. Quy tắc handoff bất biến

1. **Mọi handoff đều qua main agent** — sub-agent không tự gọi skill khác.
2. **Payload phải có schema chuẩn** (như mục 1, 2 ở trên) — không gửi text tự do.
3. **Mỗi handoff có `intent` rõ ràng** — bên nhận biết phải làm gì.
4. **Có baseline + ngày review** khi handoff training/service — để đo hiệu quả vòng lặp.
5. **Không gửi file gốc — gửi đường dẫn** đã được validate qua Hook H2.
6. **Bên nhận có quyền từ chối** (return `status: rejected, reason: ...`) — không ép buộc.

---

## 5. Vòng lặp Agentic xuyên skill (ví dụ thực tế)

```
T0  User upload DLTT + quan_tri T4/2026
    ↓
    pgs-sales-analytics chạy:
      market-analyzer  → thị phần Hyundai 76% (yếu)
      funnel-diagnoser → TVBH NV001 yếu Cold→Warm
      plan-builder     → plan với GP đào tạo NV001
    ↓
T0  Hook H6 → tạo scheduled review +12 ngày
    Layer 5 outbound → pgs-training-management
                       (training_request, baseline NV001)

T+5 pgs-training-management:
      Sub-Agent A composer → biên soạn module
      Sub-Agent B test     → tạo test pass 70%
      NV001 học + pass

T+30 pgs-training-management Sub-Agent D đến hạn
     Layer 5 inbound ← pgs-sales-analytics
                       (kpi_postcheck_after_training)
     pgs-sales-analytics funnel-diagnoser chạy lại với filter NV001
     → trả delta: ty_le_chot 0.08 → 0.19 (+0.11), verdict: improved

T+30 pgs-training-management cập nhật profile NV001
                            → đề xuất xét thăng level

T+30 Đồng thời, scheduled review T0+12 đã chạy ở T0+12:
     Đọc quan_tri mới → so baseline → đánh giá GP còn hiệu lực không
```

→ Đây chính là `Agentic Loop` mà sơ đồ "HOW IT ALL WORKS TOGETHER" mô tả:
**CLAUDE.md sets the rules → Skills provide expertise → Hooks enforce quality →
Subagents delegate work → Plugins distribute capabilities.**
