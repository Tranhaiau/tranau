# Reference 04 — Phân tích Đối thủ

> **Khi nào load:** User hỏi "Đối thủ nào đang mạnh?", "Tại sao mất share?",
> "So sánh giá Vios vs Accent". Hoặc khi `market-analyzer` thấy bất thường về thị phần.

---

## 1. Phân loại đối thủ

### 1.1 Đối thủ trực tiếp (Direct competitor)

Cùng phân khúc + cùng tệp KH mục tiêu.

| Phân khúc | Toyota | Hyundai | Mazda | Kia | Mitsubishi | Honda | Khác |
|---|---|---|---|---|---|---|---|
| Sedan A | Wigo | Grand i10 | — | Morning, Sonet | Attrage | Brio | VinFast Fadil |
| Sedan B | Vios | Accent | Mazda 2 | Soluto | — | City | — |
| Sedan C | Corolla Altis | Elantra | Mazda 3 | K3 | — | Civic | — |
| Sedan D | Camry | Sonata | Mazda 6 | K5 | — | Accord | — |
| B-SUV | Yaris Cross, Raize | Creta, Venue, Stargazer Cross | CX-3 | Sonet, Seltos | Xforce | HR-V | VF6 |
| C-SUV | Corolla Cross | Tucson | CX-5 | Sportage | Outlander | CR-V | VF7 |
| D-SUV | Fortuner, Land Cruiser Prado | Santa Fe, Palisade | CX-8 | Sorento | Pajero Sport | — | VF8 |
| MPV | Innova, Innova Cross, Veloz | Stargazer, Custin | — | Carnival, Carens | Xpander | BR-V | VF9 |
| Pickup | Hilux | — | BT-50 | — | Triton | — | Ranger (Ford) |

### 1.2 Đối thủ gián tiếp (Indirect competitor)

Cùng tệp KH nhưng khác phân khúc (KH có thể chuyển hướng):
- KH định mua C-SUV nhưng "lên đời" sang D-SUV.
- KH định mua Sedan B nhưng "đổi gu" sang B-SUV.

### 1.3 Đối thủ cùng đại lý hệ thống (Internal competitor)

Đại lý PGS Đồng Nai cạnh tranh với:
- Đại lý Toyota khác trong vùng Đông Nam Bộ.
- Đại lý cùng nhóm hãng (vd Toyota Bến Thành — nếu có).

→ Đây là góc nhìn để tính **share of dealer** (xem `02-market-share-formulas.md` mục 3).

---

## 2. Khung phân tích đối thủ (4P + S)

### 2.1 Product

```
- Phân khúc cùng / chéo phân khúc
- Phiên bản nào đang bán tốt nhất
- Tính năng nổi bật / tính năng thiếu
- Tần suất facelift / all-new
```

### 2.2 Price

```
- Giá niêm yết
- Chương trình khuyến mãi đang chạy
- Tỷ lệ chiết khấu thực tế (kể cả ngầm)
- Giá option/phụ kiện
```

### 2.3 Place

```
- Số đại lý trên địa bàn
- Vị trí showroom (so với PGS)
- Kênh phân phối phụ (online, popup)
```

### 2.4 Promotion

```
- Quảng cáo (TVC, billboard, digital)
- Sự kiện cộng đồng
- Sponsor / influencer
- KOL/KOC
```

### 2.5 Service (yếu tố bonus quan trọng cho ô-tô)

```
- Chính sách bảo hành
- Số xưởng dịch vụ
- Phụ tùng có sẵn / lead time đặt hàng
- Chương trình KH thân thiết
```

---

## 3. Code Python — phân tích thị phần đối thủ trong phân khúc

### 3.1 Tìm đối thủ đang tăng trưởng nhanh nhất

```python
def fastest_growing_competitors(dltt_cur, dltt_prev, segment, top_n=5):
    """
    So sánh DLTT theo TH × model trong segment giữa 2 kỳ.
    Trả về top N model tăng trưởng (số tuyệt đối).
    """
    cur = dltt_cur[dltt_cur['phan_khuc'] == segment]
    prev = dltt_prev[dltt_prev['phan_khuc'] == segment]

    cur_count = cur.groupby(['TH', 'model']).size().reset_index(name='cur')
    prev_count = prev.groupby(['TH', 'model']).size().reset_index(name='prev')

    merged = cur_count.merge(prev_count, on=['TH', 'model'], how='outer').fillna(0)
    merged['delta_abs'] = merged['cur'] - merged['prev']
    merged['delta_pct'] = ((merged['cur'] - merged['prev']) /
                           merged['prev'].replace(0, 1) * 100)

    return merged.sort_values('delta_abs', ascending=False).head(top_n)
```

### 3.2 Heatmap thị phần model × tỉnh (cho competitor benchmark)

```python
def competitor_heatmap(dltt, segment, period_label):
    """
    Vẽ heatmap: rows = model trong segment, cols = top 10 tỉnh.
    """
    df = dltt[dltt['phan_khuc'] == segment]
    pivot = df.pivot_table(
        index='model',
        columns='tinh',
        values='vin',
        aggfunc='count',
        fill_value=0
    )
    # Giữ top 10 tỉnh có volume cao nhất
    top_provinces = pivot.sum().sort_values(ascending=False).head(10).index
    pivot = pivot[top_provinces]

    # Render bằng matplotlib hoặc trả về dict cho chart_display_v0
    return pivot
```

### 3.3 Cảnh báo đối thủ tăng trưởng đột biến

```python
def alert_competitor_surge(dltt_history_3_periods, segment, threshold_mom=0.20):
    """
    Cảnh báo nếu 1 model đối thủ tăng > 20% MoM 2 kỳ liên tiếp.
    """
    alerts = []
    cur, prev1, prev2 = dltt_history_3_periods   # 3 kỳ gần nhất

    for model in cur[cur['phan_khuc'] == segment]['model'].unique():
        n_cur = (cur['model'] == model).sum()
        n_prev1 = (prev1['model'] == model).sum()
        n_prev2 = (prev2['model'] == model).sum()

        if n_prev2 < 5:  # tránh false positive với mẫu nhỏ
            continue

        mom1 = (n_prev1 - n_prev2) / n_prev2
        mom2 = (n_cur - n_prev1) / max(n_prev1, 1)

        if mom1 > threshold_mom and mom2 > threshold_mom:
            alerts.append({
                'model': model,
                'mom_2_kỳ_truoc': mom1 * 100,
                'mom_kỳ_gan_nhat': mom2 * 100,
                'volume_cur': n_cur,
                'verdict': 'Đối thủ surge — cần phản ứng nhanh'
            })

    return alerts
```

---

## 4. Chính sách giá — bảng tham chiếu (cập nhật định kỳ)

> ⚠️ Bảng này **thay đổi liên tục**. Khi user hỏi giá hiện tại, phải dùng `web_search`
> để verify trước khi đưa vào báo cáo. KHÔNG dùng giá trong file này làm nguồn duy nhất.

### 4.1 Cấu trúc bảng giá nội bộ

```yaml
ngay_cap_nhat: "2026-04-15"
nguon: "công bố hãng + khảo sát đại lý cạnh tranh"
sedan_B:
  toyota_vios:
    base: 458_000_000
    cao: 545_000_000
    khuyen_mai_dang_chay: "Tặng BHVC năm đầu + 5tr giảm giá"
  hyundai_accent:
    base: 439_000_000
    cao: 569_000_000
    khuyen_mai_dang_chay: "Hỗ trợ 50% trước bạ"
  honda_city:
    base: 499_000_000
    cao: 599_000_000
    khuyen_mai_dang_chay: "Tặng BHVC + 10tr"
  mazda_2:
    base: 408_000_000
    cao: 548_000_000
    khuyen_mai_dang_chay: "Giảm 30tr trực tiếp"
b_suv:
  toyota_yaris_cross:
    base: 650_000_000
    cao: 765_000_000
  hyundai_creta:
    base: 599_000_000
    cao: 729_000_000
  mitsubishi_xforce:
    base: 599_000_000
    cao: 705_000_000
# ... thêm các phân khúc khác
```

### 4.2 So sánh giá net (sau khuyến mãi) — code

```python
def compare_price_net(price_table, segment):
    """
    Tính giá net = base - khuyến mãi quy đổi tiền mặt.
    Trả về bảng so sánh để TVBH dùng khi báo giá.
    """
    rows = []
    for model_id, info in price_table[segment].items():
        km_value = parse_promo_to_cash(info.get('khuyen_mai_dang_chay', ''))
        rows.append({
            'model': model_id,
            'gia_niem_yet': info['base'],
            'gia_cao': info['cao'],
            'khuyen_mai_quy_doi': km_value,
            'gia_net': info['base'] - km_value
        })
    return pd.DataFrame(rows).sort_values('gia_net')

def parse_promo_to_cash(promo_text):
    """
    Quy đổi khuyến mãi sang tiền mặt:
    - "Hỗ trợ 50% trước bạ" → ~6% giá xe (giả định trước bạ 12%)
    - "BHVC năm đầu" → ~12tr (Sedan B)
    - "Giảm Xtr trực tiếp" → X tr
    """
    # ... implement logic
    pass
```

### 4.3 Khi nào giá là yếu tố quyết định?

| Phân khúc | Trọng số giá trong quyết định KH |
|---|---|
| Sedan A (giá thấp) | Rất cao (60-70%) |
| Sedan B | Cao (50%) |
| C-SUV | Trung bình (35-40%) — tính năng quan trọng hơn |
| D-SUV trở lên | Thấp (20-30%) — KH ưu tiên thương hiệu, tiện nghi |
| Premium | Rất thấp (< 20%) — KH ưu tiên branding |

---

## 5. SWOT phản chiếu (so PGS với đối thủ)

### 5.1 Template SWOT

```yaml
# So PGS Đồng Nai vs Hyundai Long Khánh
strengths:
  - "PGS có 4 năm kinh nghiệm địa bàn, mạng lưới refer tốt"
  - "Lái thử Toyota dễ tiếp cận với 12 xe trưng bày"
weaknesses:
  - "Showroom xa cụm KCN Amata (10km vs đối thủ 3km)"
  - "Lead online conversion thấp 7% (đối thủ ước 15%)"
opportunities:
  - "DLTT B-SUV địa bàn tăng 28% YoY — Yaris Cross & Stargazer cạnh tranh"
  - "Cụm KCN Long Thành mở rộng — KH mới 2027"
threats:
  - "Hyundai Custin ra mắt T6 — đe doạ Innova Cross share"
  - "Mazda CX-5 giảm giá 30tr — cạnh tranh với Corolla Cross"
```

### 5.2 Code: tự động phát hiện threats từ DLTT

```python
def auto_detect_threats(dltt_cur, dltt_prev, sales_pgs, dia_ban):
    """
    Phát hiện threats:
    1. Đối thủ trực tiếp tăng share
    2. Model đối thủ mới ra mắt có volume > 10
    3. PGS share trong phân khúc giảm > 3 điểm %
    """
    threats = []

    # Phân khúc nào PGS share giảm
    for segment in dltt_cur['phan_khuc'].unique():
        # Tính share PGS
        n_dltt_seg_cur = ((dltt_cur['phan_khuc'] == segment) &
                          (dltt_cur['tinh'] == dia_ban)).sum()
        n_pgs_seg_cur = ((sales_pgs['phan_khuc'] == segment) &
                         (sales_pgs['ngay_HD'] >= dltt_cur['ngay_dang_ky'].min())).sum()
        share_cur = n_pgs_seg_cur / max(n_dltt_seg_cur, 1)

        n_dltt_seg_prev = ((dltt_prev['phan_khuc'] == segment) &
                           (dltt_prev['tinh'] == dia_ban)).sum()
        n_pgs_seg_prev = ...  # tương tự
        share_prev = n_pgs_seg_prev / max(n_dltt_seg_prev, 1)

        if share_prev - share_cur > 0.03:
            threats.append({
                'type': 'share_drop',
                'segment': segment,
                'delta': share_cur - share_prev,
                'verdict': f'PGS share {segment} giảm {(share_cur-share_prev)*100:.1f} điểm %'
            })

    return threats
```

---

## 6. Counter-narrative (kịch bản phản công)

Khi TVBH bị KH so sánh "Bên A bán Y giá rẻ hơn 20tr":

### 6.1 Khung trả lời chuẩn (chuyển cho `06-action-playbook.md`)

```
1. Acknowledge: "Anh/chị nói đúng, mức giá đó hấp dẫn về thoạt nhìn."
2. Reframe: "Nhưng khi tính tổng chi phí sở hữu (TCO) 5 năm:
   - Phụ tùng X chính hãng tại PGS rẻ hơn Y%
   - Bảo hành mở rộng PGS có chương trình Z
   - Giá bán lại sau 5 năm cao hơn Y triệu (theo data thị trường)
3. Differentiate: nêu 1-2 USP của PGS không phải về giá."
```

### 6.2 Bảng TCO 5 năm (template)

```python
def calculate_5yr_TCO(model_data):
    """
    TCO = giá xe + nhiên liệu + bảo dưỡng + bảo hiểm + đăng kiểm + giảm giá trị
    """
    return {
        'gia_xe': model_data['price'],
        'nhien_lieu_5yr': model_data['fuel_l_per_100km'] * 25_000 * 5 * 25_000,  # giả định
        'bao_duong_5yr': model_data['avg_bd_per_year'] * 5,
        'bao_hiem_5yr': model_data['price'] * 0.015 * 5,
        'dang_kiem_phi_5yr': 1_000_000,
        'giam_gia_tri': model_data['price'] * (1 - model_data['residual_5yr_pct']),
        'TCO_5yr': '...'  # cộng tổng
    }
```

---

## 7. Quy tắc đưa thông tin đối thủ vào báo cáo

1. **Số liệu phải verify được** — DLTT là nguồn neo, không dùng tin đồn.
2. **Không công kích trực tiếp** — chỉ so chỉ số, không bình luận về quản lý đối thủ.
3. **Cập nhật giá theo tuần** — bảng giá > 30 ngày là rủi ro lệch.
4. **Phân biệt tin chính thức vs tin chợ** — ghi nguồn.
5. **Khi không chắc — search web** — không bịa.

---

## 8. Edge cases & warnings

| Tình huống | Cách xử lý |
|---|---|
| Đối thủ ra model mới, chưa có DLTT | Dùng `web_search` để biết ngày ra mắt, đề xuất theo dõi 2 kỳ |
| Đối thủ giảm giá flash | Cảnh báo TVBH ngay, không đợi báo cáo tháng |
| KH nói "bên A báo giá Y" mà giá đó dưới giá vốn | Verify với manager đối thủ qua quan hệ; có thể là "câu khách" |
| Hãng PGS thay đổi MSRP giữa kỳ | Tách báo cáo thành 2 đoạn (trước/sau ngày thay đổi) |
