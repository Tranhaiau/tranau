# Reference 04 — Action Playbook Xưởng (12 tình huống & GP mẫu)

> **Khi nào load:** Sub-agent xuất GP cần map insight → tình huống mẫu.
> Đây là "thư viện tình huống xưởng" — gặp pattern X → có sẵn template GP Y.

---

## 1. Cấu trúc playbook

```yaml
ma_tinh_huong: "TH-S01"
trigger:                    # khi nào pattern xuất hiện
nguyen_nhan_thuong_gap:     # 3-5 nguyên nhân
giai_phap_mau:              # GP với chủ thể/KPI/hạn
do_thanh_cong_du_kien:      # KPI kỳ vọng
cho_phep_dung_ngay:         # checklist immediate
```

---

## 2. Nhóm S — KPI Xưởng tổng

### TH-S01: Doanh thu xưởng giảm > 10% MoM

**Trigger:** Tổng doanh thu xưởng MoM ≤ -10%.

**Nguyên nhân thường gặp:**
1. Số RO giảm (UIO im ắng, capture rate thấp).
2. DT/RO giảm (KH chỉ làm BDĐK cơ bản, không upsell).
3. Số ngày làm việc trong tháng ít hơn (T2 28 ngày, lễ tết).
4. Phụ tùng thiếu hàng → không bán được PT.
5. Mất KH lớn (taxi/fleet) → giảm volume.

**Giải pháp mẫu:**

```yaml
- van_de: "DT xưởng T4=4.2 tỷ vs T3=4.85 tỷ (-13.4% MoM)"
  giai_phap: "Phân rã nguyên nhân: (a) n_RO giảm 8% (T4 ngắn), (b) DT/RO giảm 6% (PT/RO -12%); Hành động: (1) Audit kho phụ tùng top 20 PT bán chạy có thiếu hàng không; (2) Brief CVDV tăng cường upsell PT phụ trợ trong T5; (3) Xuất danh sách 200 VIN sắp đến BDĐK 30 ngày tới gọi nhắc"
  chu_the: "Trưởng xưởng + Trưởng kho PT + 4 CVDV"
  kpi: "DT xưởng T5 ≥ 4.6 tỷ; PT/RO ≥ 3.5tr; UIO recall ≥ 80 RO mới"
  han: "31/05/2026"
  ngay_review: "T+7 (12/05), T+30 (05/06)"
  nhom: "Doanh thu + Quy trình"
  bang_chung_so_lieu: ["DT T4=4.2 tỷ, T3=4.85 tỷ, n_RO T4=748 vs T3=812"]
```

---

### TH-S02: Capture rate < 60%

**Trigger:** Capture rate (12 tháng) < 60%.

**Nguyên nhân:**
1. UIO im ắng quá nhiều (KH chuyển xưởng khác hoặc bỏ xe lâu).
2. Không có chiến dịch gọi lại định kỳ.
3. CVDV chưa gọi proactive trước BDĐK.
4. Đối thủ gần (đại lý cùng TH khác) cạnh tranh giá phụ tùng.

**Giải pháp mẫu:**

```yaml
- van_de: "Capture rate 12 tháng = 54% (n_uio_active=2840, n_silent=1306)"
  giai_phap: "(1) Sub-agent vin-recaller xuất danh sách 1306 VIN im ắng theo độ ưu tiên (xe < 5 năm tuổi trước); (2) Phân lô 200 VIN/tuần cho 4 CVDV gọi nhắc; (3) Combo ưu đãi 'BDĐK trở lại' giảm 10% công lao động"
  chu_the: "Trưởng phòng dịch vụ + 4 CVDV + Marketing"
  kpi: "≥ 80 VIN/tháng quay lại xưởng; capture rate +3 điểm % trong T5"
  han: "30/06/2026"
  ngay_review: "T+14 (audit gọi), T+30 (đo VIN quay lại)"
  nhom: "Recall + Marketing"
  handoff_internal: "vin-recaller xuất file goi_lai_vin.xlsx"
```

---

### TH-S03: Comeback rate > 8%

**Trigger:** Comeback rate kỳ ≥ 8%.

**Nguyên nhân:**
1. Kỹ thuật KTV yếu (tập trung vào 1-2 KTV cụ thể).
2. Không có quality check trước bàn giao.
3. Phụ tùng kém chất lượng (PT lô hàng cụ thể).
4. Chẩn đoán sai bệnh ban đầu.

**Giải pháp mẫu:**

```yaml
- van_de: "Comeback rate T4 = 9.2% (76/827 RO), T3 = 5.1% — tăng đột biến"
  giai_phap: "(1) Diagnose theo KTV: KTV001 chiếm 45% comeback; (2) Module training quy_trinh_chan_doan + quality_check cho tổ KTV; (3) Bắt buộc check-list trước bàn giao mọi RO SC; (4) Audit lô PT bán cuối T3 có lỗi không"
  chu_the: "Trưởng xưởng + Tổ trưởng KTV + Trưởng kho PT"
  kpi: "Comeback rate T5 ≤ 5.5%; KTV001 comeback ≤ team avg trong T5"
  han: "31/05/2026"
  ngay_review: "T+14 (mid), T+30 (đo)"
  nhom: "Chất lượng + Đào tạo"
  handoff: "pgs-training-management — module quy_trinh_chan_doan + quality_check"
  bang_chung_RO: ["RO20260403-...", "RO20260415-...", "..."]   # bắt buộc cho Training (Hook H6)
```

---

### TH-S04: FTF rate < 85%

**Trigger:** FTF rate kỳ < 85%.

**Giải pháp:** Tương tự TH-S03 nhưng tập trung vào FTF failure analysis (xem `03-csi-and-service-metrics.md` mục 2.3) → mapping module training tương ứng.

---

### TH-S05: Hiệu suất khoang > 95% (quá tải)

**Trigger:** Capacity utilization > 95% kéo dài 4 tuần.

**Nguyên nhân:**
1. Volume tăng (tốt) nhưng không tăng năng lực kịp.
2. KTV chậm (nhóm `cham_va_thap`) → mỗi RO tốn nhiều giờ.
3. KH dồn vào ngày cuối tuần (lệch tải).

**Giải pháp mẫu:**

```yaml
- van_de: "Hiệu suất khoang T4 = 97% (capacity 1280h, used 1242h); KH chờ TB 4.5 ngày"
  giai_phap: "(1) Mở thêm ca chiều T5 (16h-20h) cho 8 khoang; (2) Đẩy mạnh đặt hẹn để cân tải tuần (T2-T5 còn trống nhưng T7-CN đầy); (3) Training thoi_gian_chuan_BDĐK cho 3 KTV chậm; (4) Tuyển thêm 2 KTV level 2"
  chu_the: "Trưởng xưởng + HR + Tổ trưởng KTV"
  kpi: "Hiệu suất khoang T5 ≤ 88%; thời gian chờ trung bình ≤ 2 ngày; tỷ lệ hen_truoc ≥ 60%"
  han: "30/06/2026"
  ngay_review: "T+14, T+30"
  nhom: "Năng lực + Quy trình"
```

---

### TH-S06: Hiệu suất khoang < 50% (thừa năng lực)

**Trigger:** Capacity utilization < 50% kéo dài.

**Nguyên nhân:** UIO im ắng + capture rate thấp + không marketing.

**Giải pháp:** Như TH-S02 + chiến dịch marketing dịch vụ phổ biến (vệ sinh khoang máy, dán phim, lắp phụ kiện).

---

## 3. Nhóm K — KTV cá nhân

### TH-K01: KTV pattern `chat_luong_kem` (FTF yếu + comeback cao)

**Trigger:** KTV có FTF < 70% TB team **và** comeback > 1.5× TB team, mẫu ≥ 30 RO.

**Giải pháp mẫu:**

```yaml
- van_de: "KTV001 (Phạm Văn A, L3): FTF 0.71 vs team 0.92, comeback 11% vs team 4%, mẫu 38 RO"
  giai_phap: "(1) Module training: quy_trinh_chan_doan + quality_check + sua_dung_lan_dau (3 module nối tiếp); (2) Kèm cặp 4 tuần bởi KTV017 (L5 chuyên gia); (3) Mọi RO SC của KTV001 phải có quality check chéo bởi KTV khác trước bàn giao trong 8 tuần"
  chu_the: "Tổ trưởng KTV + KTV017 + KTV001"
  kpi: "KTV001 FTF ≥ 0.85, comeback ≤ 6% trong T5+T6 (đo trên ≥ 30 RO mới)"
  han: "30/06/2026 (training), 31/07/2026 (đo KPI)"
  ngay_review: "T+14, T+30, T+60"
  nhom: "Đào tạo + Chất lượng"
  handoff: "pgs-training-management"
  baseline: {ftf_rate: 0.71, comeback_rate: 0.11, n_RO_baseline: 38}
  bang_chung_RO: ["RO20260403-A1", "RO20260408-B5", "..."]
```

---

### TH-K02: KTV pattern `cham_va_thap` (chậm + DT/RO thấp)

**Trigger:** giờ/RO > 1.5× TB team **và** DT/RO < 70% TB team.

**Giải pháp:** Module `thoi_gian_chuan_BDĐK` + `su_dung_dung_cu`.

---

### TH-K03: KTV mới (< 3 tháng) chưa quen quy trình

**Trigger:** KTV mới nhận việc < 90 ngày, có ≥ 1 dấu hiệu yếu.

**Đặc biệt:** Không xếp pattern, mở training onboarding chuẩn.

```yaml
- van_de: "KTV029 (Trần Văn D) mới vào 45 ngày, level 1, FTF chưa ổn định"
  giai_phap: "Bắt buộc onboarding 60 ngày: (1) 4 tuần làm phụ KTV017; (2) Module training onboarding_KTV_L1 (5 buổi); (3) Đánh giá thăng cấp L2 sau 90 ngày bởi Sub-Agent C"
  chu_the: "Tổ trưởng KTV + KTV017 + KTV029"
  kpi: "Hoàn thành 5 module onboarding; pass đánh giá L2 sau 90 ngày"
  han: "30/06/2026"
  ngay_review: "T+30, T+60, T+90"
  nhom: "Onboarding"
  handoff: "pgs-training-management — onboarding_KTV_L1"
```

---

## 4. Nhóm V — CVDV

### TH-V01: CVDV upsell yếu (PT/RO thấp)

**Trigger:** PT/RO < 85% TB team, mẫu ≥ 30 RO.

**Giải pháp mẫu:**

```yaml
- van_de: "CVDV003 PT/RO 1.85tr vs team 2.65tr (mẫu 42 RO)"
  giai_phap: "(1) Module training ky_nang_tu_van_phu_tung + phan_tich_lich_su_xe; (2) Cung cấp script tư vấn PT theo loại RO; (3) Daily standup review 5 RO sắp tới có cơ hội upsell"
  chu_the: "Trưởng phòng dịch vụ + CVDV003"
  kpi: "PT/RO ≥ 2.4tr trong T5 (mẫu ≥ 30 RO)"
  han: "31/05/2026"
  ngay_review: "T+14, T+30"
  nhom: "Đào tạo"
  handoff: "pgs-training-management"
```

---

### TH-V02: CVDV upsell `ép KH` (PT/RO cao + CSI thấp)

**Trigger:** PT/RO > 1.10× TB **và** CSI < 95% TB team.

**Đặc biệt:** Đây là vấn đề đạo đức nghề nghiệp, không phải kỹ năng.

```yaml
- van_de: "CVDV004 PT/RO 3.85tr (1.45× team) nhưng CSI 4.05 (vs team 4.42), điểm chạm 'gia' và 'tu_van' đều thấp"
  giai_phap: "(1) Module training dao_duc_nghe_nghiep + ky_nang_giao_tiep_KH; (2) Audit ngẫu nhiên 5 RO/tuần của CVDV004 — kiểm tra PT bán có cần thiết không; (3) Trao đổi 1-1 nghiêm túc với Trưởng phòng"
  chu_the: "Trưởng phòng dịch vụ + CVDV004"
  kpi: "CSI CVDV004 ≥ 4.30 trong T5; PT/RO về vùng 1.0-1.2× team"
  han: "30/06/2026"
  ngay_review: "T+14, T+30, T+60 (sustained)"
  nhom: "Đào tạo + Đạo đức nghề"
  handoff: "pgs-training-management"
```

---

### TH-V03: No-show rate cao do CVDV không xác nhận

**Trigger:** CVDV cụ thể có tỷ lệ no-show > 25% trong các hẹn họ phụ trách.

**Giải pháp:** Quy trình bắt buộc xác nhận lại hẹn T-1 ngày + T-2 giờ qua Zalo OA.

---

## 5. Nhóm C — CSI / Phản hồi

### TH-C01: CSI điểm chạm `thoi_gian_cho` < 4.0

**Trigger:** Điểm chạm `thoi_gian_cho` TB < 4.0 thang 1-5.

**Nguyên nhân:**
1. Hiệu suất khoang > 90% (quá tải).
2. Lead time PT thiếu hàng → chờ đặt.
3. KTV chậm.
4. Không thông báo trước với KH về thời gian dự kiến.

**Giải pháp:** Theo nguyên nhân cụ thể → điều phối tải hoặc training KTV hoặc cải thiện kho.

---

### TH-C02: CSI điểm chạm `gia` < 4.0

**Trigger:** Điểm chạm `gia` TB < 4.0.

**Nguyên nhân:**
1. CVDV không giải thích rõ chi phí trước khi sửa → KH bất ngờ với hoá đơn.
2. PT quá đắt vs đối thủ (xưởng dã chiến / đại lý hệ thống cùng TH).
3. CVDV upsell ép.

**Giải pháp:**

```yaml
- van_de: "Điểm chạm 'gia' T4 = 3.85 (gap 0.57 vs CSI tổng 4.42), text feedback 'giá cao' xuất hiện 15 lần"
  giai_phap: "(1) Bắt buộc CVDV gửi quote trước khi sửa cho mọi RO > 1tr; (2) So sánh giá PT top 20 PT bán chạy với 3 đại lý cạnh tranh; (3) Module training dao_duc_nghe_nghiep cho CVDV004 (theo TH-V02)"
  chu_the: "Trưởng phòng dịch vụ + 4 CVDV + Marketing"
  kpi: "Điểm chạm 'gia' ≥ 4.20 trong T5; phản hồi 'giá cao' ≤ 5 lần"
  han: "31/05/2026"
  ngay_review: "T+14, T+30"
  nhom: "Quy trình + Đào tạo"
```

---

### TH-C03: CSI giảm > 0.3 thang 1-5 trong 1 kỳ

**Trigger:** CSI tổng giảm ≥ 0.3 vs kỳ trước.

**Đặc biệt:** Escalate ngay cho GĐ ĐL trước khi đợi báo cáo định kỳ.

---

## 6. Nhóm B — BDĐK / KH cũ

### TH-B01: Tỷ lệ BDĐK 1k < 70%

**Trigger:** BDĐK 1k đúng hạn < 70% (mẫu ≥ 20 VIN đủ điều kiện).

**Nguyên nhân:**
1. Sales bàn giao xe không nhắc về BDĐK 1k.
2. Service không có chiến dịch nhắc nhở chủ động.
3. KH gần xưởng đối thủ → tiện đường đi.

**Giải pháp:**

```yaml
- van_de: "BDĐK 1k T4 đúng hạn 62% (n=24 VIN đủ điều kiện)"
  giai_phap: "(1) Sales bàn giao xe phải đặt hẹn BDĐK 1k tại quầy; (2) CVDV gọi nhắc T-7 ngày trước mốc 1k; (3) Coupon BDĐK 1k miễn phí 30% cho 50 KH đầu T5"
  chu_the: "Trưởng phòng kinh doanh + Trưởng phòng dịch vụ + 4 CVDV"
  kpi: "BDĐK 1k T5 ≥ 80% đúng hạn"
  han: "31/05/2026"
  ngay_review: "T+30"
  nhom: "Quy trình + Marketing (cross-skill Sales↔Service)"
  handoff_cross_skill: "pgs-sales-analytics — yêu cầu sales bàn giao xe set hẹn BDĐK 1k tại quầy"
```

---

### TH-B02: KH cũ không quay lại > 12 tháng

**Trigger:** > 30% UIO active im ắng > 12 tháng.

**Giải pháp:** Sub-agent `vin-recaller` xuất file gọi lại theo độ ưu tiên (xe trẻ + giá trị cao trước).

---

## 7. Bảng tra nhanh: Pattern → Tình huống

| Pattern phát hiện | Tình huống playbook |
|---|---|
| DT xưởng giảm MoM | TH-S01 |
| Capture rate thấp | TH-S02 |
| Comeback rate cao | TH-S03 |
| FTF rate thấp | TH-S04 |
| Quá tải khoang | TH-S05 |
| Thừa năng lực | TH-S06 |
| KTV chất lượng kém | TH-K01 |
| KTV chậm + DT thấp | TH-K02 |
| KTV mới onboarding | TH-K03 |
| CVDV upsell yếu | TH-V01 |
| CVDV upsell ép | TH-V02 |
| No-show CVDV cao | TH-V03 |
| Điểm chạm thời gian thấp | TH-C01 |
| Điểm chạm giá thấp | TH-C02 |
| CSI giảm đột biến | TH-C03 |
| BDĐK 1k thấp | TH-B01 |
| KH cũ im ắng | TH-B02 |

---

## 8. Quy tắc bất biến

1. **Mỗi GP phải có đủ 5 trường schema** (van_de, giai_phap, chu_the, kpi, han) — Hook H5.
2. **Handoff sang Training PHẢI kèm `bang_chung_RO`** — Hook H6.
3. **Mọi GP có cá nhân chỉ định phải có baseline KPI** — để T+30 đo được.
4. **GP không đề xuất sa thải/kỷ luật** — vượt quyền skill.
5. **GP cross-skill (handoff Sales/Training) phải qua main agent** — sub không gọi sub khác.
6. **GP về CVDV "upsell ép" phải có audit thực tế** — không chỉ training là đủ.
7. **GP về KTV mới chỉ áp dụng nếu có ≥ 1 dấu hiệu yếu** — không "training cho có".

---

## 9. Edge cases

| Tình huống | Cách xử lý |
|---|---|
| Pattern xuất hiện nhưng mẫu < 30 | Theo dõi 1 kỳ nữa, không xuất GP cá nhân |
| Cùng KTV vừa pattern `chat_luong_kem` vừa mới onboarding | Áp dụng TH-K03 (onboarding) trước, ưu tiên thời gian |
| Có nhiều KTV cùng pattern | Training group thay vì cá nhân, hiệu quả hơn |
| GP triển khai từ kỳ trước chưa xong | Không xuất GP mới cùng nội dung, chỉ refresh KPI và ngày review |
| Hãng yêu cầu campaign riêng | Tách thành GP có nguồn = "hãng", không lẫn với GP nội bộ |
| KTV bị tai nạn / nghỉ ốm dài | Loại khỏi diagnose pattern, ghi nhận tạm dừng |
