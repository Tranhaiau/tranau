# Reference 02 — Công thức Thị phần & YoY/MoM

> **Khi nào load:** Sub-agent `market-analyzer` cần tính thị phần / share of dealer / tăng trưởng.
> Đây là file công thức cốt lõi — sai 1 công thức → toàn bộ báo cáo sai.

---

## 1. Khái niệm cơ bản

### 1.1 Phân biệt 2 góc nhìn thị phần

Có **2 góc nhìn khác nhau**, người mới hay nhầm:

| Chỉ số | Mẫu số | Ý nghĩa | Ví dụ |
|---|---|---|---|
| **Thị phần TH** (Market share) | Tổng DLTT toàn ngành (mọi TH) | TH chiếm bao nhiêu % thị trường | "Toyota chiếm 22% xe đăng ký mới ở Đồng Nai" |
| **Share of dealer** (PGS Power Index) | Tổng doanh số TH đó trên địa bàn | PGS chiếm bao nhiêu % của TH trong địa bàn | "PGS chiếm 84% xe Toyota bán ở Đồng Nai" |

**Tại sao quan trọng:**
- Thị phần TH ↑ mà share of dealer ↓ → TH thắng nhưng PGS thua trong nội bộ TH (đối thủ cùng TH mạnh hơn).
- Thị phần TH ↓ mà share of dealer ↑ → PGS giữ được khách trong TH suy giảm — vẫn cần lo cho dài hạn.

### 1.2 Quy tắc tách B2C khỏi Fleet/Taxi

Hầu hết phân tích **chỉ dùng B2C** vì Fleet/Taxi:
- Mua sỉ, không phản ánh hành vi KH cá nhân.
- Giá khác hẳn (chiết khấu cao).
- Quyết định tập trung (1 fleet manager quyết hàng trăm xe).

```python
def filter_b2c(df):
    return df[df['loai_KH'] == 'B2C'].copy()

# Khi báo cáo, ghi rõ scope ở header:
# "Báo cáo dưới đây tính trên tập B2C; Fleet/Taxi/Corporate được trình bày riêng ở Phụ lục."
```

---

## 2. Thị phần TH (Market Share)

### 2.1 Công thức

```
Thị phần TH (X) = DLTT của TH X / Tổng DLTT toàn ngành × 100%
```

Trong **cùng 1 địa bàn + cùng 1 kỳ + cùng 1 tập KH** (B2C hoặc đầy đủ).

### 2.2 Code Python

```python
import pandas as pd

def market_share_by_th(dltt: pd.DataFrame, scope_b2c=True):
    """
    Trả về DataFrame: TH | doanh_so_TH | thi_phan_pct
    """
    df = filter_b2c(dltt) if scope_b2c else dltt.copy()
    total = len(df)
    if total == 0:
        raise ValueError('DLTT empty after filter — check scope')

    result = (df.groupby('TH').size()
                .reset_index(name='doanh_so_TH'))
    result['thi_phan_pct'] = result['doanh_so_TH'] / total * 100
    result = result.sort_values('thi_phan_pct', ascending=False)
    return result, total

# Sanity check (Hook H4)
def assert_market_share_valid(result):
    assert (result['thi_phan_pct'] >= 0).all(), 'Có thị phần âm'
    assert (result['thi_phan_pct'] <= 100).all(), 'Có thị phần > 100%'
    total_pct = result['thi_phan_pct'].sum()
    assert abs(total_pct - 100) < 0.01, f'Tổng thị phần không = 100%: {total_pct}'
```

### 2.3 Phân rã thị phần theo phân khúc

Thường nhiều insight nằm ở đây hơn là thị phần tổng:

```python
def market_share_by_segment(dltt, scope_b2c=True):
    """
    Trả về pivot: rows=phan_khuc, cols=TH, values=thi_phan_pct trong phân khúc
    """
    df = filter_b2c(dltt) if scope_b2c else dltt.copy()
    pivot = (df.groupby(['phan_khuc', 'TH']).size()
               .reset_index(name='count'))
    total_per_segment = df.groupby('phan_khuc').size().to_dict()
    pivot['share_in_segment_pct'] = pivot.apply(
        lambda r: r['count'] / total_per_segment[r['phan_khuc']] * 100,
        axis=1
    )
    return pivot.pivot(index='phan_khuc', columns='TH',
                       values='share_in_segment_pct').fillna(0)
```

### 2.4 Top model trong phân khúc (insight cụ thể)

```python
def top_models_in_segment(dltt, segment, top_n=5, scope_b2c=True):
    df = filter_b2c(dltt) if scope_b2c else dltt.copy()
    df_seg = df[df['phan_khuc'] == segment]
    return (df_seg.groupby(['TH', 'model']).size()
                  .reset_index(name='dltt_count')
                  .sort_values('dltt_count', ascending=False)
                  .head(top_n))
```

---

## 3. Share of Dealer (PGS chiếm bao nhiêu của 1 TH)

### 3.1 Công thức

```
Share of dealer (PGS, TH X) = Doanh số PGS bán xe TH X / Tổng DLTT TH X trên địa bàn × 100%
```

**Lưu ý:** Mẫu số là **DLTT** (toàn bộ xe TH X được đăng ký trong địa bàn) chứ **không** phải tổng doanh số bán xe TH X. Vì có thể KH địa bàn này mua ở đại lý địa bàn khác — vẫn đăng ký ở đây.

### 3.2 Code Python

```python
def share_of_dealer(dltt, sales_pgs, dia_ban, ky_start, ky_end, scope_b2c=True):
    """
    Trả về: TH | dltt_TH_dia_ban | sales_PGS_TH | share_of_dealer_pct
    """
    # Lọc DLTT theo địa bàn + kỳ
    dltt_f = filter_b2c(dltt) if scope_b2c else dltt.copy()
    dltt_f = dltt_f[
        (dltt_f['tinh'] == dia_ban) &
        (dltt_f['ngay_dang_ky'].between(ky_start, ky_end))
    ]

    # Lọc sales PGS theo kỳ
    sales_f = filter_b2c(sales_pgs) if scope_b2c else sales_pgs.copy()
    sales_f = sales_f[sales_f['ngay_HD'].between(ky_start, ky_end)]

    # Group
    dltt_count = dltt_f.groupby('TH').size().reset_index(name='dltt_TH_dia_ban')
    sales_count = sales_f.groupby('TH').size().reset_index(name='sales_PGS_TH')

    result = dltt_count.merge(sales_count, on='TH', how='left').fillna(0)
    result['share_of_dealer_pct'] = (
        result['sales_PGS_TH'] / result['dltt_TH_dia_ban'] * 100
    )
    return result

# Sanity (Hook H4):
# Share of dealer cao bất thường (>100%) thường do KH mua ở PGS nhưng đăng ký
# ở tỉnh khác, hoặc do xe fleet/taxi → loại khỏi dltt cũng nên loại khỏi sales.
```

### 3.3 So sánh share of dealer với benchmark hệ thống

```python
def compare_share_with_benchmark(share_pgs_df, benchmark_pct):
    """
    benchmark_pct: dict {TH: % share trung bình hệ thống đại lý cùng TH}
    Vd: {'Toyota': 82, 'Hyundai': 78}
    """
    share_pgs_df['benchmark_pct'] = share_pgs_df['TH'].map(benchmark_pct)
    share_pgs_df['delta_vs_benchmark'] = (
        share_pgs_df['share_of_dealer_pct'] - share_pgs_df['benchmark_pct']
    )
    share_pgs_df['flag'] = share_pgs_df['delta_vs_benchmark'].apply(
        lambda d: 'underperform' if d < -3
        else 'overperform' if d > 3
        else 'on_track'
    )
    return share_pgs_df
```

---

## 4. YoY (Year-over-Year) & MoM (Month-over-Month)

### 4.1 Công thức

```
YoY = (Kỳ hiện tại - Cùng kỳ năm trước) / Cùng kỳ năm trước × 100%
MoM = (Tháng này - Tháng trước) / Tháng trước × 100%
QoQ = (Quý này - Quý trước) / Quý trước × 100%
YTD = Cộng dồn từ đầu năm đến nay
```

### 4.2 Code Python

```python
from dateutil.relativedelta import relativedelta

def yoy_mom(df, value_col, date_col, current_period_start, current_period_end):
    """
    Tính YoY và MoM cho 1 metric.
    df: dữ liệu lịch sử dài (≥ 13 tháng)
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    # Kỳ hiện tại
    cur = df[df[date_col].between(current_period_start, current_period_end)][value_col].sum()

    # Cùng kỳ năm trước
    yoy_start = current_period_start - relativedelta(years=1)
    yoy_end = current_period_end - relativedelta(years=1)
    yoy_val = df[df[date_col].between(yoy_start, yoy_end)][value_col].sum()

    # Tháng trước
    mom_start = current_period_start - relativedelta(months=1)
    mom_end = current_period_end - relativedelta(months=1)
    mom_val = df[df[date_col].between(mom_start, mom_end)][value_col].sum()

    yoy = (cur - yoy_val) / yoy_val * 100 if yoy_val else None
    mom = (cur - mom_val) / mom_val * 100 if mom_val else None
    return {'cur': cur, 'yoy_val': yoy_val, 'yoy_pct': yoy,
            'mom_val': mom_val, 'mom_pct': mom}
```

### 4.3 Sanity check YoY/MoM

YoY/MoM trong khoảng `[-90%, +500%]` là chấp nhận được. Vượt khoảng:

| Tình huống | Nguyên nhân thường |
|---|---|
| YoY > +500% | Cùng kỳ năm trước rất nhỏ (vd dịch Covid, mới ra mắt model) — nên ghi chú |
| YoY < -90% | Có sự kiện đặc biệt (đóng cửa, thu hồi, Covid) — cần verify |
| MoM dao động ±50% liên tục | Dữ liệu nhiễu hoặc theo mùa — nên smoothing |

```python
def validate_growth(growth_pct, kpi_name):
    if growth_pct is None:
        return ('INFO', f'{kpi_name}: kỳ trước không có dữ liệu, không tính được')
    if growth_pct > 500:
        return ('WARN', f'{kpi_name} {growth_pct:+.1f}% — kỳ trước quá nhỏ?')
    if growth_pct < -90:
        return ('WARN', f'{kpi_name} {growth_pct:+.1f}% — sự kiện bất thường?')
    return ('OK', f'{kpi_name} {growth_pct:+.1f}%')
```

### 4.4 Mẹo trình bày YoY/MoM

| Cách viết | Khi nào |
|---|---|
| "Tăng 12% YoY (T4/2026 vs T4/2025)" | Trường hợp chuẩn |
| "Tăng 12% YoY (78 → 87 xe)" | Khi mẫu nhỏ, ghi cả số tuyệt đối |
| "Giảm 8% YoY do hết phiên bản trước Vios facelift T6/2025" | Có context giải thích |
| "Không so sánh được YoY (T4/2025 chưa phát sinh dữ liệu)" | Khi dealer mới mở |

---

## 5. Phân rã CAGR (cho phân tích nhiều năm)

```
CAGR = (Giá trị cuối / Giá trị đầu)^(1/n) - 1
```

Dùng khi user hỏi: "Tăng trưởng trung bình 3 năm qua?"

```python
def cagr(value_start, value_end, n_years):
    if value_start <= 0 or n_years <= 0:
        return None
    return (value_end / value_start) ** (1/n_years) - 1

# Vd: doanh số 2022=850, 2025=1240
# cagr(850, 1240, 3) = 0.135 → 13.5%/năm
```

---

## 6. Phân tích cộng-trừ (decomposition)

Khi doanh số PGS giảm, cần biết: do **TH suy giảm** hay do **PGS thua đối thủ cùng TH**.

```python
def decompose_sales_change(prev_sales, cur_sales, prev_dltt, cur_dltt):
    """
    Phân rã: ΔSales_PGS = (Δ Thị_phần_TH) × Share_PGS + TH_total × (Δ Share_PGS)
    """
    prev_share_PGS = prev_sales / prev_dltt
    cur_share_PGS = cur_sales / cur_dltt

    # Thành phần do thị trường (TH tổng)
    market_effect = (cur_dltt - prev_dltt) * prev_share_PGS

    # Thành phần do dealer (PGS lấy thêm/mất share)
    dealer_effect = cur_dltt * (cur_share_PGS - prev_share_PGS)

    return {
        'total_change': cur_sales - prev_sales,
        'market_effect': market_effect,
        'dealer_effect': dealer_effect,
        'interpret': 'Phần lớn do market' if abs(market_effect) > abs(dealer_effect)
                     else 'Phần lớn do dealer'
    }

# Vd:
# T3: PGS bán 80 Toyota; DLTT Toyota 400 → share PGS = 20%
# T4: PGS bán 65 Toyota; DLTT Toyota 360 → share PGS = 18%
# Total change: -15
# Market effect: (360-400) × 0.20 = -8  (TH suy giảm khiến mất 8 xe)
# Dealer effect: 360 × (0.18 - 0.20) = -7.2 (PGS mất share thêm 7 xe)
# → "Khoảng 53% là do market, 47% là do mất share — cần action cả 2 mặt"
```

Đây là kiểu insight `market-analyzer` nên đưa vào output để `plan-builder`
biết phân nhóm GP nào (Sản phẩm/giá vs Marketing).

---

## 7. Pipeline doanh số dự báo (cho phần 5 báo cáo)

```python
def forecast_HD(funnel_now, conv_rates_history):
    """
    funnel_now: {'cold': 142, 'warm': 87, 'hot': 41}
    conv_rates_history: {'cold_to_HD': 0.20, 'warm_to_HD': 0.32, 'hot_to_HD': 0.68}
    """
    HD_7d = funnel_now['hot'] * conv_rates_history['hot_to_HD']
    HD_14d = (
        funnel_now['hot'] * conv_rates_history['hot_to_HD'] +
        funnel_now['warm'] * conv_rates_history['warm_to_HD'] * 0.5  # 50% kịp warm→HD trong 14d
    )
    HD_30d = (
        funnel_now['hot'] * conv_rates_history['hot_to_HD'] +
        funnel_now['warm'] * conv_rates_history['warm_to_HD'] +
        funnel_now['cold'] * conv_rates_history['cold_to_HD'] * 0.4
    )
    return {'7d': round(HD_7d), '14d': round(HD_14d), '30d': round(HD_30d)}
```

Cảnh báo: nếu lịch sử < 100 HĐ → khoảng tin cậy rộng, ghi rõ "ước lượng tham khảo".

---

## 8. Bảng tổng hợp công thức (quick reference)

| Chỉ số | Công thức | Mẫu tối thiểu | Khoảng hợp lý |
|---|---|---|---|
| Thị phần TH | DLTT_TH / Tổng_DLTT | 30 | 0-100% |
| Share of dealer | Sales_PGS_TH / DLTT_TH_dia_ban | 30 | 0-100% (typically 60-95) |
| YoY | (cur - yoy)/yoy × 100% | — | -90% → +500% |
| MoM | (cur - prev)/prev × 100% | — | -50% → +200% |
| CAGR | (end/start)^(1/n) - 1 | n≥2 | -0.30 → +0.50 |
| Cold→HĐ | n_HĐ / n_cold | 30 | 0-100% (typically 15-30) |
| Warm→HĐ | n_HĐ / n_warm | 30 | 0-100% (typically 30-50) |
| Hot→HĐ | n_HĐ / n_hot | 30 | 0-100% (typically 60-80) |
