# Reference 03 — Phân tích Vùng miền & Chân dung Khách hàng

> **Khi nào load:** User hỏi câu kiểu "KH ở đâu mua nhiều?", "Vùng nào tăng trưởng?",
> "Ai là KH chính của dòng B-SUV?". Hoặc khi `market-analyzer` cần phân khúc địa lý sâu hơn tỉnh.

---

## 1. Phân vùng địa lý chuẩn

### 1.1 Cấp độ phân tích

| Cấp | Khi dùng | Mẫu tối thiểu | Ví dụ |
|---|---|---|---|
| **Quốc gia** | Báo cáo hãng | hàng ngàn | "Toàn Việt Nam Q1/2026" |
| **Vùng** (4-7 vùng) | Lập kế hoạch chiến lược | hàng trăm | "Đông Nam Bộ" |
| **Tỉnh/TP** | Kế hoạch tỉnh | 50+ | "Đồng Nai" |
| **Huyện/Quận** | Kế hoạch SC địa bàn | 20+ | "Biên Hòa, Long Thành" |
| **Phường/Xã** | Kế hoạch sự kiện cụm | 10+ | "Phường An Bình" |

### 1.2 Định nghĩa vùng (chuẩn PGS)

```python
VUNG_MIEN = {
    'Bắc Bộ': ['Hà Nội', 'Hải Phòng', 'Quảng Ninh', 'Bắc Ninh', 'Hưng Yên',
               'Hà Nam', 'Nam Định', 'Thái Bình', 'Hải Dương', 'Vĩnh Phúc'],
    'Bắc Trung Bộ': ['Thanh Hóa', 'Nghệ An', 'Hà Tĩnh', 'Quảng Bình',
                     'Quảng Trị', 'Thừa Thiên Huế'],
    'Nam Trung Bộ': ['Đà Nẵng', 'Quảng Nam', 'Quảng Ngãi', 'Bình Định',
                     'Phú Yên', 'Khánh Hòa', 'Ninh Thuận', 'Bình Thuận'],
    'Tây Nguyên': ['Kon Tum', 'Gia Lai', 'Đắk Lắk', 'Đắk Nông', 'Lâm Đồng'],
    'Đông Nam Bộ': ['TP.HCM', 'Bình Dương', 'Đồng Nai', 'Bà Rịa - Vũng Tàu',
                    'Tây Ninh', 'Bình Phước'],
    'Tây Nam Bộ': ['Long An', 'Tiền Giang', 'Bến Tre', 'Trà Vinh', 'Vĩnh Long',
                   'Đồng Tháp', 'An Giang', 'Kiên Giang', 'Cần Thơ', 'Hậu Giang',
                   'Sóc Trăng', 'Bạc Liêu', 'Cà Mau'],
    'Trung du miền núi phía Bắc': ['Hà Giang', 'Cao Bằng', 'Lạng Sơn', 'Bắc Giang',
                                    'Phú Thọ', 'Thái Nguyên', 'Bắc Kạn', 'Tuyên Quang',
                                    'Lào Cai', 'Yên Bái', 'Lai Châu', 'Sơn La',
                                    'Điện Biên', 'Hòa Bình']
}

def map_tinh_to_vung(tinh: str) -> str:
    for vung, tinhs in VUNG_MIEN.items():
        if tinh in tinhs:
            return vung
    return 'Khác'
```

### 1.3 Đặc điểm tiêu thụ xe theo vùng (kinh nghiệm thực tiễn)

| Vùng | Đặc điểm KH | Phân khúc thường mạnh | Lưu ý |
|---|---|---|---|
| Bắc Bộ (HN) | Quan tâm thương hiệu, thiết kế | Sedan B/C, SUV C/D | Thị trường trưởng thành, cạnh tranh cao |
| Đông Nam Bộ (HCM, Đồng Nai) | Đa dạng, KH trẻ, ưa SUV | B-SUV, C-SUV, MPV | Thị trường lớn nhất, tỷ lệ KH B2C cao |
| Tây Nam Bộ | Ưu tiên giá rẻ, tiết kiệm | Sedan A/B, MPV bình dân | Tỷ lệ Pickup nhỏ tăng |
| Tây Nguyên | Pickup, SUV gầm cao | Pickup, C-SUV | Đường xấu, ưu tiên off-road |
| Bắc Trung Bộ | Bình dân, tiện dụng | Sedan B, MPV | Ngân sách hạn chế hơn |

> ⚠️ Đây là **xu hướng quan sát**, không phải quy luật cứng. Mỗi đại lý cần verify
> bằng dữ liệu DLTT thực tế của địa bàn mình.

---

## 2. Phân khúc Khách hàng (B2C)

### 2.1 Theo độ tuổi (theo dữ liệu CCCD/CMND nếu có)

```python
AGE_SEGMENTS = {
    'Gen Z': (18, 27),
    'Millennials trẻ': (28, 35),
    'Millennials già': (36, 43),
    'Gen X': (44, 59),
    'Boomer': (60, 75)
}

def segment_by_age(df, dob_col='ngay_sinh', as_of_date='2026-01-01'):
    df = df.copy()
    df['age'] = (pd.to_datetime(as_of_date) - pd.to_datetime(df[dob_col])).dt.days // 365
    def assign(age):
        for seg, (lo, hi) in AGE_SEGMENTS.items():
            if lo <= age <= hi:
                return seg
        return 'Khác'
    df['age_segment'] = df['age'].apply(assign)
    return df
```

### 2.2 Theo nghề nghiệp / mục đích sử dụng

| Phân khúc KH | Đặc điểm | Mẫu xe ưa thích |
|---|---|---|
| **KH gia đình trẻ** | 28-40 tuổi, có 1-2 con nhỏ | C-SUV, MPV (Innova, Xpander, Xforce) |
| **KH doanh nhân** | 35-55 tuổi, chủ DN nhỏ | D-SUV, Sedan D (Camry, Sorento, CX-8) |
| **KH chạy dịch vụ** | Mua xe để chạy taxi/grab | Sedan B (Vios, Accent, City), MPV (Innova) |
| **KH đầu tiên** (first-time buyer) | 25-32 tuổi, thu nhập 15-25tr/tháng | Sedan A/B (Wigo, Morning, City) |
| **KH thay xe** | Đã có xe, lên đời sau 3-5 năm | Tăng 1 bậc phân khúc |
| **KH cao cấp** | Trên 50 tuổi, đã mua nhiều xe | Sedan E, SUV cao cấp (Land Cruiser, Palisade) |

### 2.3 Theo nguồn KHTN (lead source)

```python
def conversion_by_source(quan_tri_df):
    """
    Tỷ lệ chốt theo nguồn KHTN — biết kênh nào hiệu quả nhất.
    """
    pivot = quan_tri_df.pivot_table(
        index='nguon_KHTN',
        columns='trang_thai',
        values='ma_KHTN',
        aggfunc='count',
        fill_value=0
    )
    if 'HĐ' in pivot.columns:
        pivot['total'] = pivot.sum(axis=1)
        pivot['ty_le_chot'] = pivot['HĐ'] / pivot['total']
    return pivot.sort_values('ty_le_chot', ascending=False)

# Vd output điển hình:
# nguon_KHTN  Cold  Warm  Hot  HĐ  Mất  total  ty_le_chot
# refer        12    18    8   15   7    60      0.250    ★ tốt nhất
# walkin       45    32   18   22  18   135      0.163
# sukien       28    19   12   14  12    85      0.165
# online       65    28    9   11  35   148      0.074    ★ tệ nhất, cần xem lại
# data_cu      22    15    7    9   8    61      0.148
```

---

## 3. Phân tích KH theo cụm địa bàn (geo-clustering)

### 3.1 Heatmap doanh số theo huyện/cụm KCN

```python
def sales_heatmap_by_district(sales_pgs, dia_ban):
    """
    Trả về dict {huyen: doanh_so} để vẽ heatmap.
    """
    df = sales_pgs[sales_pgs['tinh'] == dia_ban]  # giả định có cột tinh
    return df.groupby('huyen').size().to_dict()
```

### 3.2 Tìm "cụm trắng" (white space) — vùng có DLTT cao nhưng PGS share thấp

Đây là kiểu insight quan trọng cho `plan-builder` (nhóm Marketing/Sự kiện).

```python
def find_white_space(dltt, sales_pgs, TH_target='Toyota', dia_ban='Đồng Nai',
                     min_dltt=20):
    """
    Trả về danh sách huyện có:
    - DLTT TH_target ≥ min_dltt
    - Share of PGS trong huyện < 50% (bench typical 80%)
    """
    dltt_f = dltt[(dltt['TH'] == TH_target) & (dltt['tinh'] == dia_ban)]
    sales_f = sales_pgs[(sales_pgs['TH'] == TH_target) & (sales_pgs.get('tinh') == dia_ban)]

    dltt_huyen = dltt_f.groupby('huyen').size().reset_index(name='dltt_count')
    sales_huyen = sales_f.groupby('huyen').size().reset_index(name='sales_count')

    merged = dltt_huyen.merge(sales_huyen, on='huyen', how='left').fillna(0)
    merged['share_pgs'] = merged['sales_count'] / merged['dltt_count']

    white_space = merged[
        (merged['dltt_count'] >= min_dltt) &
        (merged['share_pgs'] < 0.50)
    ].sort_values('dltt_count', ascending=False)

    return white_space
```

Sub-agent `plan-builder` dùng kết quả này để đề xuất:
- Sự kiện lái thử ở huyện đó.
- Mở booth tại trung tâm thương mại / KCN.
- Tăng cường marketing local.

---

## 4. Phân tích chân dung KH cho 1 model cụ thể

```python
def model_buyer_profile(sales_pgs, model_name):
    """
    Trả về chân dung KH đã mua model này:
    - Phân bố tuổi
    - Phân bố nguồn KHTN
    - Phân bố vùng miền
    - Phân bố thời gian từ Cold → HĐ
    """
    df = sales_pgs[sales_pgs['model'] == model_name]
    if len(df) < 30:
        return {'warning': 'Mẫu < 30, không đủ kết luận'}

    profile = {
        'n_HD': len(df),
        'avg_gia_ban': df['gia_ban'].mean(),
        'top_nguon_KHTN': df['nguon_KHTN'].value_counts(normalize=True).head(3).to_dict(),
        'top_loai_KH': df['loai_KH'].value_counts(normalize=True).head(3).to_dict(),
    }
    if 'tinh' in df.columns:
        profile['top_tinh'] = df['tinh'].value_counts(normalize=True).head(5).to_dict()
    return profile
```

### Mẫu output (Toyota Vios — Đồng Nai)

```yaml
n_HD: 142
avg_gia_ban: 538_000_000
top_nguon_KHTN:
  walkin: 0.42
  refer: 0.28
  sukien: 0.18
top_loai_KH:
  B2C: 0.78
  Taxi: 0.18                  # cao bất thường — Vios là xe taxi phổ biến
  Fleet: 0.04
top_tinh:
  Đồng Nai: 0.84
  TP.HCM: 0.09                # KH lân cận sang mua
  Bình Dương: 0.05
```

---

## 5. Phân tích thay xe (replacement cycle)

### 5.1 Khi nào KH thay xe?

```python
def estimate_replacement_window(uio_df, today):
    """
    Dự báo VIN nào sắp đến chu kỳ thay xe (3-5 năm sau giao).
    Dựa trên ngày bán đầu tiên (nếu có) hoặc nam_SX.
    """
    df = uio_df.copy()
    df['tuoi_xe'] = today.year - df['nam_SX']

    # Phân nhóm theo tuổi
    df['nhom_tuoi'] = pd.cut(
        df['tuoi_xe'],
        bins=[0, 2, 4, 6, 9, 100],
        labels=['Mới (0-2 năm)', 'Sắp thay (3-4 năm)',
                'Thay được (5-6 năm)', 'Quá hạn (7-9 năm)', 'Cũ (10+)']
    )
    return df.groupby('nhom_tuoi').size()
```

### 5.2 Cross-sell upgrade

KH mua Vios 4 năm trước → có thể upgrade lên Corolla Cross / Corolla Altis.
KH mua Innova 5 năm trước → có thể upgrade lên Innova Cross / Fortuner.

```python
UPGRADE_PATH = {
    # Toyota
    'Wigo': ['Vios'],
    'Vios': ['Yaris Cross', 'Corolla Altis', 'Corolla Cross'],
    'Corolla Altis': ['Camry', 'Corolla Cross'],
    'Corolla Cross': ['Yaris Cross', 'Camry'],
    'Innova': ['Innova Cross', 'Fortuner'],
    'Fortuner': ['Land Cruiser Prado'],
    # Hyundai
    'Grand i10': ['Accent'],
    'Accent': ['Elantra', 'Creta', 'Stargazer'],
    'Elantra': ['Sonata', 'Tucson'],
    'Tucson': ['Santa Fe'],
    'Santa Fe': ['Palisade'],
    # ... thêm Mazda, Kia ở phụ lục
}

def suggest_upgrade_for_VIN(vin_info):
    current = vin_info['model']
    return UPGRADE_PATH.get(current, [])
```

---

## 6. Insight pattern thường gặp & cách diễn giải

### 6.1 "Phân khúc B-SUV tăng share trên địa bàn — PGS chỉ giữ 18%"

**Cách diễn giải đúng (cho `plan-builder`):**
- Phân tích cụ thể: Hyundai Creta / Toyota Yaris Cross / Mitsubishi Xforce → ai đang chiếm?
- Insight kèm hành động: tổ chức lái thử Yaris Cross / Stargazer ở 2 KCN có DLTT B-SUV cao nhất.
- Số liệu hỗ trợ: "DLTT B-SUV địa bàn T4 = 280; PGS bán 50 → mất 80 cơ hội tiềm năng".

### 6.2 "Tỷ lệ chốt online thấp (7%) so với refer (25%)"

**Diễn giải đúng:**
- Online lead chất lượng thấp hơn (KH chưa committed).
- Nhưng volume online cao → vẫn đáng đầu tư.
- Action: training TVBH chuyên xử lý lead online + tự động hoá nuôi dưỡng (nurturing).

### 6.3 "KH 28-35 tuổi mua C-SUV nhiều nhất, nhưng PGS marketing chủ yếu là Sedan B"

**Diễn giải:** lệch chiến lược marketing với hành vi KH địa bàn → sub-agent `plan-builder`
đề xuất nhóm Marketing.

---

## 7. Quy tắc trình bày phần "Chân dung KH" trong báo cáo

Phần này thường là **mục 2 hoặc 2.b** trong cấu trúc báo cáo 5 phần:

```markdown
## 2.b. Chân dung khách hàng (B2C, kỳ T4/2026, n=89)

- **Phân bố tuổi:** chủ yếu 28-43 tuổi (68%), Gen X chiếm 20%.
- **Top 3 nguồn KHTN:** Walkin (42%), Refer (28%), Sự kiện (18%).
- **Top 3 huyện:** Biên Hòa (54%), Long Khánh (18%), Trảng Bom (12%).
- **Phân khúc nóng:** B-SUV (Yaris Cross, Stargazer) — 28% HĐ, +6 điểm % vs T3.
- **Cụm trắng:** Long Thành DLTT cao 47 xe Toyota nhưng PGS chỉ chốt 12 → share 25%
  (benchmark hệ thống 80%).
```

> Quy tắc: **mỗi câu phải có số** — không có số = không có insight.
