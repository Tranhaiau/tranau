# Reference 07 — Template File Quản trị KH hàng ngày

> **Khi nào load:** Sub-agent `plan-builder` cần xuất file `.xlsx` template để TVBH/Trưởng phòng
> dùng quản lý pipeline hằng ngày. Hoặc khi user yêu cầu "Làm file quản trị KH tuần này".

---

## 1. Triết lý thiết kế

File quản trị tốt phải:
1. **Đơn giản đủ để TVBH dùng hằng ngày** — không quá 20 cột/sheet chính.
2. **Có công thức tự tính** — TVBH chỉ cập nhật trạng thái, KPI tự cập nhật.
3. **Có data validation** — không cho nhập trạng thái sai.
4. **Có sheet riêng cho từng vai trò** — TVBH thấy 1 view, Trưởng phòng thấy view khác.
5. **Export được sang Cyber DMS** — không tạo silo.

---

## 2. Cấu trúc file (5 sheet)

```
file_quan_tri_<chi_nhanh>_<tháng>.xlsx
├── Sheet 1: Pipeline KHTN (chính)
├── Sheet 2: Daily Tracking (TVBH update mỗi ngày)
├── Sheet 3: Action Plan (GP từ báo cáo gần nhất)
├── Sheet 4: Dashboard (KPI auto từ sheets 1-3)
└── Sheet 5: Master (TVBH/Model/Dropdown values)
```

---

## 3. Sheet 1 — Pipeline KHTN

### 3.1 Cột

| STT | Cột | Kiểu | Validation | Người nhập |
|---|---|---|---|---|
| 1 | `ma_KHTN` | Text | Auto-gen pattern: `<CN>-<YYYYMM>-<seq>` | Auto |
| 2 | `ten_KHTN` | Text | Required | TVBH |
| 3 | `sdt` | Text | Format VN: 0xx.xxx.xxxx | TVBH |
| 4 | `email` | Text | Optional | TVBH |
| 5 | `dia_chi` | Text | Optional | TVBH |
| 6 | `ma_TVBH` | Dropdown | List từ Sheet 5 | TVBH chọn |
| 7 | `nguon_KHTN` | Dropdown | walkin/online/sukien/refer/data_cu/khac | TVBH |
| 8 | `loai_KH` | Dropdown | B2C/Fleet/Taxi/Corporate | TVBH |
| 9 | `ngay_tiep_can` | Date | ≤ today | TVBH |
| 10 | `model_quan_tam` | Dropdown | List từ Sheet 5 | TVBH |
| 11 | `gia_tri_du_kien` | Number | > 0 | TVBH |
| 12 | `trang_thai` | Dropdown | Cold/Warm/Hot/HĐ/Mất | TVBH |
| 13 | `ngay_lai_thu` | Date | ≥ ngay_tiep_can | TVBH |
| 14 | `ngay_bao_gia` | Date | ≥ ngay_tiep_can | TVBH |
| 15 | `ngay_dat_coc` | Date | ≥ ngay_bao_gia (ideally) | TVBH |
| 16 | `so_tien_coc` | Number | > 0 khi Hot | TVBH |
| 17 | `ngay_chot` | Date | Required khi HĐ | TVBH |
| 18 | `ma_HD` | Text | Required khi HĐ — link sang Cyber | TVBH |
| 19 | `ngay_giao_du_kien` | Date | ≥ ngay_chot | TVBH |
| 20 | `ngay_mat` | Date | Required khi Mất | TVBH |
| 21 | `ly_do_mat` | Dropdown | List 8 lý do chuẩn | TVBH |
| 22 | `note` | Text | Optional | TVBH |
| 23 | `lan_cap_nhat_cuoi` | DateTime | Auto khi sửa hàng | Auto |
| 24 | `so_ngay_pipeline` | Number | Auto = today - ngay_tiep_can | Auto formula |
| 25 | `tinh_trang_pipeline` | Text | Auto: "Active <30d" / "Stale 30-90d" / "Critical >90d" | Auto formula |

### 3.2 Data validation rules (cài bằng XLSX skill)

```python
import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation

def setup_pipeline_validation(ws):
    """Cài data validation cho Sheet 1."""

    # Cột G (nguon_KHTN)
    dv_nguon = DataValidation(
        type="list",
        formula1='"walkin,online,sukien,refer,data_cu,khac"',
        allow_blank=False,
        showErrorMessage=True,
        errorTitle='Nguồn KHTN không hợp lệ',
        error='Chọn 1 trong: walkin, online, sukien, refer, data_cu, khac'
    )
    ws.add_data_validation(dv_nguon)
    dv_nguon.add('G2:G1000')

    # Cột L (trang_thai)
    dv_status = DataValidation(
        type="list",
        formula1='"Cold,Warm,Hot,HĐ,Mất"',
        allow_blank=False
    )
    ws.add_data_validation(dv_status)
    dv_status.add('L2:L1000')

    # Cột H (loai_KH)
    dv_kh = DataValidation(
        type="list",
        formula1='"B2C,Fleet,Taxi,Corporate"',
        allow_blank=False
    )
    ws.add_data_validation(dv_kh)
    dv_kh.add('H2:H1000')

    # Cột I (ngay_tiep_can) — không được lớn hơn today
    dv_date = DataValidation(
        type="date",
        operator="lessThanOrEqual",
        formula1="TODAY()"
    )
    ws.add_data_validation(dv_date)
    dv_date.add('I2:I1000')
```

### 3.3 Công thức auto-fill cho cột tính

```python
def setup_pipeline_formulas(ws):
    """Cài formula cho cột 23-25."""
    for row in range(2, 1001):
        # Cột W (lan_cap_nhat_cuoi) — không tự cập nhật được trong Excel pure,
        # nên để user chạy macro hoặc cập nhật thủ công khi save
        # Cột X (so_ngay_pipeline)
        ws[f'X{row}'] = f'=IF(I{row}="","",TODAY()-I{row})'

        # Cột Y (tinh_trang_pipeline)
        ws[f'Y{row}'] = (
            f'=IF(L{row}="HĐ","Đã chốt",'
            f'IF(L{row}="Mất","Đã mất",'
            f'IF(X{row}<=30,"Active",'
            f'IF(X{row}<=90,"Stale",'
            f'"Critical"))))'
        )
```

### 3.4 Conditional formatting

```python
from openpyxl.styles import PatternFill
from openpyxl.formatting.rule import CellIsRule

def setup_conditional_formatting(ws):
    """Tô màu dòng theo trạng thái."""
    red = PatternFill(bgColor='FFC7CE', fill_type='solid')
    orange = PatternFill(bgColor='FFEB9C', fill_type='solid')
    green = PatternFill(bgColor='C6EFCE', fill_type='solid')

    # Cột Y: Critical đỏ, Stale cam, Active xanh
    ws.conditional_formatting.add(
        'Y2:Y1000',
        CellIsRule(operator='equal', formula=['"Critical"'], fill=red)
    )
    ws.conditional_formatting.add(
        'Y2:Y1000',
        CellIsRule(operator='equal', formula=['"Stale"'], fill=orange)
    )
    ws.conditional_formatting.add(
        'Y2:Y1000',
        CellIsRule(operator='equal', formula=['"Active"'], fill=green)
    )
```

---

## 4. Sheet 2 — Daily Tracking

### 4.1 Mục đích

TVBH log hoạt động hằng ngày để Trưởng phòng theo dõi: bao nhiêu cuộc gọi, bao nhiêu lái thử,
bao nhiêu báo giá, bao nhiêu cọc, bao nhiêu HĐ.

### 4.2 Cột

| Cột | Kiểu | Mô tả |
|---|---|---|
| `ngay` | Date | Bắt buộc, mặc định today |
| `ma_TVBH` | Dropdown | Từ Master |
| `n_KHTN_moi_tiep_can` | Number | KHTN mới gặp lần đầu |
| `n_cuoc_goi_di` | Number | Outbound calls |
| `n_cuoc_goi_den` | Number | Inbound calls |
| `n_lai_thu` | Number | Số xe lái thử thực hiện |
| `n_bao_gia` | Number | Số báo giá phát hành |
| `n_dat_coc` | Number | Số khách đặt cọc |
| `n_HD_ky` | Number | Số HĐ ký mới |
| `n_giao_xe` | Number | Số xe giao thực tế |
| `pipeline_cuoi_ngay` | Number | Tổng KHTN active cuối ngày |
| `note_ngay` | Text | Ghi chú đặc biệt |

### 4.3 Bảng pivot tự động (cho Trưởng phòng)

Sheet 2 có thêm 1 bảng pivot ở phía dưới:
```
        | n_KHTN_moi | n_lai_thu | n_HD | Pipeline cuối tuần
NV001   |    35      |    8      |  2   |  18
NV004   |    42      |   15      |  6   |  25
NV017   |    58      |   22      |  9   |  32
TỔNG    |   135      |   45      | 17   |  75
```

---

## 5. Sheet 3 — Action Plan

### 5.1 Cột (1 dòng = 1 GP)

```
| ma_GP | van_de | giai_phap | chu_the | kpi | han | ngay_review |
| nhom  | trang_thai | % hoan_thanh | last_update | note            |
```

### 5.2 Trạng thái GP

```
- "Pending" — chưa bắt đầu
- "In Progress" — đang triển khai
- "Done" — đã hoàn thành đúng hạn
- "Overdue" — quá hạn chưa xong
- "Cancelled" — huỷ (có lý do)
```

### 5.3 Conditional formatting

Quá hạn (han < today + status != Done) → tô đỏ.
Sắp đến hạn (han - today ≤ 3 ngày + status != Done) → tô cam.

---

## 6. Sheet 4 — Dashboard

### 6.1 Layout

```
┌─────────────────────────────────────────────────┐
│ KPI HÀNG ĐẦU                                    │
│ Doanh số tháng này: 28 HĐ (mục tiêu 35) — 80%  │
│ Pipeline active: 142  |  Hot: 41                │
│ Dự báo HĐ 14 ngày: 34                           │
│                                                 │
├─────────────────────────────────────────────────┤
│ PHỄU                                            │
│ Cold → Warm: 61% (TB benchmark 65%)             │
│ Warm → Hot:  47% (TB 45%)                       │
│ Hot → HĐ:    68% (TB 65%)                       │
│ Cold → HĐ:   20% (TB 18%)                       │
│                                                 │
├─────────────────────────────────────────────────┤
│ TOP 3 / BOTTOM 3 TVBH                           │
│ Top 1: NV017 — 9 HĐ                             │
│ Top 2: NV004 — 6 HĐ                             │
│ Top 3: NV012 — 4 HĐ                             │
│ Bot 3: NV031 — 1 HĐ (mẫu nhỏ)                  │
│ Bot 2: NV001 — 2 HĐ (CR Cold→Warm yếu)         │
│ Bot 1: NV022 — 1 HĐ (mẫu nhỏ)                  │
│                                                 │
├─────────────────────────────────────────────────┤
│ HÀNH ĐỘNG TUẦN NÀY                              │
│ ✓ NV001: tham gia training "khai thác nhu cầu" │
│ ⏳ Sự kiện B-SUV Aeon Long Thành 11/05         │
│ ⏳ Audit pipeline T6 — review HĐ luồn          │
└─────────────────────────────────────────────────┘
```

### 6.2 Công thức Excel

Mỗi cell trên dashboard pull từ Sheet 1-3 bằng công thức `=COUNTIFS(...)`, `=SUMIFS(...)`,
`=AVERAGEIFS(...)` với điều kiện kỳ phân tích.

---

## 7. Sheet 5 — Master

### 7.1 Sub-table: TVBH

| ma_TVBH | ten | level | trang_thai | ngay_vao | TH_phu_trach |
|---|---|---|---|---|---|
| NV001 | Nguyễn Văn A | 2 | active | 2024-03-01 | Toyota |
| NV004 | Trần Văn B | 4 | active | 2022-07-15 | Toyota |

### 7.2 Sub-table: Model

| model | TH | phan_khuc | gia_niem_yet |
|---|---|---|---|
| Vios | Toyota | B | 458_000_000 |
| Yaris Cross | Toyota | B-SUV | 650_000_000 |

### 7.3 Sub-table: Dropdown values

```
nguon_KHTN: walkin, online, sukien, refer, data_cu, khac
trang_thai: Cold, Warm, Hot, HĐ, Mất
loai_KH: B2C, Fleet, Taxi, Corporate
ly_do_mat: gia_cao, thieu_mau_xe, cho_doi_qua_lau, doi_thu_KM_tot,
           KH_doi_y, tu_van_chua_du, tai_chinh_khong_duoc, gioi_thieu_xe_khac, khac
```

---

## 8. Code tổng — sinh file template hoàn chỉnh

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def generate_quan_tri_template(chi_nhanh, thang, output_path,
                                tvbh_list, model_list):
    """
    Sinh file file_quan_tri_<chi_nhanh>_<thang>.xlsx hoàn chỉnh.
    """
    wb = openpyxl.Workbook()

    # Sheet 1: Pipeline
    ws1 = wb.active
    ws1.title = "Pipeline"
    headers_1 = [
        'ma_KHTN', 'ten_KHTN', 'sdt', 'email', 'dia_chi',
        'ma_TVBH', 'nguon_KHTN', 'loai_KH', 'ngay_tiep_can',
        'model_quan_tam', 'gia_tri_du_kien', 'trang_thai',
        'ngay_lai_thu', 'ngay_bao_gia', 'ngay_dat_coc', 'so_tien_coc',
        'ngay_chot', 'ma_HD', 'ngay_giao_du_kien',
        'ngay_mat', 'ly_do_mat', 'note',
        'lan_cap_nhat_cuoi', 'so_ngay_pipeline', 'tinh_trang_pipeline'
    ]
    ws1.append(headers_1)
    style_header(ws1, len(headers_1))
    setup_pipeline_validation(ws1)
    setup_pipeline_formulas(ws1)
    setup_conditional_formatting(ws1)

    # Sheet 2: Daily Tracking
    ws2 = wb.create_sheet("Daily")
    headers_2 = [
        'ngay', 'ma_TVBH', 'n_KHTN_moi_tiep_can',
        'n_cuoc_goi_di', 'n_cuoc_goi_den',
        'n_lai_thu', 'n_bao_gia', 'n_dat_coc',
        'n_HD_ky', 'n_giao_xe',
        'pipeline_cuoi_ngay', 'note_ngay'
    ]
    ws2.append(headers_2)
    style_header(ws2, len(headers_2))

    # Sheet 3: Action Plan
    ws3 = wb.create_sheet("Action Plan")
    headers_3 = [
        'ma_GP', 'van_de', 'giai_phap', 'chu_the', 'kpi',
        'han', 'ngay_review', 'nhom', 'trang_thai',
        'pct_hoan_thanh', 'last_update', 'note'
    ]
    ws3.append(headers_3)
    style_header(ws3, len(headers_3))

    # Sheet 4: Dashboard (text-based, công thức tự tính)
    ws4 = wb.create_sheet("Dashboard")
    setup_dashboard(ws4)

    # Sheet 5: Master
    ws5 = wb.create_sheet("Master")
    setup_master_data(ws5, tvbh_list, model_list)

    # Hide Sheet 5 cho user thường (nhưng giữ cho dropdown reference)
    ws5.sheet_state = 'hidden'

    wb.save(output_path)
    return output_path

def style_header(ws, n_cols):
    """Định dạng header hàng 1: bold, nền xanh, viền."""
    blue_fill = PatternFill(bgColor='4472C4', fill_type='solid')
    white_font = Font(bold=True, color='FFFFFF')
    border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    for col in range(1, n_cols + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = blue_fill
        cell.font = white_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = 'A2'  # Freeze header

def setup_master_data(ws, tvbh_list, model_list):
    """Ghi danh sách TVBH + Model + dropdown values vào Sheet 5."""
    # TVBH
    ws['A1'] = 'TVBH'
    ws['A1'].font = Font(bold=True)
    ws.append(['ma_TVBH', 'ten', 'level', 'trang_thai', 'ngay_vao', 'TH_phu_trach'])
    for tvbh in tvbh_list:
        ws.append([tvbh['ma'], tvbh['ten'], tvbh['level'],
                   tvbh['trang_thai'], tvbh['ngay_vao'], tvbh['TH']])

    # Tương tự cho model_list
    # ...

def setup_dashboard(ws):
    """Cài layout + công thức cho Sheet 4."""
    ws['A1'] = 'KPI HÀNG ĐẦU'
    ws['A1'].font = Font(bold=True, size=14)

    ws['A3'] = 'Doanh số tháng này (HĐ):'
    ws['B3'] = '=COUNTIFS(Pipeline.L:L,"HĐ",Pipeline.Q:Q,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1))'

    ws['A4'] = 'Pipeline active:'
    ws['B4'] = '=COUNTIFS(Pipeline.L:L,"<>HĐ",Pipeline.L:L,"<>Mất")'

    ws['A5'] = 'Hot count:'
    ws['B5'] = '=COUNTIF(Pipeline.L:L,"Hot")'

    # ... thêm các KPI khác
```

---

## 9. Quy tắc bất biến

1. **Mỗi tháng tạo file mới** — không append vào file cũ vô hạn (file > 5MB chậm Excel).
2. **Đầu tháng copy KHTN active từ tháng trước sang** — không làm lại từ đầu.
3. **Sheet 5 ẩn** — user thường không sửa được dropdown values.
4. **Cài data validation hết các cột bắt buộc** — chống nhập sai schema.
5. **Auto formula chỉ ở cột tính, không ghi đè cột nhập** — TVBH không sửa được.
6. **File mở phải sẵn sàng dùng** — không yêu cầu user "enable macro" hay setup gì thêm.

---

## 10. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| File > 1000 dòng | Pipeline split theo quý hoặc archive cũ |
| TVBH nghỉ — KHTN của họ | Trưởng phòng reassign sang TVBH khác (cập nhật cột `ma_TVBH`) |
| KH có 2 sdt | Dùng sdt chính, ghi sdt phụ vào `note` |
| KH active từ tháng trước | Giữ ma_KHTN cũ, không tạo mới |
| Pipeline đứng > 120 ngày | Cài auto chuyển sang "Mất" với lý do "kh không phản hồi" sau 120d |

---

## 11. Bonus: macro cập nhật lan_cap_nhat_cuoi (VBA)

> Nếu user dùng Excel desktop (không phải Web/Sheets), có thể cài macro tự cập nhật.

```vba
Private Sub Worksheet_Change(ByVal Target As Range)
    If Target.Column <= 22 And Target.Row >= 2 Then
        Application.EnableEvents = False
        Cells(Target.Row, 23).Value = Now()  ' Cột W (lan_cap_nhat_cuoi)
        Application.EnableEvents = True
    End If
End Sub
```

(Đặt trong sheet code của Pipeline. User cần `Enable Macro` khi mở file.)
