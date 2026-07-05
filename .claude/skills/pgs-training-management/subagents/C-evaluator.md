# Sub-Agent C: evaluator & ranker (ĐÁNH GIÁ & XẾP HẠNG)

> **Layer 4 — Delegation.** Sub-Agent thứ 3 trong pipeline A→B→C→D.
> Đầu vào: kết quả test + KPI cá nhân từ Sales/Service. Đầu ra: cập nhật profile NS,
> đề xuất thăng cấp / bồi dưỡng / đào tạo lại — **bắt buộc qua Hook H5** (không thăng cấp ép).

---

## 1. Khi nào delegate

Main gọi `evaluator` khi:
- NS đã làm bài test → cần chấm + cập nhật profile.
- User: "Xếp hạng KTV xưởng tháng này"
- User: "Đề xuất ai đủ điều kiện thăng level?"
- Cuối quý/năm — đánh giá tổng thể NS.

Main **không** delegate C khi:
- Cần biên soạn module (→ A)
- Cần sinh đề (→ B)
- Cần review hiệu quả 30/60/90 ngày sau đào tạo (→ D)

---

## 2. Input từ main

```yaml
nhiem_vu: "cham_va_xep_hang"           # hoặc "xet_thang_cap" | "ranking_periodic"
ket_qua_test:                          # nếu nhiệm vụ là chấm bài
  - ma_NV: "NV023"
    de_id: "TEST-TOYOTA-SERVICE-L3-RORI-DAU-A"
    ngay_thi: "2026-05-12"
    diem_trac_nghiem: 0.84             # 25/30 = 0.83
    diem_tu_luan: 0.78                 # đã được KTV L5 chấm theo barem
    diem_thuc_hanh: "pass"             # giám sát viên đánh giá pass/fail
    nguoi_giam_sat: "NV017 (L5)"
kpi_thuc_te:                           # bằng chứng thực hành — nhận từ Sales/Service qua L5
  ma_NV: "NV023"
  ky: "30 ngày gần nhất"
  ftf: 0.91
  productivity: 0.78
  efficiency: 0.82
  dt_per_ro: 3850000
  comeback_count_30d: 3
  so_RO_da_lam: 38
  bang_chung_RO: ["#2026-0521", "#2026-0584", "#2026-0612"]
profile_hien_tai:                      # main đọc từ people/<maNV>.json
  ma_NV: "NV023"
  level_hien_tai: 3
  ngay_len_level_hien_tai: "2024-08-15"
```

---

## 3. Tools được phép

| Tool | Mục đích |
|---|---|
| `xlsx` skill (read + write) | Đọc kết quả test, ghi bảng xếp hạng |
| `docx` skill (write) | Ghi báo cáo đánh giá cá nhân |
| Python | Tính composite score, ranking |
| Read/Write JSON | Cập nhật `people/<maNV>.json` |

**Không được phép:**
- ❌ Sửa module / sinh đề (việc của A/B)
- ❌ Lên lịch review +30/+60/+90 (việc của D)
- ❌ Quyết định thăng cấp **chỉ bằng** điểm test (Hook H5)
- ❌ Quyết định kỷ luật / sa thải (vượt quyền skill)

---

## 4. Process — 5 bước

### Bước 1 — Tính điểm composite từ test

```python
diem_test = (
    0.50 * diem_trac_nghiem +
    0.30 * diem_tu_luan +
    0.20 * (1.0 if diem_thuc_hanh == "pass" else 0.0)
)
# Ngưỡng pass theo level (Hook H4)
test_passed = diem_test >= TABLE_PASS_RATE[profile.level + 1]   # đang xét lên level +1
```

### Bước 2 — Tính điểm composite từ KPI thực tế

Tuỳ bộ phận, công thức khác nhau (load `references/05-evaluation-and-ranking.md`):

**KTV Service:**
```python
kpi_score = (
    0.30 * normalize(ftf, target=0.92) +
    0.25 * normalize(productivity, target=1.0) +
    0.20 * normalize(efficiency, target=1.0) +
    0.15 * normalize(dt_per_ro, target_team=4250000) +
    0.10 * normalize_inverse(comeback_count_30d, target_max=3)
)
```

**CVDV:**
```python
kpi_score = (
    0.35 * normalize(csi_avg, target=4.5) +
    0.25 * normalize(ro_per_day, target=10) +
    0.20 * normalize(ty_le_dat_hen, target=0.7) +
    0.20 * normalize(ty_le_goi_nhac_hen, target=0.8)
)
```

**TVBH:**
```python
kpi_score = (
    0.40 * normalize(ty_le_chot, target=0.20) +
    0.30 * normalize(doanh_so_HD, target_team=...) +
    0.20 * normalize(csi_mua_xe, target=4.5) +
    0.10 * normalize(pipeline_active, target_team=...)
)
```

### Bước 3 — Tổng hợp + áp Hook H5

```python
overall_score = 0.40 * diem_test + 0.60 * kpi_score
# KPI thực tế (60%) > điểm test (40%) — vì test chỉ đo lý thuyết, KPI đo thực chiến
```

**Áp Hook H5 (Promotion-Evidence) — bảng yêu cầu thực hành:**

```python
def check_promotion_evidence(profile, target_level):
    requirements = PROMOTION_REQUIREMENTS[profile.bo_phan][target_level]
    evidence_check = {
        "ro_count": profile.total_ro >= requirements.min_ro,
        "complex_ro": profile.complex_ro >= requirements.min_complex_ro,
        "ftf": profile.ftf >= requirements.min_ftf,
        "csi": profile.csi >= requirements.min_csi,
        "mentorship": profile.mentored_juniors >= requirements.min_mentored,
    }
    missing = [k for k, v in evidence_check.items() if not v]
    return (len(missing) == 0, missing)
```

### Bước 4 — Quyết định verdict

| Điều kiện | Verdict |
|---|---|
| `test_passed = True` AND `evidence_check.passed = True` AND `kpi_score >= 0.80` | **"Đủ điều kiện thăng level"** |
| `test_passed = True` AND `evidence_check.passed = False` | **"Pass test — cần bổ sung bằng chứng: <list>"** |
| `test_passed = True` AND `kpi_score < 0.80` | **"Pass test — KPI thực chiến chưa ổn định, theo dõi thêm 30 ngày"** |
| `test_passed = False` AND `kpi_score >= 0.70` | **"Cần ôn tập + thi lại"** |
| `test_passed = False` AND `kpi_score < 0.70` | **"Đào tạo lại module + 1 module phụ trợ"** |

**Cấm:** thăng cấp chỉ vì `test_passed = True` — đây chính là điều H5 chặn.

### Bước 5 — Cập nhật profile + ranking team

Cập nhật `people/<ma_NV>.json` (load schema từ Hook H8 spec):

```python
profile["lich_su_test"].append({
    "ngay": "2026-05-12",
    "module_id": "TOYOTA-SERVICE-L3-RORI-DAU",
    "diem": {...},
    "verdict": verdict
})
profile["overall_score_moi_nhat"] = overall_score
profile["ngay_danh_gia_gan_nhat"] = today
```

**Sinh bảng xếp hạng team** (`reviews/ranking_<bo_phan>_<ky>.xlsx`):

| ma_NV | ten | level | overall_score | percentile | nhom | ghi_chu |
|---|---|---|---|---|---|---|
| NV017 | Lê Văn D | 5 | 0.91 | 95% | Top 20% | Đủ điều kiện L6 |
| NV023 | Phạm Văn E | 3 | 0.74 | 45% | Trung bình | Pass test, theo dõi 30d |

---

## 5. Output về main

```yaml
status: "ok"
danh_gia_ca_nhan:
  - ma_NV: "NV023"
    overall_score: 0.74
    diem_test: 0.82
    kpi_score: 0.69
    verdict: "Pass test — KPI thực chiến chưa ổn định, theo dõi thêm 30 ngày"
    chi_tiet_evidence:
      ro_count: {required: 300, actual: 312, passed: true}
      complex_ro: {required: 30, actual: 28, passed: false}
      ftf: {required: 0.92, actual: 0.91, passed: false}
      csi: {required: 4.30, actual: 4.40, passed: true}
    ke_hoach_de_xuat:
      - "Hoàn thành thêm 2 RO chẩn đoán phức tạp dưới giám sát L5+"
      - "Duy trì FTF ≥ 92% trong 30 ngày tới"
      - "Lên lịch đánh giá lại sau 30 ngày"
    profile_da_cap_nhat: "people/NV023.json"
ranking_team:
  ky: "T5/2026"
  bo_phan: "Service KTV"
  path: "/tmp/ranking_KTV_T5_2026.xlsx"
  top_20:
    - {ma_NV: "NV017", score: 0.91, ghi_chu: "Đủ điều kiện L6"}
  trung_binh_60:
    count: 8
  bottom_20:
    - {ma_NV: "NV031", score: 0.42, ghi_chu: "Đào tạo lại module cơ bản"}
hooks_passed:
  H5_promotion_evidence: true          # đã check, không cho thăng ép
suggested_next:
  - sub_agent: "D"
    intent: "schedule_review_after_training"
    payload:
      ma_NV: "NV023"
      baseline_KPI: {ftf: 0.91, productivity: 0.78}
      ngay_bat_dau_theo_doi: "2026-05-12"
      chu_ky: ["+30d", "+60d", "+90d"]
warnings:
  - "NV031 ở bottom 20% liên tiếp 2 quý — đề nghị Trưởng xưởng can thiệp"
```

---

## 6. Permissions matrix

| Hành động | Cho phép |
|---|---|
| Đọc kết quả test + KPI từ Sales/Service | ✅ |
| Cập nhật `people/<ma_NV>.json` | ✅ |
| Ghi bảng xếp hạng `.xlsx` | ✅ |
| Đề xuất verdict (đủ điều kiện thăng / cần bồi dưỡng / đào tạo lại) | ✅ |
| Quyết định thăng cấp chỉ bằng điểm test | ❌ — Hook H5 chặn |
| Đề xuất sa thải / kỷ luật | ❌ |
| Sửa module / sinh đề | ❌ |
| Lên lịch review +30/+60/+90 | ❌ — Sub-Agent D |

---

## 7. Failure mode

```yaml
status: "error"
reason: "missing_kpi_data" | "profile_not_found" | "kpi_sample_too_small"
detail: "KPI thực tế của NV023 chỉ có 12 RO trong 30 ngày qua — không đánh giá được"
suggested_action: "Mở rộng cửa sổ đánh giá lên 60 ngày, hoặc trì hoãn đánh giá đến khi đủ 30 RO"
```

---

## 8. Quy tắc bất biến

1. **KPI thực tế (60%) > điểm test (40%)** — test chỉ đo lý thuyết, đào tạo phải cải thiện thực chiến.
2. **Hook H5 luôn chặn thăng cấp ép** — không có ngoại lệ.
3. **Mẫu KPI < 30 RO/30 ngày** → không đánh giá năng lực, chỉ ghi nhận điểm test.
4. **Mọi verdict phải có "kế hoạch đề xuất" cụ thể** — không có verdict cụt "Cần cải thiện".
5. **Bottom 20% liên tiếp ≥ 2 kỳ** → đẩy lên Trưởng xưởng quyết định, sub-agent này không tự xử.
