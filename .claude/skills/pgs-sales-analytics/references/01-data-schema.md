# Reference 01 — Data Schema cho file Cyber/WebCar/Quản trị

> **Khi nào load:** User upload file Excel chưa xác định cột; hoặc khi `market-analyzer`/`funnel-diagnoser`
> báo `missing_column`. Không load nếu user đã hỏi câu thị phần thuần (chỉ cần `02-market-share-formulas.md`).

---

## 1. File DLTT (Đăng ký lưu thông) — `dltt_<tháng>.xlsx`

**Nguồn:** Cyber DMS / WebCar export theo tháng.
**Phạm vi:** Toàn bộ xe đăng ký mới trong địa bàn tham chiếu (mọi TH, không chỉ PGS).
**Đơn vị bản ghi:** 1 xe = 1 dòng (theo số khung).

### 1.1 Cột bắt buộc

| STT | Tên cột (chuẩn) | Bí danh thường gặp | Kiểu | Ràng buộc |
|---|---|---|---|---|
| 1 | `vin` | so_khung, frame_no, chassis | string(17) | unique trong kỳ |
| 2 | `ngay_dang_ky` | reg_date, ngay_DK, NgàyĐK | date | trong kỳ phân tích |
| 3 | `TH` | thuong_hieu, brand, hãng | string | enum: Toyota/Hyundai/Mazda/Kia/... |
| 4 | `model` | mau_xe, ten_xe | string | có trong master model |
| 5 | `phan_khuc` | segment, phân_khúc | string | enum: A/B/C/D/B-SUV/C-SUV/D-SUV/MPV/Pickup/Van |
| 6 | `tinh` | province, tỉnh | string | có trong danh mục 63 tỉnh |
| 7 | `huyen` | district, huyện/quận | string | optional nhưng nên có |
| 8 | `loai_KH` | customer_type | string | enum: B2C/Fleet/Taxi/Corporate |
| 9 | `noi_ban` | dealer, đại_lý_bán | string | tên đại lý (PGS hoặc đối thủ) |

### 1.2 Cột tham khảo (nice-to-have)

| Tên | Dùng để |
|---|---|
| `nam_SX` | Phân biệt xe mới/xe trưng bày tồn |
| `mau_xe` | Phân tích preference KH theo vùng |
| `gia_niem_yet` | Tính giá trị thị trường |
| `nguon_du_lieu` | Phân biệt nguồn DLTT chính thức vs ước tính |

### 1.3 Validate code

```python
import pandas as pd

REQUIRED_DLTT = ['vin', 'ngay_dang_ky', 'TH', 'model', 'phan_khuc',
                 'tinh', 'loai_KH', 'noi_ban']
ENUM_LOAI_KH = {'B2C', 'Fleet', 'Taxi', 'Corporate'}
ENUM_PHAN_KHUC = {'A', 'B', 'C', 'D', 'B-SUV', 'C-SUV', 'D-SUV',
                  'MPV', 'Pickup', 'Van'}

def validate_dltt(df: pd.DataFrame, ky_start: str, ky_end: str):
    issues = []

    # 1. Cột bắt buộc
    missing = set(REQUIRED_DLTT) - set(df.columns)
    if missing:
        issues.append(('CRITICAL', f'Thiếu cột: {missing}'))
        return issues  # dừng ngay

    # 2. VIN duplicate
    n_dup = df.duplicated('vin').sum()
    if n_dup > 0:
        issues.append(('WARN', f'{n_dup} VIN trùng — đề nghị dedupe theo ngay_dang_ky muộn nhất'))

    # 3. Ngày trong kỳ
    df['ngay_dang_ky'] = pd.to_datetime(df['ngay_dang_ky'], errors='coerce')
    n_outrange = (~df['ngay_dang_ky'].between(ky_start, ky_end)).sum()
    if n_outrange > 0:
        issues.append(('WARN', f'{n_outrange} dòng ngoài kỳ phân tích'))

    # 4. Enum
    bad_kh = set(df['loai_KH'].dropna().unique()) - ENUM_LOAI_KH
    if bad_kh:
        issues.append(('WARN', f'loai_KH lạ: {bad_kh}'))

    bad_pk = set(df['phan_khuc'].dropna().unique()) - ENUM_PHAN_KHUC
    if bad_pk:
        issues.append(('WARN', f'phan_khuc lạ: {bad_pk}'))

    # 5. Dòng tổng lẫn vào
    suspicious = df[df['vin'].astype(str).str.contains('Tổng|Total|Sum', case=False, na=False)]
    if len(suspicious) > 0:
        issues.append(('WARN', f'{len(suspicious)} dòng nghi là dòng tổng, cần lọc'))

    # 6. Tách B2C khỏi Fleet/Taxi
    pct_non_b2c = (df['loai_KH'] != 'B2C').mean()
    if pct_non_b2c > 0.20:
        issues.append(('INFO', f'{pct_non_b2c:.1%} là Fleet/Taxi — nên tách báo cáo riêng'))

    return issues
```

### 1.4 Mẫu dữ liệu chuẩn

```
vin                | ngay_dang_ky | TH      | model         | phan_khuc | tinh        | huyen        | loai_KH | noi_ban
JTDBT923581234567  | 2026-04-03   | Toyota  | Vios          | B         | Đồng Nai    | Biên Hòa     | B2C     | PGS Đồng Nai
KMHCT41AAEU098765  | 2026-04-05   | Hyundai | Accent        | B         | Đồng Nai    | Long Khánh   | B2C     | Hyundai LK
JM6KE2DM7E0123456  | 2026-04-12   | Mazda   | CX-5          | C-SUV     | Đồng Nai    | Biên Hòa     | B2C     | Mazda Biên Hòa
```

---

## 2. File Sales PGS — `sales_pgs_<tháng>.xlsx`

**Nguồn:** Cyber DMS PGS export.
**Phạm vi:** Doanh số PGS bán ra trong kỳ.
**Đơn vị bản ghi:** 1 HĐ = 1 dòng.

### 2.1 Cột bắt buộc

| STT | Tên cột | Bí danh | Kiểu | Ràng buộc |
|---|---|---|---|---|
| 1 | `ma_HD` | so_HD, contract_no | string | unique |
| 2 | `vin` | so_khung | string(17) | có trong DLTT cùng kỳ (idealy) |
| 3 | `ngay_HD` | contract_date, ngay_ky | date | trong kỳ |
| 4 | `ngay_giao` | delivery_date | date | ≥ ngay_HD |
| 5 | `ma_TVBH` | sales_id, ma_NV_KD | string | có trong master TVBH |
| 6 | `chi_nhanh` | branch | string | enum CN PGS |
| 7 | `model` | xe, ten_xe | string | |
| 8 | `phan_khuc` | segment | string | |
| 9 | `gia_ban` | doanh_thu, contract_value | number | > 0 |
| 10 | `loai_KH` | | string | B2C/Fleet/Taxi/Corporate |
| 11 | `nguon_KHTN` | source, kênh | string | enum: walkin/online/sukien/refer/data_cu/khac |

### 2.2 Validate code

```python
REQUIRED_SALES = ['ma_HD', 'vin', 'ngay_HD', 'ngay_giao', 'ma_TVBH',
                  'chi_nhanh', 'model', 'phan_khuc', 'gia_ban',
                  'loai_KH', 'nguon_KHTN']

def validate_sales_pgs(df: pd.DataFrame, dltt_df: pd.DataFrame, ky_start, ky_end):
    issues = []
    missing = set(REQUIRED_SALES) - set(df.columns)
    if missing:
        issues.append(('CRITICAL', f'Thiếu cột: {missing}'))
        return issues

    # ma_HD duplicate
    n_dup = df.duplicated('ma_HD').sum()
    if n_dup > 0:
        issues.append(('WARN', f'{n_dup} ma_HD trùng'))

    # ngay_giao >= ngay_HD
    df['ngay_HD'] = pd.to_datetime(df['ngay_HD'])
    df['ngay_giao'] = pd.to_datetime(df['ngay_giao'])
    bad_dates = df[df['ngay_giao'] < df['ngay_HD']]
    if len(bad_dates) > 0:
        issues.append(('CRITICAL', f'{len(bad_dates)} HĐ có ngày giao < ngày ký'))

    # gia_ban > 0
    bad_price = df[df['gia_ban'] <= 0]
    if len(bad_price) > 0:
        issues.append(('CRITICAL', f'{len(bad_price)} HĐ giá ≤ 0'))

    # Cross-check VIN với DLTT
    vin_sales = set(df['vin'].dropna())
    vin_dltt = set(dltt_df['vin'].dropna())
    vin_sales_no_dltt = vin_sales - vin_dltt
    if len(vin_sales_no_dltt) / max(len(vin_sales), 1) > 0.05:
        issues.append(('WARN',
            f'{len(vin_sales_no_dltt)}/{len(vin_sales)} HĐ có VIN không có trong DLTT '
            '— có thể chưa đăng ký xong, hoặc DLTT thiếu'))

    return issues
```

---

## 3. File Quản trị — `quan_tri_<chi_nhanh>.xlsx`

**Nguồn:** File Excel nội bộ Phòng KD, cập nhật real-time.
**Phạm vi:** Toàn bộ KHTN active trong pipeline + đã chốt + đã mất.
**Đơn vị bản ghi:** 1 KHTN = 1 dòng (cập nhật trạng thái mới nhất).

### 3.1 Cột bắt buộc

| STT | Tên cột | Bí danh | Kiểu | Ràng buộc |
|---|---|---|---|---|
| 1 | `ma_KHTN` | lead_id | string | unique |
| 2 | `ten_KHTN` | ten_KH, customer_name | string | |
| 3 | `sdt` | phone | string | format Vietnam |
| 4 | `ma_TVBH` | sales_id | string | có trong master |
| 5 | `nguon_KHTN` | source | string | enum |
| 6 | `ngay_tiep_can` | first_contact_date | date | ≤ today |
| 7 | `trang_thai` | status | string | enum: Cold/Warm/Hot/HĐ/Mất |
| 8 | `model_quan_tam` | model_interest | string | có trong danh mục |
| 9 | `gia_tri_du_kien` | expected_value | number | > 0 |
| 10 | `ngay_lai_thu` | test_drive_date | date | optional, ≥ ngay_tiep_can |
| 11 | `ngay_bao_gia` | quote_date | date | optional |
| 12 | `ngay_dat_coc` | deposit_date | date | optional |
| 13 | `ngay_chot` | close_date | date | có khi trang_thai='HĐ' |
| 14 | `ngay_mat` | lost_date | date | có khi trang_thai='Mất' |
| 15 | `ly_do_mat` | lost_reason | string | optional khi Mất |

### 3.2 Định nghĩa trạng thái phễu

| Trạng thái | Khi nào set | Bằng chứng cần |
|---|---|---|
| **Cold** | TVBH vừa tiếp cận, KH chưa thể hiện nhu cầu rõ | có sdt + ngày tiếp cận |
| **Warm** | KH đã được báo giá hoặc lái thử | ngay_bao_gia hoặc ngay_lai_thu |
| **Hot** | KH đặt cọc / cam kết mua | ngay_dat_coc + số tiền cọc |
| **HĐ** | Đã ký hợp đồng | ngay_chot + ma_HD link sang sales_pgs |
| **Mất** | KH chuyển sang đối thủ hoặc huỷ ý định | ngay_mat + ly_do_mat |

### 3.3 Validate code

```python
REQUIRED_QT = ['ma_KHTN', 'ten_KHTN', 'sdt', 'ma_TVBH', 'nguon_KHTN',
               'ngay_tiep_can', 'trang_thai', 'model_quan_tam',
               'gia_tri_du_kien']
ENUM_STATUS = {'Cold', 'Warm', 'Hot', 'HĐ', 'Mất'}
ENUM_NGUON = {'walkin', 'online', 'sukien', 'refer', 'data_cu', 'khac'}

def validate_quan_tri(df: pd.DataFrame, today):
    issues = []
    missing = set(REQUIRED_QT) - set(df.columns)
    if missing:
        issues.append(('CRITICAL', f'Thiếu cột: {missing}'))
        return issues

    # Logic ràng buộc trạng thái ↔ ngày
    df = df.copy()
    for col in ['ngay_tiep_can', 'ngay_lai_thu', 'ngay_bao_gia',
                'ngay_dat_coc', 'ngay_chot', 'ngay_mat']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Warm phải có ngay_bao_gia hoặc ngay_lai_thu
    warm_no_evidence = df[
        (df['trang_thai'] == 'Warm') &
        df['ngay_bao_gia'].isna() &
        df['ngay_lai_thu'].isna()
    ]
    if len(warm_no_evidence) > 0:
        issues.append(('WARN',
            f'{len(warm_no_evidence)} KHTN Warm không có ngày báo giá/lái thử'))

    # Hot phải có ngay_dat_coc
    hot_no_deposit = df[(df['trang_thai'] == 'Hot') & df['ngay_dat_coc'].isna()]
    if len(hot_no_deposit) > 0:
        issues.append(('WARN',
            f'{len(hot_no_deposit)} KHTN Hot không có ngày đặt cọc'))

    # HĐ phải có ngay_chot
    hd_no_close = df[(df['trang_thai'] == 'HĐ') & df['ngay_chot'].isna()]
    if len(hd_no_close) > 0:
        issues.append(('CRITICAL',
            f'{len(hd_no_close)} KHTN HĐ không có ngày chốt — không tính vào doanh số'))

    # Mất phải có ngay_mat + ly_do_mat
    lost_no_reason = df[
        (df['trang_thai'] == 'Mất') &
        (df['ly_do_mat'].isna() | (df['ly_do_mat'] == ''))
    ]
    if len(lost_no_reason) > 0:
        issues.append(('INFO',
            f'{len(lost_no_reason)} KHTN Mất không ghi lý do — mất dữ liệu cải tiến'))

    # Pipeline đứng > 90 ngày ở Cold/Warm — nên close hoặc nuôi tiếp
    stale = df[
        df['trang_thai'].isin(['Cold', 'Warm']) &
        ((today - df['ngay_tiep_can']).dt.days > 90)
    ]
    if len(stale) > 0:
        issues.append(('INFO',
            f'{len(stale)} KHTN đứng > 90 ngày ở Cold/Warm — đề nghị TVBH cập nhật'))

    return issues
```

### 3.4 Edge cases thường gặp

| Tình huống | Cách xử lý |
|---|---|
| 1 KH có 2 ma_KHTN (do 2 TVBH cùng tiếp) | Dedupe theo sdt, giữ TVBH tiếp xúc đầu |
| KH chuyển model trong quá trình tư vấn | Cập nhật `model_quan_tam` mới, **giữ nguyên** ngày tiếp cận đầu |
| KH "ngủ" 6 tháng quay lại | Tạo ma_KHTN mới — không mở lại lead cũ |
| HĐ trong sales_pgs nhưng không có ma_KHTN trong quan_tri | "Bán luồn" — flag cho `funnel-diagnoser` |

---

## 4. File CSI Sales — `csi_sales_<kỳ>.xlsx`

### 4.1 Cột bắt buộc

| Tên | Kiểu | Mô tả |
|---|---|---|
| `phieu_id` | string | unique |
| `ma_HD` | string | link sang sales_pgs |
| `ngay_khao_sat` | date | sau giao xe ≥ 7 ngày |
| `ma_TVBH` | string | TVBH phụ trách HĐ |
| `diem_tong` | number | thang 1-5 hoặc 0-100 (chọn 1) |
| `diem_tu_van` | number | điểm chạm tư vấn |
| `diem_thu_tuc` | number | điểm chạm thủ tục/tài chính |
| `diem_giao_xe` | number | điểm chạm giao xe |
| `diem_hau_giao_xe` | number | điểm chạm chăm sóc sau giao |
| `phan_hoi_text` | string | optional, text phản hồi |
| `nps` | int | optional, -100 → +100 |

### 4.2 Quy tắc paraphrase phản hồi text

Khi trích phản hồi KH vào báo cáo:
- **Tối đa 15 từ liên tiếp nguyên văn**.
- **Không nêu danh tính KH** (kể cả khi file có `ten_KH`).
- Tốt hơn: paraphrase + gắn `ma_HD` để truy vết.

---

## 5. Master files (đính kèm để cross-check)

### 5.1 Master TVBH — `tvbh_master.xlsx`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `ma_TVBH` | string | unique |
| `ten` | string | |
| `chi_nhanh` | string | |
| `ngay_vao_PGS` | date | tính thâm niên |
| `level` | int | 1-7 (theo skill training) |
| `TH_phu_trach` | string | nếu chuyên 1 TH |
| `target_thang` | int | số HĐ/tháng |
| `trang_thai` | string | active/nghỉ_phép/đã_nghỉ |

### 5.2 Master Model — `model_master.xlsx`

| Cột | Mô tả |
|---|---|
| `model` | unique |
| `TH` | |
| `phan_khuc` | |
| `gia_niem_yet` | |
| `nam_ra_mat` | |
| `version_hien_tai` | facelift/all_new/special |

---

## 6. Quy trình xử lý khi file sai schema

```
[Nhận file từ user]
    ↓
[Đọc qua xlsx skill → df]
    ↓
[Detect file type theo cột có mặt]
    ↓
[Áp validate_<type> tương ứng]
    ↓
issues = []
    ├── CRITICAL → DỪNG, hỏi user gửi lại file đúng template
    ├── WARN     → Báo cáo + hỏi user xác nhận tiếp tục
    └── INFO     → Ghi nhận, tiếp tục
    ↓
[Truyền df sạch sang sub-agent tiếp]
```

**Không bao giờ tự đoán giá trị thiếu** — đây là vi phạm nguyên tắc "không bịa số" của Layer 1.

---

## 7. Convention đặt tên file

```
dltt_<YYYYMM>.xlsx                       # vd: dltt_202604.xlsx
dltt_<vung>_<YYYYMM>.xlsx                # vd: dltt_DongNai_202604.xlsx
sales_pgs_<YYYYMM>.xlsx
sales_pgs_<chi_nhanh>_<YYYYMM>.xlsx
quan_tri_<chi_nhanh>.xlsx                # real-time, không có timestamp
quan_tri_<chi_nhanh>_<YYYYMMDD>.xlsx     # snapshot ngày X
csi_sales_<YYYYQQ>.xlsx                  # vd: csi_sales_2026Q2.xlsx
```

User upload sai tên → main rename khi copy về `/mnt/` working trước khi truyền sub-agent.
