---
name: pgs-bi-report
description: Sinh BÁO CÁO BI cho Đại lý PGS - thay nguồn Power BI bằng D:\TCT PGS\Claude Data\, làm sạch dữ liệu (Power Query equiv), tái hiện Model View (relationships) và 122 measures DAX, xuất file pgs_data_slim.json + dashboard.html (Sales/Service/Market share/UIO/Model). Kích hoạt khi user nói "báo cáo BI", "Power BI replace", "dashboard PGS", "phân tích bán xe + dịch vụ + UIO" hoặc đề cập file model.bim.
---

# PGS BI Report Skill

Skill này tái hiện báo cáo Power BI gốc (`HONDA.pbix` / `model.bim`) lên một dashboard HTML chạy độc lập (không cần Power BI Desktop), với:

- Nguồn dữ liệu: `D:\TCT PGS\Claude Data\` (thay cho `D:\TCT PGS\1. QUẢN LÝ VÀ PHÂN TÍCH DỮ LIỆU\POWER BI\`)
- Làm sạch & combine: tương đương Power Query M code
- Model View: 47 relationships chính (dim ↔ fact)
- Measures: phần lớn trong 122 DAX measures (Sales, Service, Market share, UIO, KPI funnel)
- Dashboard: HTML + Chart.js, có bộ lọc Đại lý / Thương hiệu / Tỉnh / Năm / Tháng

## 1. Quy trình (5 bước)

### Bước 1 — Khảo sát nguồn
```bash
ls "D:\TCT PGS\Claude Data\"          # phải có MA DANH MUC, DU LIEU, KH DVPT,...
ls "D:\TCT PGS\Claude Data\DU LIEU\"  # có 2022/2023/2024/2025, file BANG KE *, BAO CAO *
ls "D:\TCT PGS\Claude Data\MA DANH MUC\"  # MA DON VI - 2026.xlsx,...
```

Nếu thiếu folder/file nào trong nguồn cũ → **bỏ qua** theo yêu cầu (ETL đã có guard).

### Bước 2 — Chạy ETL
Script `pgs_etl.py` / `run_etl_stages.py` nằm ngay trong thư mục skill này
(`.claude/skills/pgs-bi-report/`). Chạy trực tiếp từ đó:
```bash
cd .claude/skills/pgs-bi-report
python pgs_etl.py
# hoặc chạy theo stage:
python run_etl_stages.py A   # dims + small facts
python run_etl_stages.py B   # BK LSC (Service RO – nặng)
python run_etl_stages.py C   # measures + export JSON
```

Mặc định `ROOT` trỏ vào `D:\TCT PGS\Claude Data` (máy Windows của user). Nếu chạy
trong môi trường khác (vd. Claude Code cloud, không có ổ `D:\`), set biến môi
trường `PGS_DATA_ROOT` trỏ tới nơi thực sự chứa dữ liệu, ví dụ:
```bash
export PGS_DATA_ROOT="/path/to/Claude Data"
python pgs_etl.py
```
Có thể set thêm `PGS_BK_YEARS=2023,2024,2025` (mặc định chỉ 2025).

Đầu ra (ghi vào `output/` — cùng cấp với `pgs_etl.py`):
- `output/_cache/*.pkl` — cache trung gian
- `output/pgs_data.json` — đầy đủ (53 MB)
- `output/pgs_data_slim.json` — bản gọn cho HTML (1.7 MB)

### Bước 3 — Mở dashboard
`dashboard.html` đọc `pgs_data_slim.json` ở **cùng thư mục** với nó. Copy (hoặc symlink)
`output/pgs_data_slim.json` ra cùng chỗ với `dashboard.html`, rồi mở `dashboard.html` bằng browser (Chrome/Edge):
```bash
cp output/pgs_data_slim.json .
```

### Bước 4 — Tương tác
- Chọn Đại lý / Thương hiệu / Tỉnh / Năm / Tháng → bấm **Áp dụng**.
- 5 tabs: Bán xe • Dịch vụ • Thị phần • UIO • Model.
- Các biểu đồ + bảng + KPI tự cập nhật.

### Bước 5 — Refresh dữ liệu
Khi có file Excel mới trong `D:\TCT PGS\Claude Data\`:
```bash
# Xóa cache cũ (nếu file đã thay đổi):
rm -rf output/_cache
python pgs_etl.py
# refresh trình duyệt
```

## 2. Mapping nguồn cũ → mới

| Power BI gốc | Nguồn mới (Claude Data) |
|---|---|
| `POWER BI\MÃ DANH MỤC\` | `MA DANH MUC\` |
| `POWER BI\DỮ LIỆU\` | `DU LIEU\` |
| `POWER BI\DỮ LIỆU\2023 End\` | `DU LIEU\2023 End\` |
| `POWER BI\DỮ LIỆU\2024-CLĐ KTV\` | `DU LIEU\2024-CLĐ KTV\` |
| `ĐKM VN\HVN\` | **Không tồn tại → bỏ qua** |
| `ĐKM VN\District data.xlsx` | `District data N.csv` (file đã hoán đổi sang CSV) |
| `ĐKM VN\Toyota Share by Province.xlsb` | **Không tồn tại → bỏ qua** |
| `POWER BI\UIO 1 NĂM\`, `UIO 1 NĂM 2023\` | **Không tồn tại → bỏ qua** |
| `POWER BI\BỔ SUNG QUẬN HUYỆN.xlsx` | **Không tồn tại → bỏ qua** |
| `POWER BI\DỮ LIỆU\BÁO CÁO KHÁCH HÀNG TIỀM NĂNG.Xlsx` | **File mới corrupted, KHTN bỏ trống** |
| `POWER BI\DỮ LIỆU\BẢNG KÊ LẬP ĐIỀU KIỆN HỢP ĐỒNG.Xlsx` | **Dùng bản 2023 End** |

## 3. Tables (Power Query equiv)

Mỗi loader trong `pgs_etl.py` tái hiện một bước M-code:

| Loader | Bảng PowerBI | File nguồn mới | Note |
|---|---|---|---|
| `load_dimensions` | #Mã đơn vị, #Tỉnh PGS, #Danh mục kiểu xe, #KTV, ... | `MA DANH MUC\*.xlsx` | – |
| `load_xuat_xe` | XUẤT XE | `DU LIEU\BAO CAO CHI TIET KET QUA LAI LO BAN XE.Xlsx` | Replicates Thương hiệu N conditional |
| `load_ky_hd` | KÝ HĐ | `DU LIEU\2023 End\BANG KE LAP DIEU KIEN HOP DONG.Xlsx` | – |
| `load_kh_kd` | KH KD | `DU LIEU\BANG KE KE HOACH BAN XE.Xlsx` | UpperCase Nhân viên |
| `load_khtn` | KHTN | `DU LIEU\BAO CAO KHACH HANG TIEM NANG.Xlsx` | corrupted ⇒ empty |
| `load_bk_lsc` | BK LSC | `DU LIEU\{2023,2024,2025}\*.Xlsx` | Combine; Số lệnh→RO; LHSC split |
| `load_kh_dvpt` | KH DVPT | `DU LIEU\KH DVPT.xlsx` | – |
| `load_uio` | UIO DV | `DU LIEU\BAO CAO UIO.Xlsx` | – |
| `load_xe_ton/xe_tinh/xe_giao/xe_vao_ra` | XE TỒN / XE TỈNH / XE GIAO / XE VÀO RA | … | – |
| `load_ban_bh / cong_no_bh` | BÁN BẢO HIỂM / CÔNG NỢ BH | – | – |
| `load_luong / gv_vts / chi_phi_end` | LƯƠNG / GV VTS / CHI PHÍ End | SO CHI TIET TAI KHOAN-622/63223/627 | – |
| `load_hvn` | HVN | `\ĐKM VN\HVN\` (không có) | bỏ qua |
| `load_dkm` | ĐKM | `District data N.csv` | – |

## 4. Relationships (Model View)

47 quan hệ chính được khai báo nguyên văn trong `RELATIONSHIPS` của `pgs_etl.py` (mảng tuple `(from_table, from_col, to_table, to_col)`). Star schema:

- Trung tâm: `#Date`, `#Mã đơn vị`, `#Tỉnh PGS`, `#Danh mục kiểu xe`, `#DM công việc`, `#BẢO HIỂM`, `#DM SC`.
- Fact chính: XUẤT XE, KÝ HĐ, KH KD, KHTN, BK LSC, KH DVPT, UIO DV, HVN, ĐKM, BÁN BẢO HIỂM, LN BÁN XE.

## 5. Measures (DAX → Python/JS)

Một số measure cốt lõi đã được aggregate sẵn vào `measures` trong JSON:

| DAX gốc | Python aggregate | JS dùng ở dashboard |
|---|---|---|
| `COUNT(XUẤT XE[Số khung])` | `kpi_xx.xe_ban` | "Tổng xe bán" |
| `SUM(XUẤT XE[Tổng lãi gộp xe và phụ kiện (Cả KM)])` | `kpi_xx.lai_gop` | "Tổng Lãi gộp" |
| `BIEN LN KSNB = DIVIDE(SUM(lai_gop),SUM(gia_von))` | `total_lg/total_gv` | "Biên LN KSNB" |
| `TOTAL LX = DISTINCTCOUNT(RO)` | `bk.groupby(...).RO.nunique()` | "Tổng LX" |
| `DT/RO = DIVIDE(SUM(Tổng doanh thu),DISTINCTCOUNT(RO))` | `total_dt/total_lx` | "DT/RO" |
| `%CLĐ/DT = DIVIDE(TOTAL_CLD,Tổng doanh thu)` | `total_cld/total_dt` | "%CLĐ/DT" |
| `%PGS = DIVIDE(COUNT(XUẤT XE[Số khung]),SUM(ĐKM[Unit]))` | `total_pgs/total_dkm` | "%PGS Thị phần" |
| `UIO_DV = DISTINCTCOUNT(UIO DV[Số khung])` | `uio_summary.total_uio` | "Tổng UIO" |
| `%TT (HVN) = …SAMEPERIODLASTYEAR()` | sẽ thêm khi cần YoY | – |
| `KHTN funnel: KHTN/HOT/WARM/KHĐ` | `compute_measures.funnel` | – (KHTN file corrupted, bỏ qua) |

Các measure PY (Previous Year), SAMEPERIODLASTYEAR có thể tính tiếp bằng cách shift `Year` trong `sales_kpi`/`service_kpi` và merge.

## 6. Dashboard HTML — Cấu trúc

```
output/dashboard.html      ← entry point (mở bằng browser)
output/pgs_data_slim.json  ← dữ liệu rút gọn cho dashboard
output/pgs_data.json       ← bản đầy đủ
```

5 tabs:
1. **🚗 Bán xe** — KPI (Tổng xe / Lãi gộp / Biên LN), 4 biểu đồ (theo tháng, top dealer, cơ cấu brand, lãi gộp), bảng chi tiết.
2. **🔧 Dịch vụ** — KPI (LX, DT, DT/RO, %CLĐ/DT), so sánh TH vs KH, DT/RO theo dealer.
3. **📈 Thị phần** — %PGS vs đối thủ, ĐKM theo brand/tỉnh/tháng.
4. **🚙 UIO** — UIO theo dealer/tỉnh.
5. **🗺 Model** — Sơ đồ quan hệ + row counts.

Bộ lọc dùng chung cho cả 5 tabs.

## 7. Sửa lỗi thường gặp

| Triệu chứng | Xử lý |
|---|---|
| `pgs_data_slim.json 404` | Mở dashboard.html cùng thư mục với JSON; nếu dùng Edge mở local thì cần cho phép local file fetch (hoặc dùng `python -m http.server 8000` rồi truy cập `localhost:8000/dashboard.html`) |
| ETL chạy chậm > 30s | Chạy theo stage (A → B → C), dùng cache pickle |
| File `.Xlsx` báo "not a zip file" | EOCD bị mất / corrupted → ETL tự fallback sang file alternate, hoặc bỏ qua |
| Thiếu `Thương hiệu N` | Đảm bảo cột `Thương hiệu` có giá trị; xóa pickle cũ rồi chạy lại |

## 8. Cách mở rộng

- Thêm năm 2023/2024 vào BK LSC: `PGS_BK_YEARS=2023,2024,2025 python run_etl_stages.py B`.
- Thêm tab mới: copy cấu trúc tab trong `dashboard.html`, thêm `renderXxx()`.
- Thêm measure mới: viết trong `compute_measures()` ở `pgs_etl.py`.

## 9. Liên kết

- File ETL: `pgs_etl.py`, `run_etl_stages.py` (cùng thư mục skill)
- Cache: `output/_cache/*.pkl`
- Dashboard: `dashboard.html` (bundled sẵn trong skill) — copy hoặc symlink `output/pgs_data_slim.json` ra cùng thư mục với `dashboard.html` trước khi mở, hoặc mở thẳng `output/dashboard.html` nếu đã copy `dashboard.html` vào đó
- Data: `output/pgs_data_slim.json` (gọn) / `output/pgs_data.json` (đầy đủ)
