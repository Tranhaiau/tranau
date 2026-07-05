# Reference 06 — Action Playbook (Tình huống & Giải pháp Mẫu)

> **Khi nào load:** Sub-agent `plan-builder` cần map insight thành GP cụ thể.
> Đây là "thư viện tình huống" — gặp pattern X → có sẵn template GP Y với KPI/hạn/chủ thể.

---

## 1. Cấu trúc playbook

Mỗi tình huống được mô tả theo schema:

```yaml
ma_tinh_huong: "TH-001"
trigger:                    # khi nào pattern xuất hiện
nguyen_nhan_thuong_gap:     # 3-5 nguyên nhân chính
giai_phap_mau:              # 2-3 GP với chủ thể/KPI/hạn
do_thanh_cong_du_kien:      # KPI kỳ vọng + bằng chứng cần
cho_phep_dung_ngay:         # checklist immediate action
```

---

## 2. Nhóm A — Vấn đề Thị phần

### TH-A01: Thị phần TH suy giảm chung trên địa bàn

**Trigger:** YoY của TH X giảm ≥ 5 điểm % trên địa bàn 2 kỳ liên tiếp.

**Nguyên nhân thường gặp:**
1. Đối thủ ra model mới hấp dẫn (Custin, Xforce…)
2. TH X không có model trong phân khúc đang nóng
3. Giá TH X cao hơn đối thủ trực tiếp ≥ 10%
4. Yếu tố vĩ mô (đăng kiểm, thuế, lãi suất)

**Giải pháp mẫu:**

```yaml
- van_de: "Thị phần Toyota giảm 6 điểm % YoY (T3-T4/2026)"
  giai_phap: "Đề xuất hãng tăng KM đặc biệt cho 2 model bị cạnh tranh + tổ chức 4 sự kiện cộng đồng tại 4 cụm KCN trọng điểm"
  chu_the: "GĐ ĐL + Phòng MKT + Hãng (qua kênh ĐL → vùng → trụ sở)"
  kpi: "Thị phần Toyota +3 điểm % trong T5/2026; ≥ 200 KHTN B-SUV mới từ sự kiện"
  han: "30/06/2026"
  ngay_review: "20/05/2026 + 15/06/2026"
  nhom: "Marketing/Sự kiện + Sản phẩm/giá"
  bang_chung_so_lieu: ["DLTT Toyota T3=410, T4=345 (-15.9%)"]
```

**Cho phép dừng ngay:** Nếu đã đề xuất hãng nhưng chưa được duyệt KM, vẫn triển khai sự kiện.

---

### TH-A02: Phân khúc nào đó tăng share đột biến — PGS bỏ lỡ

**Trigger:** Phân khúc X có DLTT tăng > 20% nhưng PGS share < 25% (trong khi TB hệ thống PGS các đại lý khác > 60%).

**Nguyên nhân:**
1. PGS chưa truyền thông đủ về model mới trong phân khúc đó.
2. TVBH chưa được training về model trong phân khúc đó.
3. Không có sản phẩm/version phù hợp (chưa nhập về).

**Giải pháp mẫu:**

```yaml
- van_de: "DLTT phân khúc B-SUV địa bàn tăng 28% YoY; PGS chỉ chiếm 18%"
  giai_phap: "Combo 3 hành động: (1) Sự kiện lái thử Yaris Cross + Stargazer cuối tuần 2 cụm KCN Amata + Long Thành; (2) Training nhanh TVBH module B-SUV; (3) Banner home + landing page riêng"
  chu_the: "Trưởng phòng MKT + Trưởng phòng KD + 2 TVBH chuyên B-SUV"
  kpi: "≥ 80 KHTN B-SUV mới trong T5; ≥ 25 lượt lái thử; ≥ 6 HĐ trong 30 ngày sau sự kiện"
  han: "25/05/2026 (sự kiện) + 24/06/2026 (đo HĐ)"
  ngay_review: "01/06/2026"
  nhom: "Sự kiện + Đào tạo + Marketing"
  uoc_luong_tac_dong: "PGS share B-SUV 18% → 23% trong T5"
```

---

### TH-A03: Cụm trắng (white space) chưa khai thác

**Trigger:** Huyện có DLTT cao ≥ 30 nhưng PGS share < 25%.

**Giải pháp mẫu:**

```yaml
- van_de: "Huyện Long Thành: DLTT Toyota T4 = 47, PGS chỉ chốt 12 (share 25.5% vs benchmark 80%)"
  giai_phap: "Mở popup booth tại TTTM Aeon Long Thành 2 cuối tuần liên tiếp + chương trình 'Trade-in tại nhà' miễn phí"
  chu_the: "Phòng MKT + 2 TVBH (1 đi thường trực booth, 1 phụ trợ)"
  kpi: "≥ 40 KHTN từ Long Thành; ≥ 5 HĐ; PGS share Long Thành ≥ 35% T5"
  han: "31/05/2026"
  ngay_review: "12/05/2026 + 26/05/2026"
  nhom: "Sự kiện + Marketing"
```

---

## 3. Nhóm B — Vấn đề Phễu/TVBH

### TH-B01: TVBH yếu Cold→Warm

**Trigger:** TVBH có CR Cold→Warm < 70% TB team, mẫu ≥ 30 KHTN.

**Nguyên nhân:**
1. Kỹ năng khai thác nhu cầu yếu (chỉ "mời lái thử" không đào sâu).
2. Không follow-up đúng thời điểm.
3. Kỹ năng giao tiếp KH thô.

**Giải pháp mẫu:**

```yaml
- van_de: "TVBH NV001 (Nguyễn Văn A) có CR Cold→Warm 0.32 (TB team 0.61), mẫu 38 KHTN"
  giai_phap: "(1) Đào tạo lại module 'khai thác nhu cầu' (2 buổi); (2) Kèm cặp 4 tuần bởi NV017 (TVBH top); (3) Daily standup 15 phút review pipeline"
  chu_the: "Trưởng phòng KD: Trần Văn B + NV017 + NV001"
  kpi: "Cold→Warm ≥ 0.55 trong T5; tỷ lệ chốt overall ≥ 18%"
  han: "31/05/2026 (training) + 30/06/2026 (đo KPI thực)"
  ngay_review: "12/05/2026 (giữa kỳ) + 31/05/2026 (cuối training) + 30/06/2026 (sau 30d)"
  nhom: "Đào tạo"
  handoff: "pgs-training-management — module khai_thac_nhu_cau"
  baseline_de_so_sanh: {ty_le_chot: 0.08, cold_to_warm: 0.32}
```

---

### TH-B02: TVBH yếu Warm→Hot

**Trigger:** CR Warm→Hot < 70% TB team.

**Nguyên nhân:**
1. Kỹ năng xử lý từ chối yếu (KH so giá xong không quay lại).
2. Không tận dụng lái thử để chốt cọc.
3. Báo giá lỗi/không rõ → KH mất niềm tin.

**Giải pháp mẫu:** Module training "xu_ly_tu_choi" + "thuc_hien_lai_thu_chuyen_nghiep".

---

### TH-B03: TVBH yếu Hot→HĐ

**Trigger:** CR Hot→HĐ < 70% TB team (vd TB team 68%, TVBH 45%).

**Nguyên nhân:**
1. Kỹ năng chốt deal yếu — không tạo urgency.
2. Hỗ trợ thủ tục tài chính yếu — KH bị "tuột" ở khâu vay.
3. KH cọc rồi đối thủ chen ngang → không khoá.

**Giải pháp mẫu:**

```yaml
- van_de: "TVBH NV004 CR Hot→HĐ 0.45 vs TB team 0.68"
  giai_phap: "(1) Module training chot_deal + ho_tro_thu_tuc_tai_chinh; (2) Mỗi KH Hot phải có check-in mỗi 48h đến khi ký HĐ; (3) Trưởng phòng review từng case Hot > 7 ngày"
  chu_the: "Trưởng phòng KD + NV004"
  kpi: "Hot→HĐ ≥ 0.60 trong T5; thời gian Hot→HĐ TB ≤ 7 ngày"
  han: "30/06/2026"
  ngay_review: "T+15d, T+30d"
  nhom: "Đào tạo + Quy trình"
  handoff: "pgs-training-management"
```

---

### TH-B04: Nhiều TVBH yếu cùng pattern

**Trigger:** ≥ 30% team có cùng pattern (vd Cold→Warm yếu).

**Giải pháp:** Thay vì training cá nhân → tổ chức **Training group + workshop chung** hiệu quả hơn.

---

## 4. Nhóm C — Vấn đề Quy trình

### TH-C01: HĐ luồn ngoài quan_tri

**Trigger:** ≥ 5% HĐ trong sales_pgs không có ma_KHTN trong quan_tri.

**Giải pháp mẫu:**

```yaml
- van_de: "Phát hiện 3/28 HĐ T4 không có pipeline trong quan_tri (10.7%)"
  giai_phap: "(1) Ban hành thông báo siết quy trình: mọi HĐ phải có ma_KHTN trước ký; (2) Audit ngẫu nhiên 2 lần/tuần bởi Trưởng phòng KD; (3) KPI cá nhân TVBH gắn với % HĐ có pipeline đầy đủ"
  chu_the: "Trưởng phòng KD: Trần Văn B"
  kpi: "0 HĐ luồn trong T5; ≥ 95% HĐ có ma_KHTN trong quan_tri"
  han: "10/05/2026 (ban hành) + 31/05/2026 (audit lần 1)"
  ngay_review: "12/05/2026"
  nhom: "Quy trình"
```

---

### TH-C02: Pipeline đứng quá lâu (stale)

**Trigger:** ≥ 20% KHTN ở Cold/Warm > 90 ngày không cập nhật.

**Giải pháp mẫu:**

```yaml
- van_de: "47/142 KHTN active (33%) đứng > 90 ngày không cập nhật trạng thái"
  giai_phap: "(1) Mỗi T2 hàng tuần TVBH phải review pipeline > 30 ngày; (2) Tự động hoá nhắc nhở qua Cyber DMS; (3) KHTN > 120 ngày không có touchpoint → tự động chuyển 'Mất' với lý do 'kh không phản hồi'"
  chu_the: "Trưởng phòng KD + IT (cài rule auto)"
  kpi: "≤ 10% KHTN active đứng > 90 ngày trong T5"
  han: "20/05/2026"
  ngay_review: "31/05/2026"
  nhom: "Quy trình"
```

---

### TH-C03: TVBH không cập nhật ngày báo giá / lái thử

**Trigger:** Trong file quan_tri, > 30% bản ghi Warm thiếu cả `ngay_bao_gia` lẫn `ngay_lai_thu`.

**Giải pháp:** Bắt buộc trường, không cho lưu nếu thiếu (cài rule trong Cyber).

---

## 5. Nhóm D — Vấn đề Marketing/Lead

### TH-D01: Lead online conversion thấp

**Trigger:** CR online → HĐ < 50% CR walkin → HĐ.

**Nguyên nhân:**
1. Lead online chất lượng thấp (form spam, KH chỉ tò mò).
2. Thời gian phản hồi chậm > 10 phút.
3. TVBH không quen xử lý lead "lạnh" qua điện thoại.

**Giải pháp mẫu:**

```yaml
- van_de: "Lead online CR 7% vs walkin 22% (mẫu 148 lead online T4)"
  giai_phap: "(1) Chuyên môn hoá 1 TVBH chuyên xử lý lead online (NV019); (2) SLA phản hồi ≤ 5 phút giờ hành chính; (3) Quy trình nuôi dưỡng (nurture) tự động qua Zalo OA cho KH chưa convert sau 7 ngày"
  chu_the: "Trưởng phòng MKT + Trưởng phòng KD + NV019"
  kpi: "Lead online CR ≥ 12% trong T5; SLA phản hồi ≥ 90% trong 5 phút"
  han: "20/05/2026"
  ngay_review: "12/05/2026 + 26/05/2026"
  nhom: "Marketing + Quy trình"
```

---

### TH-D02: Pipeline cạn ở phân khúc cụ thể

**Trigger:** n KHTN mới trong phân khúc Y ≤ 50% TB lịch sử 6 tháng.

**Giải pháp:** Sự kiện chuyên đề + ngân sách ads tập trung phân khúc đó.

---

### TH-D03: Nguồn KHTN refer giảm

**Trigger:** Tỷ lệ nguồn `refer` trong tổng KHTN giảm > 30% so với cùng kỳ.

**Nguyên nhân:** KH cũ không hài lòng → ít giới thiệu. Kiểm tra CSI hậu mãi.

**Giải pháp:**
- Handoff sang `pgs-service-analytics` lấy CSI 3 tháng + tỷ lệ quay lại xưởng.
- Chương trình "Refer-a-friend" với incentive cụ thể.

---

## 6. Nhóm E — Vấn đề Sản phẩm/Giá

### TH-E01: Khách so giá đối thủ cùng phân khúc

**Trigger:** ≥ 25% lý do mất là `gia_cao` hoặc `doi_thu_KM_tot`.

**Giải pháp mẫu (KHÔNG đề xuất giảm giá vì giảm giá là quyết định hãng):**

```yaml
- van_de: "32% lý do mất là 'đối thủ KM tốt hơn' — chủ yếu Hyundai Custin tặng BHVC + 30tr T4"
  giai_phap: "(1) Đề xuất hãng tăng KM cho Innova Cross + Veloz; (2) Soạn TCO 5 năm so sánh + tài liệu cho TVBH; (3) Combo phụ kiện tặng kèm trị giá ~15tr (camera 360, thảm sàn, dán phim)"
  chu_the: "GĐ ĐL + Trưởng phòng KD + Phòng kế toán"
  kpi: "% mất do 'đối thủ KM' ≤ 18% trong T5"
  han: "15/05/2026"
  ngay_review: "31/05/2026"
  nhom: "Sản phẩm/giá + Marketing"
```

---

### TH-E02: Lead time giao xe quá lâu — KH bỏ

**Trigger:** ≥ 20% lý do mất là `cho_doi_qua_lau`.

**Giải pháp:**
- Đặt hàng dự báo tốt hơn (gắn với pipeline forecast).
- Trao đổi với chi nhánh khác trong hệ thống PGS để swap màu/version.
- Minh bạch lead time với KH ngay từ stage Warm (không hứa "có hàng" rồi chờ).

---

## 7. Nhóm F — Vấn đề Hậu mãi ảnh hưởng Bán

### TH-F01: KH cũ không refer + không quay lại

**Trigger:** Tỷ lệ KH cũ refer giảm + tỷ lệ KH cũ mua xe thứ 2/3 ở PGS giảm.

**Giải pháp:** Handoff sang `pgs-service-analytics` để diagnose CSI hậu mãi + UIO im ắng.

```yaml
- van_de: "Nguồn refer giảm 35% YoY; xe PGS bán ≥ 3 năm chưa quay lại xưởng 12 tháng = 287 VIN"
  giai_phap: "(1) Handoff Service: chiến dịch gọi lại 287 VIN; (2) Sales: gói 'Đổi xe đặc quyền KH PGS' với ưu đãi trade-in"
  chu_the: "Trưởng phòng Dịch vụ + Trưởng phòng KD"
  kpi: "≥ 80 VIN quay lại xưởng trong 60 ngày; ≥ 12 KH cũ chốt HĐ xe mới"
  han: "30/06/2026"
  ngay_review: "31/05/2026"
  nhom: "Hậu mãi (cross-skill)"
  handoff:
    - "pgs-service-analytics: vin-recaller cho 287 VIN"
    - (nội bộ sales): plan trade-in"
```

---

## 8. Quy tắc bất biến của playbook

1. **Mỗi GP phải có đủ Schema 5 trường** — Hook H5 enforce.
2. **GP phải neo về tình huống playbook** — không được "sáng tạo" GP không có trong playbook trừ khi có justification rõ.
3. **Chủ thể là người cụ thể (tên hoặc mã NS)** — không "Phòng KD" chung chung.
4. **KPI phải đo được** — có ngưỡng số.
5. **Hạn phải là ngày cụ thể** — không "trong tháng tới".
6. **Ngày review phải có** — để Hook H6 tạo scheduled task.
7. **Handoff sang skill khác phải kèm payload chuẩn** — xem `plugins.md`.
8. **Không đề xuất sa thải/kỷ luật** — vượt quyền skill.

---

## 9. Bảng tra nhanh: Pattern → Tình huống

| Pattern phát hiện | Tình huống playbook |
|---|---|
| Thị phần TH giảm chung | TH-A01 |
| Phân khúc bùng nổ — PGS bỏ lỡ | TH-A02 |
| White space ở huyện | TH-A03 |
| TVBH yếu Cold→Warm | TH-B01 |
| TVBH yếu Warm→Hot | TH-B02 |
| TVBH yếu Hot→HĐ | TH-B03 |
| Nhiều TVBH cùng yếu | TH-B04 |
| HĐ luồn ngoài quy trình | TH-C01 |
| Pipeline stale > 90 ngày | TH-C02 |
| TVBH không cập nhật trường bắt buộc | TH-C03 |
| Lead online CR thấp | TH-D01 |
| Pipeline cạn theo phân khúc | TH-D02 |
| Refer giảm | TH-D03 |
| Mất do giá / đối thủ KM | TH-E01 |
| Mất do lead time | TH-E02 |
| KH cũ không quay lại | TH-F01 |

→ Sub-agent `plan-builder` dùng bảng này để map pattern → template GP nhanh chóng.
