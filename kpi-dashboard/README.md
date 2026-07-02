# KPI Dashboard — Dịch vụ Phụ tùng (DVPT) · PGS Corp

Dashboard KPI dịch vụ – phụ tùng dạng **một file HTML tự chứa**: mở bằng
trình duyệt là chạy, không cần internet (Chart.js đã nhúng sẵn), không cần
server.

## Cách cập nhật dữ liệu mỗi kỳ

```bash
# 1. Copy 3 file CSV mới (đè lên file cũ) vào thư mục data/
#    data/fact.csv  ·  data/dim_date.csv  ·  data/dim_org.csv

# 2. Build (ngày "dữ liệu đến hết" mặc định = hôm nay;
#    build lại dữ liệu cũ thì chỉ định rõ: --asof YYYY-MM-DD)
node build.js
node build.js --asof 2026-06-23

# 3. Mở kết quả
#    dist/index.html  ← file dashboard hoàn chỉnh, gửi ai cũng mở được
```

Chỉ cần cài Node.js (bản 18 trở lên) — script không dùng thư viện ngoài.

## Cấu trúc project

| Đường dẫn | Vai trò |
|---|---|
| `data/fact.csv` | Bảng fact: mỗi dòng = 1 đại lý × 1 tháng, 45 cột chỉ số |
| `data/dim_date.csv` | Danh sách kỳ có dữ liệu (`y`, `m`) |
| `data/dim_org.csv` | Danh sách đại lý (`code`, `name`, `brand`, `color`) |
| `template.html` | Giao diện dashboard (không chứa dữ liệu) — sửa layout/biểu đồ ở đây |
| `vendor/` | Chart.js 4.4.1 + plugin datalabels 2.2.0 (nhúng vào file build) |
| `build.js` | Ghép template + vendor + dữ liệu CSV → `dist/index.html` |
| `dist/index.html` | **Kết quả build** — file duy nhất cần gửi đi (không commit vào git) |

## Định dạng CSV

- Mã hoá **UTF-8** (có hoặc không BOM đều được — Excel xuất ra là dùng được).
- Dấu phân cách `,` hoặc `;` — script tự nhận diện.
- Số thập phân dùng **dấu chấm** (`245.603`), không dùng dấu phẩy.
- Ô để trống = không có dữ liệu (ví dụ các cột `csi_*` những kỳ chưa khảo sát).
- Dòng đầu tiên là tên cột; tên cột phải khớp với file mẫu hiện có.

Cột bắt buộc: `fact.csv` cần `o`, `y`, `m` (mã đại lý, năm, tháng);
`dim_org.csv` cần `code`, `name`, `brand`, `color`. Script sẽ báo lỗi rõ
ràng nếu thiếu cột hoặc thiếu file, và cảnh báo nếu `fact.csv` chứa mã đại
lý không có trong `dim_org.csv`.

## Nguồn dữ liệu

CSV export từ hệ thống PGS, các view: `Vw_DV_KeHoach2`, `Vw_DV_KTV`,
`Vw_DV_VatTuSon`, `Vw_DV_LSC`, `Vw_CR_KQ_CSKH_DV`
(mô hình Dim_Date × Dim_Org × Fact).

## Xem trên điện thoại

**Đừng xem bằng khung xem trước trong ứng dụng** (bấm thẳng vào file đính
kèm trong Zalo/Messages/Claude — Quick Look của iPhone): trình xem trước
này chặn JavaScript nên dashboard chỉ hiện khung trống với "Đang tải...".

Cách đúng: **lưu file về máy rồi mở bằng Safari hoặc Chrome**
(iPhone: tải về → app Tệp → giữ file → Chia sẻ → Safari;
Android: tải về → mở bằng Chrome). Giao diện đã responsive cho màn hình
điện thoại. Ổn định nhất là đưa file lên một địa chỉ web nội bộ và mở
bằng link.

## Sửa giao diện / biểu đồ

Sửa trực tiếp `template.html` rồi chạy lại `node build.js`. Không sửa
`dist/index.html` — file này bị ghi đè mỗi lần build.
