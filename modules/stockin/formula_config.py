"""
formula_config.py
=================
Konfigurasi dan penerapan rumus otomatis untuk sheet stok harian (01-31).

Untuk mengubah rumus:
  - Kolom J (fix per baris)  → edit J_FORMULAS
  - Kolom K, L, M (relative) → edit RELATIVE_FORMULAS / RELATIVE_ROW_START / RELATIVE_ROW_END
  - Rentang background J     → edit J_FILL_ROW_START / J_FILL_ROW_END
  - Kolom yang di-lock        → edit LOCKED_COLUMNS
  - Password proteksi         → edit SHEET_PASSWORD
"""

from openpyxl.styles import PatternFill, Protection
from openpyxl.cell.cell import MergedCell
from openpyxl.styles import PatternFill, Protection, Border, Side

# ─── KONFIGURASI ─────────────────────────────────────────────────────────────

# Password proteksi sheet
SHEET_PASSWORD = "12345678"

# ── Rentang lock & kuning per kelompok kolom ──────────────────────────────────
# A(1), B(2)          → baris 1–95   (semua sheet)
# D(4)                → baris 1–95   (sheet 02-31 saja; sheet 01 TIDAK dikunci/kuning)
# I(9),J(10),K(11),
#   L(12),M(13)       → baris 2–95   (semua sheet)
# O(15),P(16),Q(17)   → baris 2–120  (semua sheet, dengan border)
# S(19),T(20),U(21)   → baris 2–19   (semua sheet)
# W(23),X(24)         → baris 1–122  (semua sheet; 121-122 = summary)

AB_ROW_START    = 1;  AB_ROW_END    = 95
D_ROW_START     = 1;  D_ROW_END     = 95
IJKLM_ROW_START = 2;  IJKLM_ROW_END = 95
OPQ_ROW_START   = 1;  OPQ_ROW_END   = 120
STU_ROW_START   = 1;  STU_ROW_END   = 19
WX_ROW_START    = 1;  WX_ROW_END    = 122

# Alias agar kompatibel dengan import di processor.py
RELATIVE_ROW_START = IJKLM_ROW_START
RELATIVE_ROW_END   = IJKLM_ROW_END

# Rentang background kuning kolom J (sama dengan IJKLM)
J_FILL_ROW_START = IJKLM_ROW_START
J_FILL_ROW_END   = IJKLM_ROW_END

# Baris summary W/X
WX_SUMMARY_START = 121   # W121 = "Selisih Bersih", X121 = SUM
WX_DATA_END      = 120   # baris terakhir data produk (untuk range SUM)



# Warna & border
FORMULA_FILL   = PatternFill("solid", fgColor="FFE6E6FA")   # kuning
HEADER_IJKLM_FILL = PatternFill("solid", fgColor="FFE6E6FA")
HEADER_WX_FILL = PatternFill("solid", fgColor="FFE6E6FA")   # oranye header W/X baris 1
BORDER_THIN    = Side(border_style="thin", color="000000")
CELL_BORDER    = Border(left=BORDER_THIN, right=BORDER_THIN,
                        top=BORDER_THIN,  bottom=BORDER_THIN)


# ─── RUMUS FIX KOLOM J ───────────────────────────────────────────────────────
# Key   = nomor baris (sesuai posisi di Excel, tidak berubah antar sheet/file)
# Value = rumus Excel persis seperti di file asli
# Untuk mengubah rumus → ganti value-nya
# Untuk mengubah posisi → ganti key-nya
# Untuk menambah rumus  → tambah baris baru
# Baris yang tidak ada di sini akan di-skip (tidak ditulis rumus, tapi tetap kuning)

J_FORMULAS = {
    # =========================================================
    # BAHAN BAKU UTAMA
    # =========================================================

    2:  "=((Q8+Q9+Q10+Q11+Q14+Q15+Q16+Q17+Q18+Q19+Q49+Q50+Q51+Q52+Q53+Q61+Q63+Q64)*130)+((Q56+Q57+Q65+Q58)*100)+(Q66*150)",
    # Item   : Susu UHT
    # Satuan : ml per cup
    # Logika : Menu reguler pakai 130ml, beberapa menu pakai 100ml, Brown Sugar Boba Milk pakai 150ml
    # 130ml  : Taro, Taro L, Green Tea, Green Tea L, Choco Hazelnut, Choco Hazelnut L,
    #           Chocolate, Chocolate L, Bubble Gum, Bubble Gum L, Vanilla Oreo, Red Velvet Oreo,
    #           Red Velvet, Cotton Candy, Biscoff Milk, Ovaltine Cheese, Green Tea Cheese, Choco Cheese
    # 100ml  : Choco Ovaltine, Choco Milo, Brown Sugar Boba Milk Tea, Kopi Susu Goks
    # 150ml  : Brown Sugar Boba Milk

    3:  "=(U3/U2)*E40",
    # Item   : Teh Bubuk Chatramue
    # Logika : Proporsi pemakaian berdasarkan rasio batch (U3/U2) dikali stok awal E41

    4:  "=(U13/U12)*E42",
    # Item   : Tapioca Pearl
    # Logika : Proporsi pemakaian berdasarkan rasio batch (U13/U12) dikali stok awal E43

    5:  "=(U11/U10)*E38",
    # Item   : Kopi Robusta Kerinci
    # Logika : Proporsi pemakaian berdasarkan rasio batch (U11/U10) dikali stok awal E39

    6:  "=(Q2+Q3+Q4+Q5+Q8+Q9+Q10+Q11+Q16+Q17+Q18+Q19+Q49+Q50+Q51+Q52+Q53+Q54+Q55+Q61+Q63+Q64+Q65+Q66+Q6+Q7+Q60)*40",
    # Item   : Fructose Syrup
    # Satuan : ml per cup (40ml)
    # Logika : Semua menu minuman masing-masing pakai 40ml fructose syrup
    # Menu   : Lemon Tea, Lemon Tea L, Lychee Tea, Lychee Tea L, Thai Tea, Thai Tea L,
    #           Taro, Taro L, Chocolate, Chocolate L, Bubble Gum, Bubble Gum L,
    #           Vanilla Oreo, Red Velvet Oreo, Red Velvet, Cotton Candy, Biscoff Milk,
    #           Mango Yakult, Lychee Yakult, Ovaltine Cheese, Green Tea Cheese, Choco Cheese,
    #           Brown Sugar Boba Milk Tea, Brown Sugar Boba Milk, Thai Tea Cheese

    8:  "=(Q37+Q65+Q66)*10",
    # Item   : Gula Aren Cair
    # Satuan : ml per cup (10ml)
    # Menu   : Boba Sundae, Brown Sugar Boba Milk Tea, Brown Sugar Boba Milk

    9:  "=(Q12+Q13+Q60+Q6+Q7+Q59+Q62)*40",
    # Item   : Carnation (Susu Evaporasi)
    # Satuan : ml per cup (40ml)
    # Menu   : Es Permen Karet, Es Permen Karet L, Thai Tea Cheese,
    #           Thai Tea, Thai Tea L, Kopi Rakyat, Ovaltine Cheese

    10: "=(Q14+Q15)*20",
    # Item   : Hazelnut Syrup
    # Satuan : ml per cup (20ml)
    # Menu   : Chocolate Hazelnut, Chocolate Hazelnut Large

    11: "=Q2+Q4+Q6+Q8+Q10+Q12+Q14+Q16+Q18+Q54+Q55+Q58+Q59+Q79",
    # Item   : Small Cup - 14 Oz
    # Logika : Semua menu minuman ukuran reguler (non-Large) pakai cup 14 Oz
    # Menu   : Lemon Tea, Lychee Tea, Thai Tea, Taro, Green Tea, Es Permen Karet,
    #           Choco Hazelnut, Chocolate, Bubble Gum, Mango Yakult, Lychee Yakult,
    #           Kopi Susu Goks, Kopi Rakyat, Cup Take Away 14 OZ

    12: "=Q3+Q5+Q7+Q9+Q11+Q13+Q15+Q17+Q19+Q49+Q50+Q51+Q52+Q53+Q56+Q57+Q60+Q61+Q62+Q63+Q64+Q65+Q66",
    # Item   : Large Cup - 22 Oz
    # Logika : Semua menu minuman ukuran Large pakai cup 22 Oz
    # Menu   : Lemon Tea L, Lychee Tea L, Thai Tea L, Taro L, Green Tea L,
    #           Es Permen Karet L, Choco Hazelnut L, Chocolate L, Bubble Gum L,
    #           Vanilla Oreo, Red Velvet Oreo, Red Velvet, Cotton Candy, Biscoff Milk,
    #           Choco Ovaltine, Choco Milo, Thai Tea Cheese, Taro Cheese, Ovaltine Cheese,
    #           Green Tea Cheese, Choco Cheese, Brown Sugar Boba Milk Tea, Brown Sugar Boba Milk

    13: "=Q49+Q50+Q53",
    # Item   : Sedotan Besar
    # Logika : Menu dengan boba/pearl butuh sedotan besar
    # Menu   : Vanilla Oreo, Red Velvet Oreo, Biscoff Milk

    14: "=(SUM(Q2:Q19))+Q52+Q51+((SUM(Q54:Q66)))",
    # Item   : Sedotan Kecil
    # Logika : Semua menu minuman pakai sedotan kecil
    # Menu   : Seluruh menu minuman (Q2:Q19), Cotton Candy (Q52), Red Velvet (Q51),
    #           semua menu Q54:Q66 (Yakult, Kopi, Cheese, Boba Milk Tea, dll)

    17: "=(U5/U4)*E39",
    # Item   : Teh Bubuk Kayu Aro
    # Logika : Proporsi pemakaian berdasarkan rasio batch (U5/U4) dikali stok awal E40

    18: "=(U19/U18)*E44",
    # Item   : Teh vanilla
    # Logika : Proporsi pemakaian berdasarkan rasio batch (U5/U4) dikali stok awal E40

    19: "=(U19/U18)*E45",
    # Item   : Teh melati/jasmin
    # Logika : Proporsi pemakaian berdasarkan rasio batch (U5/U4) dikali stok awal E40

    20: "=(U17/U16)*E39",
    # Item   : Teh bendera
    # Logika : Proporsi pemakaian berdasarkan rasio batch (U5/U4) dikali stok awal E40

    #21: "=(Q2+Q3+Q4+Q5+Q8+Q9+Q10+Q11+Q16+Q17+Q18+Q19+Q49+Q50+Q51+Q52+Q53+Q54+Q55+Q61+Q63+Q64+Q65+Q66+Q6+Q7+Q60)*50",
    # Gula Pasir

    # =========================================================
    # POWDER
    # =========================================================

    22: "=(Q18+Q19)*30",
    # Item   : Bubble Gum Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Bubble Gum, Bubble Gum Large

    23: "=Q52*30",
    # Item   : Cotton Candy Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Cotton Candy

    24: "=(U9/U8)*E41",
    # Item   : Cream Cheese Powder
    # Logika : Proporsi pemakaian berdasarkan rasio batch (U9/U8) dikali stok awal E42

    25: "=(Q12+Q13)*30",
    # Item   : Es Permen Karet Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Es Permen Karet, Es Permen Karet Large

    26: "=(Q10+Q11+Q63)*30",
    # Item   : Green Tea Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Green Tea, Green Tea Large, Green Tea Cheese

    27: "=(Q2+Q3)*30",
    # Item   : Lemon Tea Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Lemon Tea, Lemon Tea Large
    # CATATAN: Rumus di file Excel salah tulis "=(Q2*+Q3)*30" — versi Anda yang BENAR

    28: "=Q55*30",
    # Item   : Lychee Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Lychee Yakult

    29: "=(Q4+Q5)*30",
    # Item   : Lychee Tea Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Lychee Tea, Lychee Tea Large

    30: "=Q54*30",
    # Item   : Mango Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Mango Yakult

    31: "=(Q35+Q57)*30",
    # Item   : Milo Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Choco Milo Sundae, Choco Milo

    32: "=(U7/U6)*E43",
    # Item   : NDC Creamer Powder
    # Logika : Proporsi pemakaian berdasarkan rasio batch (U7/U6) dikali stok awal E44

    33: "=Q56*30",
    # Item   : Ovaltine Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Choco Ovaltine

    34: "=Q51*30",
    # Item   : Red Velvet Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Red Velvet

    35: "=(Q14+Q15+Q16+Q17+Q64)*30",
    # Item   : Royal Chocolate Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Chocolate Hazelnut, Chocolate Hazelnut L, Chocolate, Chocolate L, Choco Cheese

    36: "=(Q8+Q9)*30",
    # Item   : Taro Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Taro, Taro Large

    37: "=(Q49+Q50+Q53)*30",
    # Item   : Vanilla Powder
    # Satuan : gram per cup (30gr)
    # Menu   : Vanilla Oreo, Red Velvet Oreo, Biscoff Milk

    # =========================================================
    # BAHAN SETENGAH JADI
    # =========================================================

    38: "=(Q58*100)+(Q59*120)",
    # Item   : Cold Brew
    # Satuan : ml per cup
    # Menu   : Kopi Susu Goks (100ml), Kopi Rakyat (120ml)

    39: "=Q65*100",
    # Item   : Biang Black Tea Kayu Aro
    # Satuan : ml per cup (100ml)
    # Menu   : Brown Sugar Boba Milk Tea

    40: "=(Q7+Q6+Q60)*200",
    # Item   : Biang Thai Tea
    # Satuan : ml per cup (200ml)
    # Menu   : Thai Tea Large, Thai Tea, Thai Tea Cheese

    41: "=(Q60+Q61+Q62+Q63+Q64+Q51+Q52+Q67)*30",
    # Item   : Cream Cheese
    # Satuan : gram per cup (30gr)
    # Menu   : Thai Tea Cheese, Taro Cheese, Ovaltine Cheese, Green Tea Cheese, Choco Cheese,
    #           Red Velvet, Cotton Candy, Cream Cheese (topping)

    42: "=(Q37+Q65+Q66+Q68+Q103)*40",
    # Item   : Boba
    # Satuan : gram per cup (40gr)
    # Menu   : Boba Sundae (Q37), Brown Sugar Boba Milk Tea (Q65), Brown Sugar Boba Milk (Q66),
    #           Boba Topping add-on (Q68)
    # +Q103  : Topping: Boba Topping — pelanggan yang tambah Boba secara terpisah di POS
    # [dari J_FORMULAS user: =(Q37+Q65+Q66+Q68)*40 → ditambah Q103 dari Excel]

    43: "=(Q57+Q58+Q59+Q6+Q5+Q64+Q65)*30",
    # Item   : Creamer Cair
    # Satuan : ml per cup (30ml)
    # Menu   : Choco Milo, Kopi Susu Goks, Kopi Rakyat, Thai Tea, Lychee Tea L,
    #           Choco Cheese, Brown Sugar Boba Milk Tea

    44: "=Q119*200",
    # Item   : biang vanilla


    45: "=Q118*200",
    # Item   : biang melati/jasmin


    46: "=Q120*200",
    # Item   : biang teh bendera


    47: "=((Q38+Q53+Q74+Q109)*30)+(Q88*15)",
    # Item   : Lotus / Biscoff Crumb
    # Satuan : gram per porsi (30gr menu utama, 15gr untuk Gonuts)
    # 30gr   : Biscoff Sundae (Q38), Biscoff Milk (Q53), Biscoff Crumbs topping (Q74)
    # +Q109  : Topping: Biscoff Crumbs — pelanggan yang tambah Biscoff secara terpisah di POS
    # 15gr   : Gonuts Choco Biscoff Sundae (Q88)
    # [dari J_FORMULAS user: =((Q38+Q53+Q74)*30)+(Q88*15) → ditambah Q109 dari Excel]

    48: "=((Q24+Q34+Q43+Q47+Q49+Q69+Q102)*30)+((Q82+Q86)*15)",
    # Item   : Oreo Crumbs
    # Satuan : gram per porsi (30gr menu utama, 15gr untuk Gonuts)
    # 30gr   : Oreo Sundae (Q24), Choco Oreo Sundae (Q34), Coffee Oreo Sundae (Q43),
    #           Green Tea Oreo Sundae (Q47), Vanilla Oreo (Q49), Oreo Crumbs topping (Q69)
    # +Q102  : Topping: Oreo Crumbs — pelanggan yang tambah Oreo secara terpisah di POS
    # 15gr   : Gonuts Oreo Sundae (Q82), Gonuts Choco Oreo Sundae (Q86)
    # [dari J_FORMULAS user: =((Q24+Q34+Q43+Q47+Q49+Q69)*30)+... → ditambah Q102 dari Excel]

    49: "=((Q20+Q21+Q76+Q108)*30)+(Q85*15)",
    # Item   : Strawberry Jam
    # Satuan : gram per porsi (30gr menu utama, 15gr untuk Gonuts)
    # 30gr   : Very Strawberry Sundae (Q20), Strawberry Sundae (Q21), Strawberry Jam topping (Q76)
    # +Q108  : Topping: Strawberry Jam — pelanggan yang tambah Strawberry Jam secara terpisah di POS
    # 15gr   : Gonuts Strawberry Sundae (Q85)
    # [dari J_FORMULAS user: =((Q20+Q21+Q76)*30)+(Q85*15) → ditambah Q108 dari Excel]

    50: "=((Q25+Q77+Q105)*30)+(Q83*15)",
    # Item   : Mango Jam
    # Satuan : gram per porsi (30gr menu utama, 15gr untuk Gonuts)
    # 30gr   : Mango Sundae (Q25), Mango Jam topping (Q77)
    # +Q105  : Topping: Mango Jam — pelanggan yang tambah Mango Jam secara terpisah di POS
    # 15gr   : Gonuts Mango Sundae (Q83)
    # [dari J_FORMULAS user: =(Q25+Q77*30)+(Q83*15) → DIPERBAIKI strukturnya + ditambah Q105]
    # CATATAN: Penulisan user salah — "(Q25+Q77*30)" hanya mengalikan Q77 saja,
    #          seharusnya "((Q25+Q77)*30)" agar Q25 juga ikut dikali 30

    51: "=((Q26+Q32+Q33+Q40+Q44+Q73+Q106)*30)+((Q81+Q87)*15)",
    # Item   : Chocolate Topping / Chocolate Sauce
    # Satuan : gram per porsi (30gr menu utama, 15gr untuk Gonuts)
    # 30gr   : Chocolate Sundae (Q26), Green Tea Chocolate Sundae (Q32),
    #           Double Choco Sundae (Q33), Chocolate Peanut Sundae (Q40),
    #           Coffee Choco Sundae (Q44), Chocolate Sauce topping (Q73)
    # +Q106  : Topping: Chocolate Sauce — pelanggan yang tambah Chocolate secara terpisah di POS
    # 15gr   : Gonuts Chocolate Sundae (Q81), Gonuts Double Choco Sundae (Q87)
    # [dari J_FORMULAS user: =((Q26+Q32+Q33+Q40+Q44+Q73)*30)+... → ditambah Q106 dari Excel]

    52: "=Q54+Q55",
    # Item   : Yakult
    # Satuan : botol (1 botol per cup)
    # Menu   : Mango Yakult (Q54), Lychee Yakult (Q55)

    53: "=(Q40+Q75+Q104)*5",
    # Item   : Kacang Morin (Peanut)
    # Satuan : gram per porsi (5gr)
    # Menu   : Chocolate Peanut Sundae (Q40), Peanut Topping (Q75)
    # +Q104  : Topping: Peanut Topping — pelanggan yang tambah Kacang secara terpisah di POS
    # [dari J_FORMULAS user: =(Q40+Q75)*5 → ditambah Q104 dari Excel]

    54: "=Q13*225",
    # Item   : Kacang Morin (Peanut)
    # Satuan : gram per porsi (5gr)
    # Menu   : Chocolate Peanut Sundae (Q40), Peanut Topping (Q75)
    # +Q104  : Topping: Peanut Topping — pelanggan yang tambah Kacang secara terpisah di POS
    # [dari J_FORMULAS user: =(Q40+Q75)*5 → ditambah Q104 dari Excel]

    55: "=Q115*22",
    # Item   : Kacang Morin (Peanut)
    # Satuan : gram per porsi (5gr)
    # Menu   : Chocolate Peanut Sundae (Q40), Peanut Topping (Q75)
    # +Q104  : Topping: Peanut Topping — pelanggan yang tambah Kacang secara terpisah di POS
    # [dari J_FORMULAS user: =(Q40+Q75)*5 → ditambah Q104 dari Excel]

    56: "=Q117*22",
    # Item   : Kacang Morin (Peanut)
    # Satuan : gram per porsi (5gr)
    # Menu   : Chocolate Peanut Sundae (Q40), Peanut Topping (Q75)
    # +Q104  : Topping: Peanut Topping — pelanggan yang tambah Kacang secara terpisah di POS
    # [dari J_FORMULAS user: =(Q40+Q75)*5 → ditambah Q104 dari Excel]

    57: "=Q114*6",
    # Item   : Kacang Morin (Peanut)
    # Satuan : gram per porsi (5gr)
    # Menu   : Chocolate Peanut Sundae (Q40), Peanut Topping (Q75)
    # +Q104  : Topping: Peanut Topping — pelanggan yang tambah Kacang secara terpisah di POS
    # [dari J_FORMULAS user: =(Q40+Q75)*5 → ditambah Q104 dari Excel]

    58: "=Q118*22",
    # Item   : Kacang Morin (Peanut)
    # Satuan : gram per porsi (5gr)
    # Menu   : Chocolate Peanut Sundae (Q40), Peanut Topping (Q75)
    # +Q104  : Topping: Peanut Topping — pelanggan yang tambah Kacang secara terpisah di POS
    # [dari J_FORMULAS user: =(Q40+Q75)*5 → ditambah Q104 dari Excel]

    59: "=Q116*17",
    # Item   : Kacang Morin (Peanut)
    # Satuan : gram per porsi (5gr)
    # Menu   : Chocolate Peanut Sundae (Q40), Peanut Topping (Q75)
    # +Q104  : Topping: Peanut Topping — pelanggan yang tambah Kacang secara terpisah di POS
    # [dari J_FORMULAS user: =(Q40+Q75)*5 → ditambah Q104 dari Excel]

    # =========================================================
    # ICE CREAM - SOFTMIX
    # =========================================================

    60: "=(Q21*210)+(Q24*210)+(Q25*210)+(Q26*210)+(Q27*210)+(Q28*210)+(Q29*110)+(Q37*210)+(Q38*210)+(Q39*210)+(Q40*210)+(Q41*55)+(Q42*55)+(Q46*55)+(Q48*55)+(Q99*45)+(Q100*85)+(Q107*85)+((Q70+Q101)*100)+(200*(SUM(Q110:Q117)))",
    #"=(Q21*210)+(Q24*210)+(Q25*210)+(Q26*210)+(Q27*210)+(Q28*210)+(Q29*110)+(Q37*210)+(Q38*210)+(Q39*210)+(Q40*210)+(Q41*55)+(Q42*55)+(Q46*55)+(Q48*55)+(Q99*45)+(Q100*85)+(Q107*85)+((Q70+Q101)*100)",
    #"=(Q21*210)+(Q24*210)+(Q25*210)+(Q26*210)+(Q27*210)+(Q28*210)+(Q29*110)+(Q37*210)+(Q38*210)+(Q39*210)+(Q40*210)+(Q41*55)+(Q42*55)+(Q46*55)+(Q48*55)+(Q99*45)+(Q100*85)+(Q107*85)+((Q70+Q101)*100)+(200*(SUM(Q110:Q117)))""
    # Item   : Softmix Vanilla
    # Satuan : ml per porsi (bervariasi tergantung menu)
    # 210ml  : Strawberry Sundae, Oreo Sundae, Mango Sundae, Chocolate Sundae, Lychee Sundae,
    #           Kiwi Sundae, Boba Sundae, Biscoff Sundae, Red Velvet Oreo Sundae, Choco Peanut Sundae
    # 110ml  : Ice Cream Cone (Q29)
    # 55ml   : Choco Vanilla Cone (Q41), Green Tea Vanilla Cone (Q42),
    #           Coffee Vanilla Cone (Q46), Strawberry Vanilla Cone (Q48)
    # +Q99   : Free Topping Pudding Ice Cream Mix Vanilla & Coffee (45ml)
    # +Q100  : Free Topping Pudding Ice Cream Vanilla (85ml)
    # +Q107  : Topping: Free Topping Pudding Ice Cream Vanilla (85ml)
    # +Q101  : Topping: Vanilla Ice Cream — pelanggan yang tambah Vanilla Ice Cream di POS (100ml)
    # +Q70   : Vanilla Ice Cream topping (100ml)
    # [dari J_FORMULAS user: sampai Q48*55 saja → ditambah Q99,Q100,Q107,Q70,Q101 dari Excel]

    61: "=((Q43+Q44)*210)+(Q45*120)+(Q46*60)",
    # Item   : Softmix Mocca
    # Satuan : ml per porsi (bervariasi tergantung menu)
    # 210ml  : Coffee Oreo Sundae (Q43), Coffee Choco Sundae (Q44)
    # 120ml  : Coffee Cone (Q45)
    # 60ml   : Coffee Vanilla Cone (Q46) — porsi Mocca dalam cone mix
    # [BARU — belum ada di J_FORMULAS user]

    62: "=((Q30+Q32))*220+(Q31*120)+(Q42*60)",
    # Item   : Softmix Green Tea
    # Satuan : ml per porsi (bervariasi tergantung menu)
    # 220ml  : Green Tea Sundae (Q30), Green Tea Chocolate Sundae (Q32)
    # 120ml  : Green Tea Cone (Q31)
    # 60ml   : Green Tea Vanilla Cone (Q42) — porsi Green Tea dalam cone mix
    # [BARU — belum ada di J_FORMULAS user]

    63: "=(Q20+Q22)*210+(Q23*120)+(Q48*60)",
    # Item   : Softmix Strawberry
    # Satuan : ml per porsi (bervariasi tergantung menu)
    # 210ml  : Very Strawberry Sundae (Q20), Strawberry Oreo Sundae (Q22)
    # 120ml  : Strawberry Cone (Q23)
    # 60ml   : Strawberry Vanilla Cone (Q48) — porsi Strawberry dalam cone mix
    # [BARU — belum ada di J_FORMULAS user]

    64: "=(Q33+Q34+Q35)*210+((Q41)*55)+((Q36+Q88+Q87+Q86)*110)",
    # Item   : Softmix Chocolate
    # Satuan : ml per porsi (bervariasi tergantung menu)
    # 210ml  : Double Choco Sundae (Q33), Choco Oreo Sundae (Q34), Choco Milo Sundae (Q35)
    # 55ml   : Choco Vanilla Cone (Q41) — porsi Chocolate dalam cone mix
    # 110ml  : Choco Cone (Q36), Gonuts Choco Biscoff Sundae (Q88),
    #           Gonuts Double Choco Sundae (Q87), Gonuts Choco Oreo Sundae (Q86)
    # [BARU — belum ada di J_FORMULAS user]

    # =========================================================
    # PACKAGING - ICE CREAM
    # =========================================================

    65: "=Q20+Q21+Q22+Q24+Q25+Q26+Q27+Q28+Q30+Q32+Q33+Q34+Q35+Q37+Q38+Q39+Q40+Q43+Q44+Q47+Q78",
    # Item   : Cup 12 Oz
    # Logika : Semua menu Sundae + Cup Take Away 12 OZ pakai Cup 12 Oz
    # Menu   : Very Strawberry, Strawberry, Strawberry Oreo, Oreo, Mango, Chocolate,
    #           Lychee, Kiwi, Green Tea, Green Tea Chocolate, Double Choco, Choco Oreo,
    #           Choco Milo, Boba, Biscoff, Red Velvet Oreo, Choco Peanut,
    #           Coffee Oreo, Coffee Choco, Green Tea Oreo Sundae + Cup Take Away 12 OZ (Q78)

    66: "=Q23+Q29+Q31+Q36+Q41+Q42+Q45+Q46+Q48",
    # Item   : Cone
    # Logika : Semua menu Ice Cream Cone pakai Cone
    # Menu   : Strawberry Cone, Ice Cream Cone, Green Tea Cone, Choco Cone,
    #           Choco Vanilla Cone, Green Tea Vanilla Cone, Coffee Cone,
    #           Coffee Vanilla Cone, Strawberry Vanilla Cone

    67: "=Q20+Q21+Q22+Q24+Q25+Q26+Q27+Q28+Q30+Q32+Q33+Q34+Q35+Q37+Q38+Q39+Q40+Q43+Q44+Q47+Q89+Q90+Q91+Q92+Q93+Q94+Q95+Q96+Q97",
    # Item   : Sendok Ice Cream
    # Logika : Semua menu Sundae + semua Paper Cup pakai sendok ice cream
    # Sundae : sama seperti Cup 12 Oz (tanpa Q78)
    # Paper  : Vanilla s/d Coffee Vanilla Paper Cup (Q89:Q97)

    68: "=SUM(Q89:Q97)",
    # Item   : Cup 4 Oz
    # Logika : Semua menu Paper Cup pakai Cup 4 Oz
    # Menu   : Vanilla Paper Cup s/d Coffee Vanilla Paper Cup (Q89:Q97)

    69: "=SUM(Q80:Q88)",
    # Item   : Donut Gula
    # Logika : Semua menu Gonuts butuh donut (termasuk Gonuts plain Q80)
    # Menu   : Gonuts (Q80) + semua varian Gonuts Sundae (Q81:Q88)

    70: "=SUM(Q81:Q88)",
    # Item   : Garpu Donut
    # Logika : Semua Gonuts Sundae butuh garpu (kecuali Gonuts plain Q80)
    # Menu   : Gonuts Chocolate s/d Gonuts Choco Biscoff Sundae (Q81:Q88)

    71: "=SUM(Q81:Q88)",
    # Item   : Paper Tray
    # Logika : Semua Gonuts Sundae butuh paper tray
    # Menu   : Gonuts Chocolate s/d Gonuts Choco Biscoff Sundae (Q81:Q88)

    72: "=SUM(Q81:Q88)",
    # Item   : Pisau Donut
    # Logika : Semua Gonuts Sundae butuh pisau donut
    # Menu   : Gonuts Chocolate s/d Gonuts Choco Biscoff Sundae (Q81:Q88)

    73: "=Q110+Q111+Q112+Q113+Q114+Q115+Q116+Q117",
    # Item   : cup twist

    74: "=Q110+Q111+Q112+Q113+Q114+Q115+Q116+Q117",
    # Item   : tutup twist

    75: "=Q110+Q111+Q112+Q113+Q114+Q115+Q116+Q117",
    # Item   : sendok silkyY

}

# ─── RUMUS RELATIVE KOLOM K, L, M ────────────────────────────────────────────
# {r} akan diganti dengan nomor baris saat penulisan
# Untuk mengubah rumus → ganti value-nya
# Untuk mengubah rentang baris → ubah RELATIVE_ROW_START / RELATIVE_ROW_END di atas

RELATIVE_FORMULAS = {
    "K": "=D{r}+E{r}-F{r}-G{r}",
    "L": "=D{r}+E{r}-J{r}",
    "M": "=J{r}-K{r}",
}

# ─── FUNGSI UTAMA ─────────────────────────────────────────────────────────────

def _safe_write(ws, row, col, value):
    """Tulis value ke cell, aman untuk MergedCell."""
    cell = ws.cell(row=row, column=col)
    if isinstance(cell, MergedCell):
        for merged_range in ws.merged_cells.ranges:
            if (merged_range.min_row <= row <= merged_range.max_row and
                    merged_range.min_col <= col <= merged_range.max_col):
                cell = ws.cell(row=merged_range.min_row, column=merged_range.min_col)
                break
    try:
        cell.value = value
    except:
        pass
    return cell


def _set_cell(ws, row, col, fill=None, locked=True, border=None, value=None):
    """
    Helper satu tempat: tulis value, set fill, border, dan lock sekaligus.
    Aman untuk MergedCell — cell merged di-skip.
    """
    cell = ws.cell(row=row, column=col)
    if isinstance(cell, MergedCell):
        return
    if value is not None:
        try:
            cell.value = value
        except:
            pass
    if fill is not None:
        cell.fill = fill
    if border is not None:
        cell.border = border
    cell.protection = Protection(locked=locked)


def apply_all(ws, lock_column_d=False):
    """
    Fungsi utama yang dipanggil dari processor.py.

    Arsitektur SATU PASS:
      1. Unlock semua cell (clean slate)
      2. Terapkan kuning + lock + rumus per kelompok kolom
      3. Aktifkan proteksi sheet
    Tidak ada fungsi yang saling menimpa karena semua dikerjakan
    dalam urutan linier tanpa unlock kedua.

    Kolom & rentang:
      A(1), B(2)        → kuning + lock, baris 1–95
      D(4)              → kuning + lock, baris 1–95, HANYA jika lock_column_d=True
      I(9)              → kuning + lock, baris 2–95  (nilai tetap, tidak ada rumus)
      J(10)             → kuning + lock + rumus J_FORMULAS, baris 2–95
      K(11),L(12),M(13) → kuning + lock + rumus relative, baris 2–95
      O(15),P(16),Q(17) → kuning + lock + border, baris 2–120
      S(19),T(20),U(21) → kuning + lock, baris 2–19
      W(23),X(24)       → kuning + lock + border + rumus, baris 1–122
        - W/X baris 1        : header oranye
        - W/X baris 2–120    : data produk (X = =W{r}*M{r})
        - W121               : label "Selisih Bersih", X121 = =SUM(X2:X120)
        - W122               : label "Kerugian Murni", X122 = =SUMIF(X2:X120,"<0")

    Parameter:
        lock_column_d (bool): True untuk sheet 02-31, False untuk sheet 01.
    """

    # ── STEP 1: Unlock semua cell (clean slate) ───────────────────────────────
    for row in ws.iter_rows():
        for cell in row:
            if not isinstance(cell, MergedCell):
                cell.protection = Protection(locked=False)

    # ── STEP 2A: Kolom A (1) dan B (2) → baris 1–95, kuning + lock ───────────
    for col in [1, 2]:
        for r in range(AB_ROW_START, AB_ROW_END + 1):
            _set_cell(ws, r, col, fill=FORMULA_FILL, locked=True)

    # ── STEP 2B: Kolom D (4) → baris 1–95, kuning + lock (sheet 02-31 saja) ──
    if lock_column_d:
        for r in range(D_ROW_START, D_ROW_END + 1):
            _set_cell(ws, r, 4, fill=FORMULA_FILL, locked=True)

    # ── HEADER I-M (baris 1) ────────────────────────────────────────────────
    for col in [9, 10, 11, 12, 13]:
        _set_cell(
            ws,
            1,
            col,
            fill=HEADER_IJKLM_FILL,
            locked=True
        )

    # ── STEP 2C: Kolom I (9) → baris 2–95, kuning + lock ────────────────────
    for r in range(IJKLM_ROW_START, IJKLM_ROW_END + 1):
        _set_cell(ws, r, 9, fill=FORMULA_FILL, locked=True)

    # ── STEP 2D: Kolom J (10) → baris 2–95, kuning + lock + rumus ───────────
    for r in range(J_FILL_ROW_START, J_FILL_ROW_END + 1):
        _set_cell(ws, r, 10, fill=FORMULA_FILL, locked=True)
    for row_num, formula in J_FORMULAS.items():
        _safe_write(ws, row_num, 10, formula)

    # ── STEP 2E: Kolom K(11), L(12), M(13) → baris 2–95, kuning+lock+rumus ──
    col_map = {"K": 11, "L": 12, "M": 13}
    for col_letter, col_idx in col_map.items():
        for r in range(RELATIVE_ROW_START, RELATIVE_ROW_END + 1):
            formula = RELATIVE_FORMULAS[col_letter].format(r=r)
            _set_cell(ws, r, col_idx, fill=FORMULA_FILL, locked=True, value=formula)

    # ── STEP 2F: Kolom O(15), P(16), Q(17) → baris 2–120, kuning+lock+border─
    # Bersihkan dulu label lama di baris 118 & 119 kolom W jika ada
    for r in range(OPQ_ROW_START, OPQ_ROW_END + 1):
        for col in [15, 16, 17]:
            _set_cell(ws, r, col, fill=FORMULA_FILL, locked=True, border=CELL_BORDER)

    # ── STEP 2G: Kolom S(19), T(20), U(21) → baris 2–19, kuning + lock ──────
    for col in [19, 20, 21]:
        for r in range(STU_ROW_START, STU_ROW_END + 1):
            _set_cell(ws, r, col, fill=FORMULA_FILL, locked=True)

    # ── STEP 2H: Kolom W(23) dan X(24) → baris 1–122 ────────────────────────
    # Bersihkan label lama "Selisih Bersih" / "Kerugian Murni" di baris 118-119
    for r in [118, 119]:
        cell_w = ws.cell(row=r, column=23)
        if not isinstance(cell_w, MergedCell):
            old_val = str(cell_w.value or "")
            if "Selisih" in old_val or "Kerugian" in old_val:
                cell_w.value = None

    # Baris 1: header oranye
    for col in [23, 24]:
        _set_cell(ws, 1, col, fill=HEADER_WX_FILL, locked=True, border=CELL_BORDER)

    # Baris 2–120: data produk, kuning, rumus X = W*M
    for r in range(2, WX_DATA_END + 1):
        _set_cell(ws, r, 23, fill=FORMULA_FILL, locked=True, border=CELL_BORDER)
        _set_cell(ws, r, 24, fill=FORMULA_FILL, locked=True, border=CELL_BORDER,
                  value=f"=W{r}*M{r}")

    # Baris 121: Selisih Bersih
    _set_cell(ws, WX_SUMMARY_START, 23, fill=FORMULA_FILL, locked=True,
              border=CELL_BORDER, value="Selisih Bersih")
    _set_cell(ws, WX_SUMMARY_START, 24, fill=FORMULA_FILL, locked=True,
              border=CELL_BORDER, value=f"=SUM(X2:X{WX_DATA_END})")

    # Baris 122: Kerugian Murni
    _set_cell(ws, WX_SUMMARY_START + 1, 23, fill=FORMULA_FILL, locked=True,
              border=CELL_BORDER, value="Kerugian Murni")
    _set_cell(ws, WX_SUMMARY_START + 1, 24, fill=FORMULA_FILL, locked=True,
              border=CELL_BORDER, value=f'=SUMIF(X2:X{WX_DATA_END},"<0")')

    # ── STEP 3: Aktifkan proteksi sheet ──────────────────────────────────────
    ws.protection.sheet = True
    ws.protection.password = SHEET_PASSWORD
    ws.protection.selectLockedCells = False
    ws.protection.selectUnlockedCells = False
    ws.protection.formatColumns = False   # izinkan resize kolom
    ws.protection.formatRows = False      # izinkan resize baris