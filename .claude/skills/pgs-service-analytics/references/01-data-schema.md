# Reference 01 — Data Schema cho file Xưởng Dịch vụ

> **Khi nào load:** User upload file Excel chưa xác định cột; hoặc khi sub-agent báo `missing_column`;
> hoặc khi cần verify cấu trúc UIO/RO/PT/Hẹn/CSI.

---

## 1. Tổng quan các loại file Service

PGS Service quản lý ≥ 5 loại file song song. **Phải đọc đúng schema mới cross-reference được.**

| File | Đơn vị bản ghi | Tần suất | Nguồn |
|---|---|---|---|
| **UIO** (Units in Operation) | 1 VIN = 1 dòng | Snapshot tháng | Cyber DMS export |
| **RO** (Repair Order) | 1 RO = 1 dòng (header) | Real-time | Cyber DMS |
| **RO_chi_tiet** | 1 dòng = 1 đầu việc / 1 phụ tùng | Real-time | Cyber DMS |
| **Hẹn** (Appointment) | 1 hẹn = 1 dòng | Real-time | Cyber DMS / Web/Zalo |
| **CSI** (Customer Satisfaction Index) | 1 phiếu = 1 dòng | Sau RO 3-7 ngày | Khảo sát |
| **BDĐK_due** (lịch BDĐK) | 1 VIN × mốc km | Real-time | Tính từ UIO |

---

## 2. File UIO — `uio_<chi_nhanh>_<YYYYMM>.xlsx`

### 2.1 Định nghĩa UIO

UIO = **Units in Operation** = tất cả xe **PGS đã bán** đang lưu thông trên địa bàn,
chưa quá tuổi đời cut-off (thường 7-10 năm tùy chính sách hãng).

### 2.2 Cột bắt buộc

| STT | Tên cột | Bí danh | Kiểu | Ràng buộc |
|---|---|---|---|---|
| 1 | `vin` | so_khung, frame_no | string(17) | unique |
| 2 | `ngay_ban` | ngay_HD, ngay_giao | date | ≤ today |
| 3 | `model` | xe, ten_xe | string | có trong master |
| 4 | `nam_SX` | mfg_year | int | hợp lý vs ngay_ban |
| 5 | `mau_xe` | mau, color | string | optional |
| 6 | `khach_hang_id` | ma_KH | string | có thể trùng (1 KH nhiều xe) |
| 7 | `sdt_KH` | phone | string | format VN |
| 8 | `email_KH` | email | string | optional |
| 9 | `dia_chi` | address | string | optional |
| 10 | `tinh` | province | string | địa bàn |
| 11 | `huyen` | district | string | optional |
| 12 | `dai_ly_ban_dau` | dealer_origin | string | PGS hoặc đại lý khác |
| 13 | `lan_vao_xuong_cuoi` | last_visit_date | date | có thể null |
| 14 | `km_lan_cuoi` | last_km | number | optional |
| 15 | `BDĐK_tiep_theo_du_kien` | next_BDĐK | date | ước tính từ km/thời gian |
| 16 | `trang_thai` | status | enum | active/da_thanh_ly/da_doi_chu/khong_lien_lac |

### 2.3 Validate code

```python
import pandas as pd

REQUIRED_UIO = ['vin', 'ngay_ban', 'model', 'nam_SX', 'sdt_KH', 'tinh',
                'dai_ly_ban_dau', 'trang_thai']
ENUM_TRANG_THAI_UIO = {'active', 'da_thanh_ly', 'da_doi_chu', 'khong_lien_lac'}

def validate_uio(df: pd.DataFrame, today):
    issues = []
    missing = set(REQUIRED_UIO) - set(df.columns)
    if missing:
        issues.append(('CRITICAL', f'Thiếu cột: {missing}'))
        return issues

    # 1. VIN unique
    n_dup = df.duplicated('vin').sum()
    if n_dup > 0:
        issues.append(('CRITICAL',
            f'{n_dup} VIN trùng — UIO phải unique theo VIN. '
            'Dedupe theo lan_vao_xuong_cuoi muộn nhất, giữ trang_thai mới nhất.'))

    # 2. VIN format (17 ký tự alphanumeric, không có I/O/Q)
    bad_vin = df[~df['vin'].astype(str).str.match(r'^[A-HJ-NPR-Z0-9]{17}$')]
    if len(bad_vin) > 0:
        issues.append(('WARN',
            f'{len(bad_vin)} VIN không đúng format — verify trước khi cross-ref RO'))

    # 3. ngay_ban hợp lý
    df['ngay_ban'] = pd.to_datetime(df['ngay_ban'], errors='coerce')
    bad_date = df[df['ngay_ban'] > pd.Timestamp(today)]
    if len(bad_date) > 0:
        issues.append(('CRITICAL', f'{len(bad_date)} dòng có ngay_ban tương lai'))

    # 4. Tuổi xe vs nam_SX
    df['nam_ban'] = df['ngay_ban'].dt.year
    bad_age = df[df['nam_ban'] - df['nam_SX'] > 2]   # bán xe mới quá 2 năm SX là lạ
    if len(bad_age) > len(df) * 0.05:
        issues.append(('INFO',
            f'{len(bad_age)} dòng tuổi xe lệch >2y vs năm SX (xe trưng bày tồn?)'))

    # 5. trang_thai
    bad_status = set(df['trang_thai'].dropna().unique()) - ENUM_TRANG_THAI_UIO
    if bad_status:
        issues.append(('WARN', f'trang_thai lạ: {bad_status}'))

    # 6. % UIO im ắng (chưa vào xưởng > 12 tháng)
    df['lan_vao_xuong_cuoi'] = pd.to_datetime(df['lan_vao_xuong_cuoi'], errors='coerce')
    silent = df[
        (df['trang_thai'] == 'active') &
        ((pd.Timestamp(today) - df['lan_vao_xuong_cuoi']).dt.days > 365 |
         df['lan_vao_xuong_cuoi'].isna())
    ]
    pct_silent = len(silent) / len(df)
    if pct_silent > 0.30:
        issues.append(('INFO',
            f'{pct_silent:.1%} UIO im ắng > 12 tháng — tiềm năng cho vin-recaller'))

    return issues
```

### 2.4 Mẫu dữ liệu chuẩn

```
vin                | ngay_ban    | model       | nam_SX | mau_xe | sdt_KH      | tinh     | dai_ly_ban_dau   | lan_vao_xuong_cuoi | trang_thai
JTDBT923581234567  | 2023-04-12  | Vios        | 2023   | Trắng  | 0901234567  | Đồng Nai | PGS Đồng Nai     | 2025-12-08         | active
KMHCT41AAEU098765  | 2021-09-05  | Accent      | 2021   | Bạc    | 0908765432  | Đồng Nai | Hyundai LK       | 2024-06-15         | active
JM6KE2DM7E0123456  | 2020-03-22  | CX-5        | 2019   | Đen    | 0912345678  | Đồng Nai | PGS Đồng Nai     |                    | khong_lien_lac
```

---

## 3. File RO header — `ro_<chi_nhanh>_<YYYYMM>.xlsx`

### 3.1 Cột bắt buộc

| STT | Tên cột | Bí danh | Kiểu | Ràng buộc |
|---|---|---|---|---|
| 1 | `ma_RO` | so_RO, ro_no | string | unique |
| 2 | `vin` | so_khung | string(17) | có trong UIO (lý tưởng) |
| 3 | `ngay_mo_RO` | open_date | date | trong kỳ |
| 4 | `ngay_dong_RO` | close_date | date | ≥ ngay_mo_RO |
| 5 | `ma_KTV_chinh` | technician_lead | string | có trong master KTV |
| 6 | `ma_CVDV` | service_advisor | string | có trong master CVDV |
| 7 | `loai_RO` | ro_type | enum | BDĐK/SC/ĐS/BH/Khac |
| 8 | `nguon_RO` | ro_source | enum | hen_truoc/walkin/cuu_ho/recall |
| 9 | `tong_doanh_thu` | total_revenue | number | ≥ 0 |
| 10 | `doanh_thu_CLĐ` | labor_revenue | number | ≥ 0 |
| 11 | `doanh_thu_PT` | parts_revenue | number | ≥ 0 |
| 12 | `doanh_thu_DS` | bodyshop_revenue | number | ≥ 0 (nếu có đồng sơn) |
| 13 | `km_xe_vao` | km_in | number | ≥ 0 |
| 14 | `trang_thai_RO` | status | enum | open/in_progress/closed/cancelled |
| 15 | `FTF_flag` | first_time_fix | bool | true nếu sửa đúng lần đầu |
| 16 | `comeback_flag` | is_comeback | bool | true nếu KH quay lại trong 7d cùng triệu chứng |

### 3.2 Enum chi tiết

```python
LOAI_RO = {
    'BDĐK': 'Bảo dưỡng định kỳ (1k, 5k, 10k, 20k, 30k, 40k, 60k, 80k, 100k km)',
    'SC':   'Sửa chữa chung (động cơ, hộp số, điện, gầm, điều hoà...)',
    'ĐS':   'Đồng sơn (va chạm, sơn lại, tỉa khung...)',
    'BH':   'Bảo hành (chính sách hãng)',
    'Khac': 'Vệ sinh, dán phim, lắp phụ kiện...'
}
NGUON_RO = {
    'hen_truoc':  'KH đặt hẹn online/Zalo/điện thoại trước',
    'walkin':     'KH đến trực tiếp không hẹn',
    'cuu_ho':     'Cứu hộ kéo về',
    'recall':     'Triệu hồi từ hãng'
}
```

### 3.3 Validate code

```python
REQUIRED_RO = ['ma_RO', 'vin', 'ngay_mo_RO', 'ngay_dong_RO',
               'ma_KTV_chinh', 'ma_CVDV', 'loai_RO', 'nguon_RO',
               'tong_doanh_thu', 'doanh_thu_CLĐ', 'doanh_thu_PT',
               'km_xe_vao', 'trang_thai_RO']

def validate_ro(df, uio_df, today):
    issues = []
    missing = set(REQUIRED_RO) - set(df.columns)
    if missing:
        issues.append(('CRITICAL', f'Thiếu cột: {missing}'))
        return issues

    # 1. ma_RO unique
    n_dup = df.duplicated('ma_RO').sum()
    if n_dup > 0:
        issues.append(('CRITICAL', f'{n_dup} ma_RO trùng'))

    # 2. ngay_dong >= ngay_mo
    df['ngay_mo_RO'] = pd.to_datetime(df['ngay_mo_RO'])
    df['ngay_dong_RO'] = pd.to_datetime(df['ngay_dong_RO'], errors='coerce')
    closed = df[df['trang_thai_RO'] == 'closed']
    bad_dates = closed[closed['ngay_dong_RO'] < closed['ngay_mo_RO']]
    if len(bad_dates) > 0:
        issues.append(('CRITICAL', f'{len(bad_dates)} RO closed có ngay_dong < ngay_mo'))

    # 3. doanh_thu = CLĐ + PT + DS
    df['doanh_thu_DS'] = df.get('doanh_thu_DS', 0).fillna(0)
    df['expected_total'] = df['doanh_thu_CLĐ'] + df['doanh_thu_PT'] + df['doanh_thu_DS']
    diff = (df['tong_doanh_thu'] - df['expected_total']).abs()
    bad_total = df[diff > 1000]  # cho phép sai lệch ≤ 1k VND do làm tròn
    if len(bad_total) > 0:
        issues.append(('WARN',
            f'{len(bad_total)} RO có tong_doanh_thu ≠ CLĐ+PT+ĐS — cần verify'))

    # 4. doanh_thu âm
    bad_neg = df[(df['tong_doanh_thu'] < 0) | (df['doanh_thu_CLĐ'] < 0) |
                 (df['doanh_thu_PT'] < 0)]
    if len(bad_neg) > 0:
        issues.append(('CRITICAL', f'{len(bad_neg)} RO có doanh thu âm — không hợp lệ'))

    # 5. VIN trong RO phải có trong UIO (Hook H3 VIN-Integrity)
    vin_ro = set(df['vin'].dropna())
    vin_uio = set(uio_df['vin'].dropna())
    vin_ngoai = vin_ro - vin_uio
    if len(vin_ngoai) > 0:
        pct = len(vin_ngoai) / len(vin_ro)
        severity = 'CRITICAL' if pct > 0.10 else 'WARN'
        issues.append((severity,
            f'{len(vin_ngoai)} VIN trong RO không có trong UIO ({pct:.1%}). '
            'Có thể là xe tỉnh khác vào sửa chữa, xe đã đổi chủ chưa cập nhật, '
            'hoặc UIO bị thiếu. Đánh dấu "ngoài UIO" trong báo cáo.'))

    # 6. Comeback rate cao bất thường
    if 'comeback_flag' in df.columns:
        comeback_rate = df['comeback_flag'].mean()
        if comeback_rate > 0.10:
            issues.append(('WARN',
                f'Comeback rate {comeback_rate:.1%} > 10% — bất thường, '
                'có thể chất lượng sửa chữa kém hoặc cách ghi nhận sai'))

    return issues
```

---

## 4. File RO_chi_tiet — `ro_chi_tiet_<chi_nhanh>_<YYYYMM>.xlsx`

### 4.1 Cột bắt buộc

| Tên | Kiểu | Mô tả |
|---|---|---|
| `ma_RO` | string | link sang ro header |
| `dong_so` | int | thứ tự dòng trong RO |
| `loai` | enum | CLĐ/PT/PHU_KIEN |
| `ma_phu_tung` | string | required khi loai=PT |
| `ten_phu_tung` | string | |
| `so_luong` | number | > 0 |
| `don_gia` | number | ≥ 0 |
| `thanh_tien` | number | = so_luong × don_gia |
| `gio_cong` | number | required khi loai=CLĐ |
| `ma_KTV_thuc_hien` | string | KTV làm dòng việc cụ thể |
| `loai_lao_dong` | enum | bdĐk/sc_co_ban/sc_phuc_tap/đong_son |

### 4.2 Quy tắc tính tiền

```python
def reconcile_ro_chi_tiet(ro_df, ro_chi_tiet_df):
    """
    Cross-check: tổng từ ro_chi_tiet phải bằng header ro_df.
    """
    summary = ro_chi_tiet_df.groupby('ma_RO').agg(
        sum_thanh_tien=('thanh_tien', 'sum'),
        sum_PT=('thanh_tien', lambda x: x[ro_chi_tiet_df.loc[x.index, 'loai']=='PT'].sum()),
        sum_CLĐ=('thanh_tien', lambda x: x[ro_chi_tiet_df.loc[x.index, 'loai']=='CLĐ'].sum()),
    ).reset_index()

    merged = ro_df[['ma_RO', 'tong_doanh_thu', 'doanh_thu_PT', 'doanh_thu_CLĐ']].merge(
        summary, on='ma_RO', how='left'
    )

    # So sánh
    merged['diff_total'] = merged['tong_doanh_thu'] - merged['sum_thanh_tien'].fillna(0)
    bad = merged[merged['diff_total'].abs() > 1000]
    return bad
```

---

## 5. File Hẹn — `hen_<chi_nhanh>_<YYYYMM>.xlsx`

### 5.1 Cột

| Tên | Kiểu | Mô tả |
|---|---|---|
| `ma_hen` | string | unique |
| `vin` | string | có thể null nếu KH mới |
| `sdt_KH` | string | required |
| `ngay_hen` | datetime | giờ hẹn cụ thể |
| `kenh_dat` | enum | web/zalo/dien_thoai/cvdv_chu_dong/walkin_chuyen_thanh_hen |
| `loai_dich_vu_du_kien` | enum | BDĐK/SC/ĐS/Khac |
| `ma_CVDV_phu_trach` | string | |
| `trang_thai_hen` | enum | confirmed/no_show/đa_den/da_huy |
| `ma_RO_phat_sinh` | string | link sang RO khi hẹn → RO |
| `note_hen` | text | |

### 5.2 Validate

```python
def validate_hen(df, today):
    issues = []
    if 'ngay_hen' not in df.columns:
        return [('CRITICAL', 'Thiếu cột ngay_hen')]

    df['ngay_hen'] = pd.to_datetime(df['ngay_hen'])

    # No-show rate
    past = df[df['ngay_hen'] < pd.Timestamp(today)]
    no_show_rate = (past['trang_thai_hen'] == 'no_show').mean()
    if no_show_rate > 0.20:
        issues.append(('WARN',
            f'No-show rate {no_show_rate:.1%} > 20% — nhắc hẹn không hiệu quả'))

    # Đặt hẹn quá sát giờ (< 2h)
    confirmed_recent = df[
        (df['trang_thai_hen'].isin(['confirmed', 'đa_den'])) &
        ((df['ngay_hen'] - df['ngay_dat']).dt.total_seconds() < 7200)
    ] if 'ngay_dat' in df.columns else pd.DataFrame()
    if len(confirmed_recent) > len(df) * 0.30:
        issues.append(('INFO', 'Nhiều hẹn được đặt trong < 2h trước — thực chất là walkin'))

    return issues
```

---

## 6. File CSI — `csi_service_<chi_nhanh>_<kỳ>.xlsx`

### 6.1 Cột

| Tên | Kiểu | Mô tả |
|---|---|---|
| `phieu_id` | string | unique |
| `ma_RO` | string | link |
| `ngay_khao_sat` | date | sau RO closed 3-7 ngày |
| `ma_CVDV` | string | |
| `ma_KTV_chinh` | string | |
| `diem_tong` | number | 1-5 hoặc 0-100 |
| `diem_don_tiep` | number | điểm chạm tiếp đón |
| `diem_tu_van` | number | điểm chạm tư vấn |
| `diem_thoi_gian_cho` | number | điểm chạm thời gian |
| `diem_chat_luong_sua` | number | điểm chạm chất lượng |
| `diem_giao_xe_lai` | number | điểm chạm trả xe |
| `diem_gia_phai_chang` | number | điểm chạm giá |
| `phan_hoi_text` | string | optional, paraphrase khi trích |
| `nps` | int | -100 → +100 |
| `comeback_intent` | enum | chac_chan/co_le/khong_chac/khong_quay_lai |

### 6.2 Quy tắc paraphrase

Như Sales — **tối đa 15 từ liên tiếp nguyên văn**, không nêu danh tính KH,
trích kèm `ma_RO` để truy vết.

---

## 7. Master files

### 7.1 Master KTV — `ktv_master.xlsx`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `ma_KTV` | string | unique |
| `ten` | string | |
| `chi_nhanh` | string | |
| `level` | int | 1-7 (theo skill training) |
| `chuyen_mon` | enum | dong_co/dien/gam/may_lanh/đa_nang |
| `ngay_vao_PGS` | date | tính thâm niên |
| `target_RO_ngay` | int | thường 4-6 RO/ngày tuỳ level |
| `trang_thai` | enum | active/nghi_phep/nghi_om/da_nghi |

### 7.2 Master CVDV — `cvdv_master.xlsx`

| Cột | Mô tả |
|---|---|
| `ma_CVDV` | unique |
| `ten` | |
| `level` | 1-7 (skill training) |
| `chi_nhanh` | |
| `khoang_quan_ly` | số VIN active đang phụ trách |

### 7.3 Master Phụ tùng — `pt_master.xlsx`

| Cột | Mô tả |
|---|---|
| `ma_phu_tung` | unique |
| `ten` | |
| `loai` | tieu_hao/dien/gam/than_vo/khac |
| `gia_niem_yet` | |
| `ton_kho_min` | mức tồn an toàn |
| `lead_time_dat_hang_ngay` | |

---

## 8. Quy trình xử lý sai schema

```
[Nhận file]
   ↓
[Đọc xlsx, detect type theo cột]
   ↓
[Validate file_type tương ứng]
   ↓
issues:
   ├── CRITICAL → DỪNG, hỏi user gửi lại
   ├── WARN     → Báo + xin phép tiếp tục
   └── INFO     → Ghi nhận, tiếp
   ↓
[Cross-check VIN-Integrity giữa UIO ↔ RO (Hook H3)]
   ↓
[Reconcile ro_chi_tiet ↔ ro header]
   ↓
[Truyền df sạch sang sub-agent]
```

---

## 9. Convention đặt tên

```
uio_<chi_nhanh>_<YYYYMM>.xlsx                # snapshot tháng
uio_<chi_nhanh>_<YYYYMMDD>.xlsx              # snapshot ngày
ro_<chi_nhanh>_<YYYYMM>.xlsx                 # 1 tháng
ro_chi_tiet_<chi_nhanh>_<YYYYMM>.xlsx
hen_<chi_nhanh>_<YYYYMM>.xlsx
csi_service_<chi_nhanh>_<YYYYQQ>.xlsx        # quý
ktv_master.xlsx                              # cập nhật khi có thay đổi
cvdv_master.xlsx
pt_master.xlsx
```

---

## 10. Edge cases & lưu ý đặc biệt Service

| Tình huống | Cách xử lý |
|---|---|
| 1 RO có 2-3 KTV (RO phức tạp) | Header lấy KTV chính, ro_chi_tiet ghi từng dòng việc |
| RO chưa close hết kỳ | Tách báo cáo: "RO đã close" + "RO open carryover" |
| KH đến nhưng từ chối sửa | Vẫn mở RO + tổng_doanh_thu=0, loai=Khac, note "tu_choi_sua" |
| Bảo hành (BH) doanh thu = 0 | OK, đó là quy định, không tính vào doanh thu xưởng |
| Đồng sơn tách kho riêng | File `ro_dong_son_*.xlsx` riêng, gộp vào báo cáo tổng có cờ `co_DS=true` |
| VIN xe đối thủ vào sửa | Ghi `dai_ly_ban_dau != PGS`, vẫn tính doanh thu xưởng nhưng không tính vào "share UIO" |
| Recall hãng | Doanh thu = 0, KTV được tính giờ công riêng, không lẫn vào BDĐK |
