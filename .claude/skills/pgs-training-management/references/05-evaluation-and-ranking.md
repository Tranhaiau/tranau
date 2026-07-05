# Reference 05 — Đánh giá Composite & Xếp hạng

> **Khi nào load:** Sub-Agent C (Evaluator) tổng hợp đánh giá NS định kỳ;
> hoặc khi user hỏi "Xếp hạng KTV trong tổ", "Ai đủ điều kiện thăng cấp".

---

## 1. Triết lý đánh giá

PGS dùng công thức composite để tránh 2 cực:
1. **Chỉ test:** NS giỏi thi nhưng kém thực tế → vẫn được thăng (sai).
2. **Chỉ KPI thực:** NS có KPI tốt do may mắn (case dễ) hoặc gian lận → vẫn thăng (sai).

Composite balance:
```
Diem_composite = KPI_thực × 60% + Test_score × 40%
```

Vì sao 60/40:
- KPI thực phản ánh trực tiếp giá trị NS tạo ra → trọng số cao hơn.
- Test đảm bảo nền tảng kiến thức vững → trọng số đáng kể.
- Tỷ lệ này đã hiệu chỉnh từ 50/50 ban đầu sau 2 năm vận hành PGS.

---

## 2. Công thức điểm composite chi tiết

### 2.1 Cho KTV

```python
def composite_score_KTV(kpi_data, test_score, level_target):
    """
    KPI thực 60% + Test 40%.
    KPI thực dựa trên 4 thành phần: FTF, comeback, gio_per_RO, n_RO.
    """
    # Quy KPI thực về thang 100
    kpi_score_components = {
        'FTF': kpi_data['ftf_rate'] * 100,                    # 0.92 → 92
        'comeback_inv': (1 - kpi_data['comeback_rate']) * 100, # 0.04 → 96 (đảo: thấp = tốt)
        'speed_inv': speed_to_score(kpi_data['gio_per_RO'], level_target),  # quy gio/RO → score
        'volume': volume_to_score(kpi_data['n_RO'], level_target)
    }

    # Trọng số 4 KPI
    weights_KPI = {'FTF': 0.40, 'comeback_inv': 0.30, 'speed_inv': 0.15, 'volume': 0.15}
    kpi_total = sum(kpi_score_components[k] * weights_KPI[k] for k in weights_KPI)

    # Composite
    composite = kpi_total * 0.60 + test_score * 0.40
    return {
        'composite': composite,
        'kpi_total': kpi_total,
        'test_score': test_score,
        'breakdown_KPI': kpi_score_components
    }

def speed_to_score(gio_per_RO, level):
    """
    Quy gio_per_RO → score 0-100.
    L1: target 5h → 100đ; > 7h → 0đ
    L3: target 4h → 100đ; > 6h → 0đ
    L5: target 3h → 100đ; > 5h → 0đ
    """
    targets = {1: (5, 7), 2: (4.5, 6.5), 3: (4, 6),
               4: (3.5, 5.5), 5: (3, 5), 6: (3, 5), 7: (3, 5)}
    target_max, fail = targets.get(level, (4, 6))
    if gio_per_RO <= target_max:
        return 100
    if gio_per_RO >= fail:
        return 0
    # linear giữa 2 mốc
    return (1 - (gio_per_RO - target_max) / (fail - target_max)) * 100

def volume_to_score(n_RO, level):
    """
    Quy số RO/kỳ → score.
    L1: 25 RO = 100đ
    L3: 35 RO = 100đ
    L5: 40 RO = 100đ
    """
    targets = {1: 25, 2: 30, 3: 35, 4: 38, 5: 40, 6: 35, 7: 30}  # L6-L7 ít RO vì kèm cặp
    target = targets.get(level, 35)
    return min(n_RO / target * 100, 110)   # cap 110 (over-target có bonus nhẹ)
```

### 2.2 Cho CVDV

```python
def composite_score_CVDV(kpi_data, test_score, level_target):
    """
    KPI thực: PT/RO + CSI + no_show + tỷ lệ chốt hẹn.
    """
    kpi_components = {
        'PT_per_RO': pt_to_score(kpi_data['PT_per_RO_pct_team']),  # vs team avg
        'CSI': csi_to_score(kpi_data['csi_mean']),
        'no_show_inv': (1 - kpi_data['no_show_rate']) * 100,
        'don_tiep': kpi_data['csi_don_tiep'] * 20   # thang 5 → thang 100
    }
    weights = {'PT_per_RO': 0.30, 'CSI': 0.40, 'no_show_inv': 0.15, 'don_tiep': 0.15}
    kpi_total = sum(kpi_components[k] * weights[k] for k in weights)

    composite = kpi_total * 0.60 + test_score * 0.40
    return {'composite': composite, 'kpi_total': kpi_total, 'test_score': test_score,
            'breakdown_KPI': kpi_components}

def pt_to_score(pct_vs_team):
    """
    PT/RO của CVDV / TB team. Score:
    - 1.0 (= TB) → 80đ
    - 1.1 → 90đ
    - 1.3+ → 100đ
    - 0.85 → 60đ
    - < 0.7 → 0đ
    """
    if pct_vs_team >= 1.3: return 100
    if pct_vs_team >= 1.1: return 80 + (pct_vs_team - 1.0) * 100
    if pct_vs_team >= 0.85: return 60 + (pct_vs_team - 0.85) * 80
    if pct_vs_team >= 0.7: return (pct_vs_team - 0.7) * 60 / 0.15
    return 0

def csi_to_score(csi_mean):
    """Thang 1-5 → 0-100."""
    if csi_mean >= 4.7: return 100
    if csi_mean >= 4.4: return 85 + (csi_mean - 4.4) * 50
    if csi_mean >= 4.0: return 60 + (csi_mean - 4.0) * 62.5
    if csi_mean >= 3.5: return 40 + (csi_mean - 3.5) * 40
    return max(0, csi_mean * 11)
```

### 2.3 Cho PT (Phụ tùng)

```python
def composite_score_PT(kpi_data, test_score, level_target):
    """
    KPI thực: lead_time, accuracy_kho, ti_le_thieu_hang, ngan_sach_ton_kho.
    """
    kpi_components = {
        'lead_time': lead_time_to_score(kpi_data['lead_time_TB_ngay']),
        'accuracy': kpi_data['accuracy_kho_pct'],   # đã 0-100
        'thieu_hang_inv': (1 - kpi_data['ti_le_thieu_hang']) * 100,
        'ton_kho_eff': inventory_eff_to_score(kpi_data['ton_kho_VND_per_RO'])
    }
    weights = {'lead_time': 0.30, 'accuracy': 0.30, 'thieu_hang_inv': 0.25, 'ton_kho_eff': 0.15}
    kpi_total = sum(kpi_components[k] * weights[k] for k in weights)
    return {'composite': kpi_total * 0.60 + test_score * 0.40,
            'kpi_total': kpi_total, 'test_score': test_score,
            'breakdown_KPI': kpi_components}
```

### 2.4 Cho DS (Đồng sơn)

```python
def composite_score_DS(kpi_data, test_score, level_target):
    """
    KPI thực: chat_luong_son, thoi_gian_per_panel, redo_rate, KH_satisfaction_DS.
    """
    kpi_components = {
        'chat_luong': kpi_data['chat_luong_son_diem'] * 20,   # thang 5
        'speed': speed_DS_to_score(kpi_data['gio_per_panel']),
        'redo_inv': (1 - kpi_data['redo_rate']) * 100,
        'KH_sat': kpi_data['CSI_DS'] * 20
    }
    weights = {'chat_luong': 0.40, 'speed': 0.20, 'redo_inv': 0.25, 'KH_sat': 0.15}
    kpi_total = sum(kpi_components[k] * weights[k] for k in weights)
    return {'composite': kpi_total * 0.60 + test_score * 0.40,
            'kpi_total': kpi_total, 'test_score': test_score,
            'breakdown_KPI': kpi_components}
```

---

## 3. Xếp hạng trong tổ / chi nhánh

### 3.1 Quy tắc xếp hạng

```python
def rank_within_team(eval_records, bo_phan, level=None):
    """
    Xếp hạng NS trong cùng bộ phận (và level nếu chỉ định).
    Hook H7: chỉ rank NS có mẫu KPI ≥ ngưỡng.
    """
    df = pd.DataFrame(eval_records)
    df = df[df['bo_phan'] == bo_phan]
    if level:
        df = df[df['level_hien_tai'] == level]

    # Hook H7: lọc mẫu đủ
    df = df[df['n_RO_in_period'] >= 30]   # cứng 30 RO/kỳ

    df_sorted = df.sort_values('composite', ascending=False).reset_index(drop=True)
    df_sorted['rank'] = df_sorted.index + 1
    df_sorted['percentile'] = (1 - df_sorted['rank'] / len(df_sorted)) * 100

    # Phân nhóm
    def classify(p):
        if p >= 80: return 'Top 20% (xuất sắc)'
        if p >= 60: return 'Top 40% (giỏi)'
        if p >= 40: return 'Trung bình'
        if p >= 20: return 'Cần cải thiện'
        return 'Đáy nhóm — cần can thiệp'

    df_sorted['nhom_xep_hang'] = df_sorted['percentile'].apply(classify)
    return df_sorted
```

### 3.2 Bảng phân nhóm hành động

| Nhóm xếp hạng | Hành động đề xuất |
|---|---|
| Top 20% (xuất sắc) | Đề xuất thăng cấp (nếu đủ điều kiện); kèm cặp NS L thấp |
| Top 40% (giỏi) | Module training nâng cao; chuẩn bị thăng cấp |
| Trung bình | Module training duy trì; theo dõi |
| Cần cải thiện | Module training booster; review T+30/T+60 |
| Đáy nhóm | Diagnose pattern → handoff sang Service playbook + module training intensive |

### 3.3 Code: phân loại theo phân vị từng KPI thành phần

```python
def diagnose_weakness(eval_record, team_avg):
    """
    Tìm KPI nào của NS yếu nhất so với team → recommend module training.
    """
    components = eval_record['breakdown_KPI']
    weak_kpis = []
    for k, v in components.items():
        team_v = team_avg.get(k, 70)
        if v < team_v * 0.85:   # yếu hơn TB > 15%
            weak_kpis.append({'kpi': k, 'cua_NS': v, 'team_avg': team_v,
                              'gap_pct': (team_v - v) / team_v * 100})

    return sorted(weak_kpis, key=lambda x: -x['gap_pct'])
```

---

## 4. Mapping KPI yếu → Module training

### 4.1 KTV

```python
KPI_WEAK_TO_MODULE_KTV = {
    'FTF': ['quy_trinh_chan_doan', 'sua_dung_lan_dau', 'kiem_tra_truoc_ban_giao'],
    'comeback_inv': ['quality_check', 'kiem_tra_truoc_ban_giao'],
    'speed_inv': ['thoi_gian_chuan_BDĐK', 'su_dung_dung_cu', 'quy_trinh_lam_viec'],
    'volume': ['quy_trinh_lam_viec', 'multitasking_kho_xuong']  # ít RO = chậm hoặc nghỉ nhiều
}
```

### 4.2 CVDV

```python
KPI_WEAK_TO_MODULE_CVDV = {
    'PT_per_RO': ['ky_nang_tu_van_phu_tung', 'phan_tich_lich_su_xe'],
    'CSI': ['ky_nang_giao_tiep_KH', 'xu_ly_phan_nan'],
    'no_show_inv': ['quy_trinh_xac_nhan_hen', 'ky_nang_dien_thoai'],
    'don_tiep': ['don_tiep_chuyen_nghiep']
}
```

### 4.3 PT

```python
KPI_WEAK_TO_MODULE_PT = {
    'lead_time': ['dam_phan_supplier', 'du_bao_nhu_cau_PT'],
    'accuracy': ['quy_trinh_kiem_kho', 'su_dung_he_thong_DMS'],
    'thieu_hang_inv': ['du_bao_nhu_cau_PT', 'muc_ton_kho_an_toan'],
    'ton_kho_eff': ['toi_uu_chi_phi_ton_kho']
}
```

### 4.4 DS

```python
KPI_WEAK_TO_MODULE_DS = {
    'chat_luong': ['ky_thuat_son_co_ban', 'pha_son_chinh_xac'],
    'speed': ['quy_trinh_son_chuan', 'su_dung_buong_son'],
    'redo_inv': ['kiem_tra_chat_luong_DS', 'quality_check'],
    'KH_sat': ['ky_nang_giao_xe_DS']
}
```

---

## 5. Báo cáo đánh giá định kỳ (output Sub-Agent C)

### 5.1 Template báo cáo cá nhân

```markdown
# Đánh giá KTV001 — Phạm Văn A — Kỳ T4/2026

**Bộ phận:** KTV — Level hiện tại: L2 — Mục tiêu kỳ này: L3

## 1. Điểm composite: 76.5 / 100
- KPI thực: 71.2 (60%) → 42.7
- Test (KTV-L3-T015 lần 1): 84% → 33.6
- **Composite: 42.7 + 33.6 = 76.3**

## 2. Phân tích KPI thực

| Thành phần | Score | Diễn giải |
|---|---|---|
| FTF (40%) | 71 | FTF 0.71 vs team 0.92 — yếu rõ rệt |
| Comeback inv (30%) | 89 | Comeback 0.11 vs team 0.04 — yếu |
| Speed inv (15%) | 85 | gio/RO 4.2h vs L3 target 4h — chấp nhận |
| Volume (15%) | 100 | 38 RO/kỳ vs target 35 — vượt nhẹ |

## 3. Test KTV-L3-T015 (đề A_v1, 12/05/2026)
- Trắc nghiệm: 27/30 (90%)
- Tự luận: 21/25 (84%)
- Thực hành: 10/15 (67%) — yếu phần "thực hiện thao tác kiểm tra"
- **Tổng: 84%** — pass ngưỡng L3 (80%)

## 4. So với team (level L2 chi nhánh Đồng Nai, n=8 KTV)
- Rank: 6/8 — Top 25% từ dưới lên
- Nhóm: **Cần cải thiện**

## 5. KPI yếu nhất (so team)
1. FTF: 71 vs team 92 → gap 23%
2. Comeback: gap 18%

## 6. Đủ điều kiện thăng L3?
**KHÔNG ĐỦ.** Lý do:
- ❌ FTF 0.71 < yêu cầu L3 = 0.90
- ❌ Comeback 0.11 > giới hạn L3 = 0.05
- ✓ Test 84% ≥ pass-rate L3 = 80%
- ✓ On-job 14 tháng ≥ yêu cầu L3 = 12 tháng
- ✓ Mẫu 38 RO ≥ yêu cầu 30

## 7. Module training đề xuất
- KTV-L3-015 Chẩn đoán OBD nâng cao (đã hoàn thành test)
- KTV-L3-013 Sửa hệ thống phanh ABS (chưa học)
- Booster: kèm cặp 4 tuần bởi KTV017 (L5)

## 8. Lộ trình
- Hoàn thành 2 module mới + kèm cặp: hết 06/2026
- Cải thiện FTF lên ≥ 0.90 + comeback ≤ 0.05 (mẫu ≥ 30 RO mới): hết 07/2026
- Re-evaluate L3 vào: 15/07/2026

## 9. Bằng chứng
- KPI baseline: 38 RO trong T4/2026
- Phiếu thi: PT-2026-05-12-KTV001-T015
- Mẫu RO comeback: RO20260403-A1, RO20260408-B5, ..., (xem chi tiết evaluations/KTV001_DongNai_2026-05.json)
```

### 5.2 Template báo cáo team

```markdown
# Đánh giá Tổ KTV — Đồng Nai — Kỳ T4/2026 (n=8 KTV)

## Bảng xếp hạng

| Rank | Mã NS | Tên | Level | Composite | Nhóm | Đề xuất |
|---|---|---|---|---|---|---|
| 1 | KTV017 | Trần Văn H | L5 | 95.2 | Top 20% xuất sắc | Đề xuất L6, làm trainer |
| 2 | KTV004 | Lê Văn B | L4 | 89.7 | Top 20% xuất sắc | Module L5, kèm cặp L1 |
| 3 | KTV012 | Nguyễn Văn D | L3 | 86.4 | Top 40% giỏi | Chuẩn bị L4 |
| 4 | KTV023 | Bùi Văn E | L3 | 81.5 | Top 40% giỏi | Module L4 chuẩn bị |
| 5 | KTV007 | Hoàng Văn F | L2 | 78.9 | Trung bình | Module duy trì |
| 6 | KTV001 | Phạm Văn A | L2 | 76.3 | Cần cải thiện | Module booster + kèm cặp |
| 7 | KTV029 | Trần Văn D | L1 (mới 45d) | 65.2 | Onboarding | Tiếp tục onboarding 45 ngày nữa |
| 8 | KTV015 | Đỗ Văn G | L2 | 58.4 | Đáy nhóm | Diagnose intensive + module bắt buộc |

## Tổng hợp KPI tổ
- Composite TB: 79.0 (vs đại lý PGS hệ thống TB 82.0) — dưới TB
- FTF tổ: 0.92 (đạt benchmark)
- Comeback tổ: 0.04 (đạt)
- DT/RO tổ: 5.7tr (đạt)

## Vấn đề tổ
1. KTV015 đáy nhóm — escalate Trưởng phòng dịch vụ
2. KTV001 cần kèm cặp — handoff KTV017 làm mentor
3. KTV029 onboarding tốt, tiếp tục lộ trình

## Handoff cross-skill
- KTV001, KTV015 → đề xuất sang `pgs-service-analytics` xem có pattern thuộc TH-K01 không
```

---

## 6. Đặc biệt: NS rớt liên tiếp 2 kỳ

```python
def detect_chronic_underperformer(history_records):
    """
    Phát hiện NS đã rớt nhóm "đáy" hoặc "cần cải thiện" 2+ kỳ liên tiếp.
    """
    df = pd.DataFrame(history_records)
    df = df.sort_values(['ma_NS', 'ky'], ascending=[True, False])

    chronic = []
    for ma_NS, group in df.groupby('ma_NS'):
        recent_2 = group.head(2)
        if len(recent_2) < 2:
            continue
        if all(recent_2['nhom_xep_hang'].isin(['Đáy nhóm — cần can thiệp', 'Cần cải thiện'])):
            chronic.append({
                'ma_NS': ma_NS,
                'composite_2_ky': recent_2['composite'].tolist(),
                'verdict': 'CHRONIC_UNDERPERFORMER',
                'recommended': 'Mời họp 1-1 với Trưởng phòng + plan cải thiện 30 ngày + có thể đề xuất chuyển bộ phận nếu plan thất bại'
            })
    return chronic
```

---

## 7. Quy tắc bất biến

1. **Composite = KPI 60% + Test 40%** — không thay tỉ lệ tuỳ tiện.
2. **Mẫu KPI < 30 RO/kỳ → không xếp hạng** — Hook H7.
3. **Pass-rate test cứng theo level** — Hook H4.
4. **NS không thăng cấp phải có gap_to_close + ngày review lại** — Hook H5.
5. **Pattern lỗi đạo đức (vd CVDV upsell ép) → không tính KPI cao** — bị giảm thẳng.
6. **NS rớt 2 kỳ liên tiếp → escalate** — không bỏ qua.
7. **Mỗi đánh giá phải có bằng chứng (mã RO, mã phiếu thi)** — truy vết được.

---

## 8. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| NS có KPI cao nhưng test fail | Không thăng. Cho retake test sau 30 ngày học bù |
| NS có test cao nhưng KPI thấp | Không thăng. Plan cải thiện KPI 60-90 ngày |
| NS mới (< 90 ngày) chưa đủ mẫu | Đánh giá riêng theo onboarding checklist, không xếp hạng cùng team |
| NS chuyển bộ phận giữa kỳ | Lịch sử đánh giá giữ nguyên, kỳ này tính trên bộ phận mới (mẫu giảm) |
| Team có 2 NS đồng điểm composite | Phân theo: KPI thực cao hơn → trên |
| NS từ chối thi nhưng KPI tốt | Không thăng. Yêu cầu thi để duy trì level đã có |
| Hãng có chứng nhận riêng (T-Tep, GBS) | Cộng vào composite +5 đến +10 điểm bonus |
