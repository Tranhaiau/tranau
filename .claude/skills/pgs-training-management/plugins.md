# Plugins — Layer 5 Distribution & Handoff Matrix

> **Layer 5.** Skill `pgs-training-management` ở vị trí **đóng vòng lặp** trong hệ sinh thái:
> nhận handoff từ Sales/Service (NS yếu cần đào tạo), trả lại Sales/Service sau 30/60/90 ngày
> (KPI cải thiện chưa). Đây là skill duy nhất có **scheduled task tự động** xuyên thời gian.

---

## 1. Inbound — Training nhận về

### 1.1 ← `pgs-sales-analytics` (TVBH yếu)

**Khi nào sales trigger:**
- `funnel-diagnoser` phát hiện TVBH có pattern năng lực yếu (Cold→Warm yếu, Hot→HĐ yếu, …).

**Payload nhận:**

```yaml
from: "pgs-sales-analytics"
to: "pgs-training-management"
intent: "training_request"
nhan_su:
  ma_NV: "NV001"
  ten: "Nguyễn Văn A"
  bo_phan: "Sales (TVBH)"
  level_hien_tai: 2
  TH_chuyen: "Toyota"
ly_do:
  pattern: "Cold_to_Warm_yeu"
  mo_ta: "Tỷ lệ Cold→Warm 0.32 (TB team 0.61), tỷ lệ chốt 8% (TB 20%)"
  bang_chung: {so_KHTN_thang: 38, so_lai_thu: 11, so_HD: 3}
module_de_xuat: ["khai_thac_nhu_cau", "xu_ly_tu_choi"]
baseline_KPI_truoc_dao_tao:
  ngay: "2026-05-05"
  ty_le_chot: 0.08
  cold_to_warm: 0.32
  warm_to_hot: 0.50
review_sau:
  thoi_diem: ["+30 ngày", "+60 ngày", "+90 ngày"]
  field_can_lay: ["ty_le_chot", "cold_to_warm", "warm_to_hot"]
```

**Training xử lý:**
1. Main kiểm tra kho `training/brands/toyota/sales/L2/modules/` — module "khai_thac_nhu_cau" có sẵn?
   - **Có** → bỏ qua A, gọi B test-builder.
   - **Chưa** → gọi A composer (cần upload tài liệu nguồn từ user) → B → C → D.
2. NS học + thi → C cập nhật profile.
3. Main lên scheduled task +30/+60/+90 (Hook H8).
4. Mỗi mốc đến hạn → D gọi outbound trở lại Sales lấy KPI mới.

---

### 1.2 ← `pgs-service-analytics` (KTV/CVDV yếu)

**Khi nào service trigger:**
- `ro-analyzer` phát hiện KTV bottom 20% có pattern (low_productivity, comeback_kỹ_thuật, …).
- `csi-diagnoser` phát hiện CVDV có CSI thấp với mẫu ≥ 30 phiếu.

**Payload nhận** (mẫu KTV):

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
  mo_ta: "FTF 80%, 9/45 RO comeback, lỗi lặp 'rò rỉ dầu'"
  bang_chung_RO: ["#2024-0421", "#2024-0438", "#2024-0492"]   # ★ Service luôn kèm RO
module_de_xuat: ["ro_ri_dau_chuan_doan", "kiem_tra_sau_sua_chua"]
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

**Training xử lý:** giống 1.1, nhưng nội dung kỹ thuật → kích hoạt Hook H6 (Safety-First) khi A biên soạn.

---

### 1.3 ← User trực tiếp

**Khi nào:**
- User upload PDF/Word/PPT từ hãng kèm yêu cầu "biên soạn lại cho KTV mới".
- User: "Tạo bài test cho CVDV level 2"
- User: "Xếp hạng KTV xưởng tháng này"
- User: "Review hiệu quả đào tạo tháng trước"

**Không cần payload chuẩn** — main parse intent rồi delegate sang A/B/C/D phù hợp.

---

## 2. Outbound — Training gửi đi

### 2.1 → `pgs-service-analytics` (lấy KPI sau đào tạo)

**Khi nào training trigger:**
- Sub-Agent D đến hạn 30/60/90 ngày sau đào tạo → cần KPI mới của KTV/CVDV để đo delta.

**Payload chuẩn:**

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

**Kỳ vọng nhận lại:** YAML với delta + sample_n + verdict (như đã định trong service/plugins.md mục 2.2).

---

### 2.2 → `pgs-sales-analytics` (lấy KPI sau đào tạo TVBH)

**Khi nào:**
- Tương tự 2.1 nhưng cho TVBH.

**Payload chuẩn:**

```yaml
from: "pgs-training-management"
to: "pgs-sales-analytics"
intent: "kpi_postcheck_after_training"
nhan_su:
  ma_NV: "NV001"
  bo_phan: "TVBH"
chu_ky: "+30 ngày"
yeu_cau:
  - "Lấy ty_le_chot, cold_to_warm, warm_to_hot, ngay_TB_cold_to_HD"
  - "So với baseline trong payload gốc"
baseline_goc:
  ngay: "2026-05-05"
  ty_le_chot: 0.08
  cold_to_warm: 0.32
return_format: "yaml + verdict"
```

---

### 2.3 → `automotive-dealer-analytics` (báo cáo tổng hợp)

```yaml
from: "pgs-training-management"
to: "automotive-dealer-analytics"
intent: "consolidate_for_dealer_report"
contribution:
  ky: "T4-T5/2026"
  so_NS_da_dao_tao: 14
  so_module_da_bien_soan: 6
  ty_le_pass_test: 0.86
  ty_le_cai_thien_KPI_30d: 0.71        # 10/14 NS có KPI improved sau 30d
  hot_action_items:
    - "NV023 đủ điều kiện thăng L4 sau module rò rỉ dầu"
    - "NV001 cải thiện ty_le_chot từ 8% → 19% sau training"
    - "3 module mới sẵn sàng triển khai cho team Hyundai"
```

---

## 3. Cấu trúc skill bundle

```
pgs-training-management/
├── SKILL.md                     ← Layer 1 + bản đồ
├── references/                  ← Layer 2
│   ├── 01-folder-structure.md
│   ├── 02-level-competency-matrix.md
│   ├── 03-training-content-template.md
│   ├── 04-test-template.md
│   ├── 05-evaluation-and-ranking.md
│   ├── 06-review-cycle.md
│   └── 07-training-roadmap.md
├── hooks/                       ← Layer 3
│   └── checkpoints.md
├── subagents/                   ← Layer 4 (★ nhiều nhất: 4 subs)
│   ├── A-composer.md
│   ├── B-test-builder.md
│   ├── C-evaluator.md
│   └── D-reviewer.md
├── training/                    ← Layer 1 long-term memory
│   ├── 00-framework/
│   ├── brands/
│   │   ├── toyota/
│   │   │   ├── service/L1/...L7/{modules,tests,practical}
│   │   │   ├── sales/L1/...L7/{modules,tests,practical}
│   │   │   ├── parts/...
│   │   │   └── csa/...
│   │   ├── hyundai/...
│   │   └── ...
│   ├── people/                  ← profile <ma_NV>.json
│   └── reviews/                 ← bảng xếp hạng + báo cáo định kỳ
└── plugins.md                   ← Layer 5 (file này)
```

---

## 4. Quy tắc handoff bất biến

1. **Mọi handoff đều qua main agent** — sub-agent A/B/C/D không tự gọi skill khác.
2. **Inbound bắt buộc có baseline KPI** — Hook H7 từ chối nếu thiếu.
3. **Service inbound bắt buộc có `bang_chung_RO`** — Hook H6 đặc trưng RAG bên Service.
4. **Outbound D → Sales/Service phải có `baseline_goc`** — không bên kia có gì để so.
5. **Mọi handoff inbound trigger pipeline A→B→C→D** (hoặc bỏ qua A nếu module có sẵn).
6. **Mỗi NS chỉ có 1 đào tạo "active" tại 1 thời điểm** — không trộn 2 module song song.

---

## 5. Vòng lặp Agentic xuyên skill — 2 case study

### Case A: KTV NV023 (Service ↔ Training)

```
T0    Service ro-analyzer phát hiện NV023 FTF 80%, comeback rò rỉ dầu
       Service csi-diagnoser xác nhận lỗi kỹ thuật
       Service Hook H8 → ghi baseline + tạo scheduled review +12d
       Service Layer 5 outbound → Training (training_request, baseline đầy đủ)

T+1   Training Main nhận → kiểm tra kho training/brands/toyota/service/L3/modules/
       → "ro_ri_dau_chuan_doan.docx" CHƯA CÓ → user upload manual hãng
       Training A composer biên soạn (Hook H1/H2/H6 pass)
       Training B test-builder sinh 2 đề song song (Hook H3/H4 pass)

T+10  NV023 học (8h) + thi
       Training C evaluator chấm: diem_test=0.82, KPI_score=0.69 (mới đầu)
       Verdict C: "Pass test — KPI thực chiến chưa ổn định, theo dõi 30d"
       Training Hook H8 → cập nhật people/NV023.json + tạo 3 scheduled tasks +30/+60/+90d

T+30  Scheduled task +30d kích hoạt Sub-Agent D
       D Hook H7 check: baseline có ✓
       D Layer 5 outbound → Service (kpi_postcheck_after_training)
       Service ro-analyzer chạy filter NV023, kỳ T+1 → T+30, n=38 RO
       Trả về:
         ftf 0.80→0.91 (+0.11) improved
         productivity 0.68→0.78 (+0.10) improved
         comeback 9→3 (-6) improved
       D verdict tổng: "improved"
       D handoff lại C → C kiểm Hook H5: complex_ro 28/30 (cận biên)
                       → verdict "Pass test, đề xuất chờ +60d xác nhận thăng L4"
       D lên scheduled +60d

T+60  Scheduled +60d → D chạy lại
       Service trả về: ftf 0.93 (qua ngưỡng 0.92), complex_ro 32 (đủ)
       D handoff C → C: Hook H5 pass đầy đủ → verdict "Đủ điều kiện thăng L4"
       D lên scheduled +90d (theo dõi sau thăng cấp)

T+90  Scheduled +90d → D chạy lần cuối
       Verdict: "improved sustained"
       D đóng vòng lặp đào tạo này (lich_su_dao_tao.da_dong_vong_lap = true)
       Training báo cáo về dealer-analytics: "+1 KTV thăng L4, ROI rõ ràng"
```

### Case B: TVBH NV001 (Sales ↔ Training)

```
T0    Sales funnel-diagnoser phát hiện NV001 ty_le_chot 8%, cold_to_warm 0.32
       Sales Layer 5 outbound → Training (training_request)

T+1   Training kiểm kho — module "khai_thac_nhu_cau" cho TVBH L2 ĐÃ CÓ
       → Bỏ qua A composer
       Training B sinh đề mới (làm mới ngân hàng câu hỏi)

T+5   NV001 học (4h, ngắn hơn KTV) + thi
       C: pass test 0.85, verdict "Theo dõi 30d"
       Hook H8 → 3 scheduled tasks

T+30  D + Sales outbound:
       cold_to_warm 0.32 → 0.58 (+0.26) improved
       ty_le_chot 0.08 → 0.19 (+0.11) improved
       Verdict tổng: "improved"
       D đề xuất nhân rộng module cho 2 TVBH khác có pattern tương tự

T+60, T+90  Theo dõi tiếp → đóng vòng lặp
```

→ Cả 2 case đều minh hoạ tinh thần Agent Development Kit: **CLAUDE.md sets the rules
→ Skills provide expertise → Hooks enforce quality → Subagents delegate work
→ Plugins distribute capabilities** — kết quả là ROI đào tạo đo được bằng KPI thực tế,
không phải "cảm thấy" cải thiện.
