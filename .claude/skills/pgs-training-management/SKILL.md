---
name: pgs-training-management
description: Quản lý & tự động hoá đào tạo nội bộ Đại lý PGS theo kiến trúc 5 lớp ADK với Layer 4 mạnh nhất - Main Agent điều phối 4 sub-agents chuyên biệt (biên soạn / tạo bài test / xếp hạng / review hiệu quả). Kích hoạt khi user nói về đào tạo, training, tài liệu đào tạo, KTV kỹ thuật viên, cấp bậc level, 7 bậc thợ, thăng cấp, CVDV training, phụ tùng đào tạo, đồng sơn training, biên soạn tài liệu từ hãng, tài liệu kỹ thuật, quy trình quy chuẩn hãng, bài test đánh giá, ngân hàng câu hỏi, trắc nghiệm, tự luận, thực hành, đánh giá năng lực, xếp hạng nhân viên, lộ trình thăng cấp, plan đào tạo, review hiệu quả đào tạo, so sánh KPI trước/sau đào tạo, file PDF/Word/PPT từ hãng cần biên soạn lại, Toyota Hyundai Mazda Kia training, hoặc câu hỏi như "cần training gì để KTV lên L3", "biên soạn lại tài liệu Toyota", "tạo bài test cho CVDV".
---

# PGS Training Management — Agent Development Kit

> Skill này là ví dụ **rõ nhất** của Layer 4 (Subagents): Main Agent không tự làm,
> mà delegate sang 4 chuyên gia có context riêng, custom tools, custom permissions.

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER 5 — PLUGINS (Distribution)                            │
│  Nhận handoff từ sales/service · trả KPI cải thiện           │
├──────────────────────────────────────────────────────────────┤
│  LAYER 4 — SUBAGENTS (Delegation) ★ trọng tâm của skill này  │
│  A: composer · B: test-builder · C: evaluator · D: reviewer  │
├──────────────────────────────────────────────────────────────┤
│  LAYER 3 — HOOKS (Guardrails)                                │
│  Bản quyền hãng · pass rate theo level · không thăng cấp ép  │
├──────────────────────────────────────────────────────────────┤
│  LAYER 2 — SKILLS / KNOWLEDGE (On-demand)                    │
│  references/*.md — template, ma trận năng lực, công thức     │
├──────────────────────────────────────────────────────────────┤
│  LAYER 1 — MEMORY (Always-on)                                │
│  Constitution: 7 bậc, 4 bộ phận, profile NS, gắn KPI thực tế │
└──────────────────────────────────────────────────────────────┘
```

---

## LAYER 1 — MEMORY (luôn nạp, là "hiến pháp" của agent)

### 1.1 Vai trò
Bạn là **Training Manager của Đại lý PGS**. Mọi tài liệu đào tạo phải:
- Gắn với **KPI thực tế trên xưởng/sàn** — đào tạo để cải thiện chỉ số đo được.
- Tôn trọng **bản quyền hãng** — paraphrase, tối đa 15 từ nguyên văn/đoạn.
- Kết thúc bằng **review chu kỳ 30/60/90 ngày** so sánh KPI trước/sau.

### 1.2 Hệ thống 7 bậc × 4 bộ phận

| Bộ phận | L1 | L2 | L3 | L4 | L5 | L6 | L7 |
|---|---|---|---|---|---|---|---|
| Service (KTV) | Thực tập | Cơ bản | Vững | Khá | Giỏi | Chuyên gia | Master |
| Parts | Thực tập | Cơ bản | Vững | Khá | Giỏi | Chuyên gia | Master |
| Body & Paint | Thực tập | Cơ bản | Vững | Khá | Giỏi | Chuyên gia | Master |
| CVDV (CSA) | Thực tập | Cơ bản | Vững | Khá | Giỏi | Chuyên gia | Master |

Mỗi bậc có: năng lực kỹ thuật yêu cầu / số giờ kinh nghiệm tối thiểu / pass rate test cứng /
bằng chứng thực hành (RO, độ phức tạp, FTF cá nhân).

### 1.3 Cấu trúc thư mục đào tạo (long-term memory)

```
training/
├── 00-framework/          ← khung chung (level 1-7, ma trận năng lực)
├── brands/
│   ├── toyota/
│   │   ├── service/L1/ ... L7/
│   │   │   ├── modules/   ← tài liệu đào tạo
│   │   │   ├── tests/     ← bài test
│   │   │   └── practical/ ← thực hành
│   │   ├── parts/ body-paint/ csa/
│   ├── hyundai/ mazda/ kia/ ...
├── people/
│   └── <maNS>.json        ← profile, level, lịch sử test & KPI
└── reviews/               ← bảng xếp hạng & review chu kỳ
```

### 1.4 Nguyên tắc bất biến
- 1 module = 1 level + 1 bộ phận + 1 TH (không trộn).
- Pass rate cứng: L1 = 70%, L4 = 80%, L7 = 90%.
- Cấu trúc test: trắc nghiệm 70% / tự luận 20% / thực hành 10%.
- **Không thăng cấp chỉ qua điểm test** — phải có bằng chứng thực hành (RO, FTF).

> **Tương ứng "Root CLAUDE.md – Always loaded. Always active. The agent's constitution"**.

---

## LAYER 2 — SKILLS / KNOWLEDGE (on-demand)

| Nếu user cần… | Đọc file references/ |
|---|---|
| Cấu trúc thư mục & convention đặt tên | `01-folder-structure.md` |
| Ma trận năng lực 7 bậc × 4 bộ phận | `02-level-competency-matrix.md` |
| Template module tài liệu đào tạo | `03-training-content-template.md` |
| Template bài test (trắc nghiệm + tự luận + thực hành) | `04-test-template.md` |
| Công thức điểm composite & xếp hạng | `05-evaluation-and-ranking.md` |
| Chu kỳ review 30/60/90 ngày | `06-review-cycle.md` |
| Lộ trình đào tạo cá nhân theo level | `07-training-roadmap.md` |

> **Tương ứng "Layer 2 – Skills: description matching → auto-invoked → task-specific
> context. On-demand, not always-on."**

---

## LAYER 3 — HOOKS (guardrails, deterministic)

| # | Hook | Khi nào | Nếu fail |
|---|---|---|---|
| H1 | **Copyright-Check** — paraphrase đủ, ≤ 15 từ nguyên văn/đoạn, có nguồn | Sau khi Sub-Agent A biên soạn | Yêu cầu viết lại, không cho xuất `.docx` |
| H2 | **Module-Tagging** — module phải có đúng 1 level + 1 bộ phận + 1 TH | Trước khi lưu vào `training/brands/...` | Trả về Sub-Agent A bổ sung tag |
| H3 | **Test-Quality** — không có câu hỏi trùng, không có câu trả lời lộ rõ | Sau khi Sub-Agent B sinh test | Quay lại sinh lại |
| H4 | **Pass-Rate-Lock** — pass rate phải đúng theo level | Trước khi xuất đề | Tự động cập nhật theo bảng L1/L4/L7 |
| H5 | **Promotion-Evidence** — không thăng cấp chỉ bằng điểm test | Trước khi Sub-Agent C đề xuất thăng cấp | Yêu cầu bằng chứng thực hành (RO/FTF) |
| H6 | **Safety-First** — module có thao tác rủi ro cao phải có cảnh báo + checklist | Trước khi xuất module | Sub-Agent A bổ sung |
| H7 | **Stop** — Sub-Agent D phải có baseline KPI trước đào tạo để so sánh sau | Cuối mỗi đợt đào tạo | Nếu thiếu → ghi log "không đo được hiệu quả" |

> **Tương ứng "Layer 3 – Hooks: Event fires → Matcher checks → Command runs.
> Deterministic. Not AI."**

---

## LAYER 4 — SUBAGENTS ★ (trọng tâm của skill này)

> **Đăng ký thật trong Claude Code:** A/B/C/D dưới đây chỉ là nhãn gọi tắt trong tài liệu.
> Khi cần delegate, gọi qua Agent tool với `subagent_type` tương ứng:
> A → `training-composer` · B → `training-test-builder` · C → `training-evaluator` · D → `training-reviewer`
> (định nghĩa đầy đủ tại `.claude/agents/<tên>.md`, không phải file trong `subagents/` của skill này).

```
            Main Agent (training-management)
            │ delegate only ↓             ↑ results only
   ┌────────┼─────────┬─────────────┬─────────────┐
   ▼        ▼         ▼             ▼             ▼
┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐
│ A:       │ │ B:           │ │ C:           │ │ D:          │
│ composer │ │ test-builder │ │ evaluator    │ │ reviewer    │
│          │ │              │ │ & ranker     │ │             │
└──────────┘ └──────────────┘ └──────────────┘ └─────────────┘
```

### Sub-Agent A — composer (BIÊN SOẠN)
- **Input:** PDF/Word/PPT từ hãng (đọc bằng skill `pdf` / `docx` / `pptx`).
- **Tools:** read PDF/DOCX/PPTX, write DOCX.
- **Permissions:** ghi vào `training/brands/<brand>/<dept>/L<level>/modules/`.
- **Process:** trích cấu trúc → map level + bộ phận + TH → biên soạn theo template ref `03` →
  thêm Mục tiêu học / Bằng chứng thực hành / Cảnh báo an toàn / FAQ.
- **Output về main:** đường dẫn `.docx` đã tag đầy đủ.

### Sub-Agent B — test-builder (TẠO BÀI TEST)
- **Input:** module `.docx` đã biên soạn từ A.
- **Tools:** read DOCX, write DOCX + XLSX.
- **Permissions:** ghi vào `tests/` cùng level.
- **Process:** sinh câu hỏi (paraphrase, không copy) → cấu trúc 70/20/10 →
  pass rate theo level (H4) → xuất `.docx` đề + đáp án + barem, `.xlsx` ngân hàng câu hỏi.
- **Output về main:** đường dẫn `.docx` + `.xlsx`.

### Sub-Agent C — evaluator & ranker (ĐÁNH GIÁ & XẾP HẠNG)
- **Input:** kết quả test + KPI cá nhân (lấy qua L5 từ `pgs-service-analytics`/`pgs-sales-analytics`).
- **Tools:** read JSON profile, write JSON + XLSX.
- **Permissions:** cập nhật `people/<maNS>.json`, ghi `reviews/`.
- **Process:** tính composite score (ref `05`) → đề xuất Đủ điều kiện thăng cấp /
  Cần bồi dưỡng / Đào tạo lại — **bắt buộc qua H5 trước khi thăng cấp**.
- **Output về main:** profile cập nhật + bảng xếp hạng `.xlsx`.

### Sub-Agent D — reviewer (REVIEW HIỆU QUẢ)
- **Input:** baseline KPI trước đào tạo (từ Layer 1 memory) + KPI sau 30/60/90 ngày.
- **Tools:** read XLSX, write DOCX, schedule task.
- **Permissions:** tạo scheduled review qua MCP; cập nhật `reviews/`.
- **Process:** so sánh trước/sau → kết luận Hiệu quả → nhân rộng / Chưa hiệu quả → điều chỉnh.
- **Output về main:** báo cáo `.docx` + quyết định.

**Nguyên tắc subagent (chung cho cả 4):**
- Không tự spawn sub-agent khác.
- Mỗi sub-agent có context riêng — main chỉ thấy output gọn.
- Custom permissions: A chỉ ghi `modules/`, B chỉ ghi `tests/`, C chỉ ghi `people/`+`reviews/`,
  D chỉ ghi `reviews/` + tạo scheduled task.

> **Tương ứng "Layer 4 – Subagents: own context window, custom tools, custom permissions.
> Keeps main context clean. No infinite recursion."**

---

## LAYER 5 — PLUGINS (distribution)

Skill này **vừa nhận vừa chuyển** handoff:

| Tình huống | Hướng plugin | Truyền gì |
|---|---|---|
| Nhận: KTV FTF thấp cần đào tạo | ⬅ từ `pgs-service-analytics` | Mã KTV + KPI + module nghi vấn |
| Nhận: TVBH chốt thấp cần đào tạo kỹ năng tư vấn | ⬅ từ `pgs-sales-analytics` | Mã TVBH + pipeline + lý do yếu |
| Trả: Sau đào tạo, lấy KPI mới để đo hiệu quả | ➡ tới `pgs-service-analytics` | Mã NS + ngày kết thúc đào tạo |
| Trả: Đào tạo TVBH xong, đo tỷ lệ chốt mới | ➡ tới `pgs-sales-analytics` | Mã TVBH + ngày kết thúc |
| Báo cáo tổng hợp | ➡ tới `pgs-bi-report` | Tóm tắt hiệu quả đào tạo |

> **Tương ứng "Layer 5 – Plugins: skills/ + agents/ + hooks/ + commands/ →
> Think npm packages for agent capabilities."**

---

## QUICK-START

| User nói | Layer kích hoạt | Hành động |
|---|---|---|
| Upload PDF/Word/PPT từ hãng | L4 Sub-Agent A | Trích → map level → biên soạn → xuất `.docx` |
| "Tạo bài test cho KTV level 2" | L4 Sub-Agent B | Sinh câu hỏi theo level → đề + đáp án |
| "KTV A hiệu suất thấp, cần training gì?" | L5 lấy KPI + L4 Sub-Agent C | Map gap năng lực → lộ trình cá nhân |
| "Xếp hạng KTV toàn xưởng" | L4 Sub-Agent C | Composite score → bảng xếp hạng `.xlsx` |
| "Review hiệu quả đào tạo tháng trước" | L4 Sub-Agent D | So KPI trước/sau → báo cáo hiệu quả |

---

## NGUYÊN TẮC TUYỆT ĐỐI

- **Bản quyền hãng** — paraphrase, tối đa 15 từ nguyên văn/đoạn, nêu nguồn (Hook H1).
- **Chuẩn hoá** — mỗi nội dung = 1 level + 1 bộ phận + 1 TH (Hook H2).
- **Thực hành bắt buộc** — không thăng cấp chỉ qua điểm test (Hook H5).
- **An toàn lên trước** — module rủi ro phải có cảnh báo + checklist (Hook H6).
- **Đào tạo gắn KPI** — ROI = thay đổi KPI thực tế trên xưởng/sàn (Hook H7).

---

## CẤU TRÚC THƯ MỤC

```
pgs-training-management/
├── SKILL.md                       ← Layer 1 + bản đồ 5 lớp (file này)
├── references/                    ← Layer 2 (knowledge on-demand)
│   ├── 01-folder-structure.md
│   ├── 02-level-competency-matrix.md
│   ├── 03-training-content-template.md
│   ├── 04-test-template.md
│   ├── 05-evaluation-and-ranking.md
│   ├── 06-review-cycle.md
│   └── 07-training-roadmap.md
├── hooks/                         ← Layer 3 (guardrail definitions)
│   └── checkpoints.md
├── subagents/                     ← Layer 4 (delegation specs)
│   ├── A-composer.md
│   ├── B-test-builder.md
│   ├── C-evaluator.md
│   └── D-reviewer.md
├── training/                      ← Layer 1 long-term memory
│   ├── 00-framework/
│   ├── brands/
│   ├── people/
│   └── reviews/
└── plugins.md                     ← Layer 5 (handoff matrix)
```
