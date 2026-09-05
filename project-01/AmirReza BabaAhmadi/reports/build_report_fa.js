const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, Header, Footer, PageNumber,
  VerticalAlign,
} = require("docx");
const { ROOT, summary, waterfall } = require("./report_data");

const NAVY = "1F4E5A";
const BLUE = "2E6E8E";
const LIGHT = "EAF1F4";
const GREY = "5A6B72";
const FONT = "Noto Sans Arabic"; // covers Persian glyphs (پ چ ژ گ ک ی)
const LATIN_FONT = "Noto Sans"; // Noto Sans Arabic's own Latin glyphs mis-kern for plain ASCII (filenames, code)

const fig = (name) => fs.readFileSync(path.join(ROOT, "figures", name));

const FA_DIGITS = { 0: "۰", 1: "۱", 2: "۲", 3: "۳", 4: "۴", 5: "۵", 6: "۶", 7: "۷", 8: "۸", 9: "۹" };
function fa(n) {
  return String(n).replace(/[0-9]/g, (d) => FA_DIGITS[d]);
}
function faPct(n, d) {
  return fa(((n / d) * 100).toFixed(1)) + "٪";
}
// Only mark a run right-to-left when it actually contains Persian/Arabic
// script. Forcing rtl:true on a run that is purely Latin (a filename like
// "sales.csv", a column name, "R1"/"F1") makes some renderers mis-shape and
// stretch it; the surrounding paragraph's bidirectional flag already places
// it correctly within the RTL flow via the standard Unicode bidi algorithm.
function isRtlScript(text) {
  return /[؀-ۿ]/.test(text);
}
function pickFont(text) {
  return isRtlScript(text) ? FONT : LATIN_FONT;
}
// Split mixed Persian/Latin text into per-script runs (e.g. a Persian
// sentence that quotes a path like data/processed/quarantine_*.csv) so each
// segment gets its own font and rtl flag. Rendering a Latin code/path
// fragment under "Noto Sans Arabic" (because the sentence as a whole is
// Persian) mis-shapes and misplaces it -- this keeps each script segment on
// its native font while the paragraph's bidirectional flag still reorders
// the segments correctly for display.
function splitSegments(text) {
  return String(text).match(/[؀-ۿ]+|[^؀-ۿ]+/g) || [String(text)];
}
function runsFor(text, extra = {}) {
  return splitSegments(text).map((seg) => new TextRun({
    text: seg, font: pickFont(seg), rightToLeft: isRtlScript(seg), ...extra,
  }));
}

// ---------------------------------------------------------------------------
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    bidirectional: true,
    alignment: AlignmentType.RIGHT,
    spacing: { before: 380, after: 180 },
    border: { bottom: { color: BLUE, space: 4, style: BorderStyle.SINGLE, size: 6 } },
    children: runsFor(text, { bold: true, color: NAVY, size: 30 }),
  });
}
function p(text) {
  return new Paragraph({
    bidirectional: true,
    alignment: AlignmentType.RIGHT,
    spacing: { after: 160, line: 300 },
    children: runsFor(text, { size: 22 }),
  });
}
function bullet(text) {
  return new Paragraph({
    bidirectional: true,
    alignment: AlignmentType.RIGHT,
    bullet: { level: 0 },
    spacing: { after: 90 },
    children: runsFor(text, { size: 22 }),
  });
}
function caption(text) {
  return new Paragraph({
    bidirectional: true,
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 260 },
    children: runsFor(text, { size: 18, italics: true, color: GREY }),
  });
}
function image(name, widthPx = 520) {
  const buf = fig(name);
  const ratio = 675 / 1200;
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: widthPx, height: Math.round(widthPx * ratio) } })],
  });
}

function cellText(text, { bold = false, color = "111111", align = AlignmentType.RIGHT } = {}) {
  const s = String(text);
  return new Paragraph({
    bidirectional: true,
    alignment: align,
    children: runsFor(s, { bold, color, size: 20 }),
  });
}
function headerCell(text, width) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: NAVY, color: "auto" },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [cellText(text, { bold: true, color: "FFFFFF" })],
  });
}
function bodyCell(text, width, { shaded = false, align = AlignmentType.RIGHT, bold = false, color = "111111" } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shaded ? { type: ShadingType.CLEAR, fill: LIGHT, color: "auto" } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 70, bottom: 70, left: 100, right: 100 },
    children: [cellText(text, { align, bold, color })],
  });
}
function dataTable(widths, headers, rows) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    visuallyRightToLeft: true,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => headerCell(h, widths[i])) }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((c, ci) => bodyCell(c, widths[ci], { shaded: ri % 2 === 1, align: ci === r.length - 1 ? AlignmentType.RIGHT : AlignmentType.CENTER })),
      })),
    ],
  });
}

const S = summary;

// ---------------------------------------------------------------------------
const children = [];

// Title page ------------------------------------------------------------
children.push(
  new Paragraph({ spacing: { before: 1300 }, alignment: AlignmentType.CENTER, bidirectional: true,
    children: [new TextRun({ text: "خط لوله یکپارچه‌سازی داده‌های موجودی", bold: true, color: NAVY, size: 50, font: FONT, rightToLeft: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, bidirectional: true, spacing: { after: 100 },
    children: [
      new TextRun({ text: "کالاهای مصرفی سریع‌گردش (", bold: true, color: NAVY, size: 50, font: FONT, rightToLeft: true }),
      new TextRun({ text: "FMCG", bold: true, color: NAVY, size: 50, font: LATIN_FONT }),
      new TextRun({ text: ")", bold: true, color: NAVY, size: 50, font: FONT, rightToLeft: true }),
    ] }),
  new Paragraph({ alignment: AlignmentType.CENTER, bidirectional: true, spacing: { before: 260, after: 40 },
    children: [new TextRun({ text: "گزارش پروژه", color: BLUE, size: 32, font: FONT, rightToLeft: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, bidirectional: true, spacing: { before: 40 },
    children: [
      new TextRun({ text: "Python · Pandas · SQLite", color: GREY, size: 22, italics: true, font: LATIN_FONT }),
      new TextRun({ text: " — یک پروژه خودآموز ده‌روزه", color: GREY, size: 22, italics: true, font: FONT, rightToLeft: true }),
    ] }),
  new Paragraph({ alignment: AlignmentType.CENTER, bidirectional: true, spacing: { before: 900 },
    children: [new TextRun({ text: "تهیه‌شده برای: امیررضا بابااحمدی", color: GREY, size: 20, font: FONT, rightToLeft: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, bidirectional: true, spacing: { before: 60 },
    children: [new TextRun({ text: `تاریخ داده‌ها: ${fa(1)} سپتامبر ${fa(2026)}`, color: GREY, size: 20, font: FONT, rightToLeft: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, bidirectional: true, spacing: { before: 60, after: 200 },
    children: [new TextRun({ text: `تاریخ گزارش: ${fa(5)} سپتامبر ${fa(2026)}`, color: GREY, size: 20, font: FONT, rightToLeft: true })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// Contents ----------------------------------------------------------------------
const TOC_ENTRIES = [
  "۱. خلاصه مدیریتی", "۲. مسئله کسب‌وکار و اهداف", "۳. منابع داده",
  "۴. معماری خط لوله", "۵. یافته‌های کیفیت داده (Q1)",
  "۶. اعتبارسنجی قوانین کسب‌وکار (Q2)", "۷. استانداردسازی و تبدیل داده (Q3)",
  "۸. یکپارچه‌سازی داده (Q4)", "۹. نمای تحلیلی آماده کسب‌وکار (Q5)",
  "۱۰. پرچم‌های عملیاتی (Q6)", "۱۱. بارگذاری و بازتولیدپذیری (Q7)",
  "۱۲. ثبت رخداد و مسیر ممیزی (Q8)", "۱۳. محدودیت‌ها", "۱۴. نتیجه‌گیری و پیشنهادها",
];
children.push(
  h1("فهرست مطالب"),
  ...TOC_ENTRIES.map((t) => new Paragraph({
    bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { after: 130 },
    children: [new TextRun({ text: t, size: 22, font: FONT, color: "222222", rightToLeft: true })],
  })),
  new Paragraph({ children: [new PageBreak()] }),
);

// 1. خلاصه مدیریتی -----------------------------------------------------------
children.push(
  h1("۱. خلاصه مدیریتی"),
  p("این پروژه یک خط لوله ETL کامل و بازتولیدپذیر برای داده‌های فروش، سفارش و موجودی یک توزیع‌کننده منطقه‌ای کالاهای مصرفی سریع‌گردش (FMCG) می‌سازد. چهار فایل خام CSV — فروش، سفارش‌ها، عکس‌های لحظه‌ای موجودی و فایل مرجع انبارها — پروفایل‌بندی، در برابر هشت قانون صریح کسب‌وکار اعتبارسنجی، پاک‌سازی و استانداردسازی، به‌صورت ایمن در یک جدول تحلیلی آماده کسب‌وکار یکپارچه، از نظر چهار وضعیت ریسک عملیاتی بررسی و در نهایت در یک پایگاه‌داده SQLite بارگذاری شدند. هر مرحله برای ممیزی ثبت شده است."),
  p(`این خط لوله ${fa(S.raw_row_counts.sales)} ردیف خام فروش، ${fa(S.raw_row_counts.orders)} ردیف خام سفارش و ${fa(S.raw_row_counts.inventory)} ردیف خام عکس لحظه‌ای موجودی را در ${fa(S.raw_row_counts.warehouses)} انبار پردازش کرد. پس از اعتبارسنجی و پاک‌سازی، ${fa(S.clean_row_counts.sales)} ردیف فروش، ${fa(S.clean_row_counts.orders)} ردیف سفارش و ${fa(S.clean_row_counts.inventory)} ردیف موجودی بارگذاری شدند که نمای آماده کسب‌وکاری شامل ${fa(S.analytic_rows)} ترکیب کالا/انبار را پدید آوردند. تعداد ردیف‌های هر جدول SQLite در برابر دیتافریم منبع آن راستی‌آزمایی شد و هیچ ردیفی از جداول واقعیت به انباری اشاره نمی‌کند که در فایل مرجع انبارها وجود نداشته باشد.`),
  p(`یافته‌های کلیدی: ${faPct(S.flag_counts.flag_excess_inventory, S.analytic_rows)} از ترکیب‌های کالا/انبار نسبت به سرعت فروش اخیر موجودی مازاد نشان می‌دهند، ${faPct(S.flag_counts.flag_dead_stock, S.analytic_rows)} در ۳۰ روز گذشته هیچ فروشی نداشته‌اند (موجودی راکد) و ${faPct(S.flag_counts.flag_order_backlog, S.analytic_rows)} مقدار سفارش باز بیشتری از موجودی فعلی دارند. این موارد برای بررسی کسب‌وکاری پرچم‌گذاری شده‌اند، نه برای اقدام خودکار — به بخش ۱۰ مراجعه کنید.`),
);

// 2. مسئله کسب‌وکار و اهداف --------------------------------------------------
children.push(
  h1("۲. مسئله کسب‌وکار و اهداف"),
  p("یک توزیع‌کننده، داده‌های فروش، سفارش خرید و موجودی انبار را در سه سیستم جداگانه نگهداری می‌کند که با زمان‌بندی‌های متفاوت و بدون استاندارد مشترک برای ورود داده، فایل‌های مسطح (flat file) خروجی می‌گیرند. پیش از پاسخ به سؤالات عملیاتی پایه — کدام کالاها در آستانه اتمام موجودی هستند، کدام انبارها بیش از حد موجودی دارند، آیا سفارش‌های باز برای پوشش تقاضای اخیر کافی هستند — باید این چهار منبع پروفایل‌بندی، به یک استاندارد مشترک پاک‌سازی، به‌صورت ایمن ترکیب و از نظر سازگاری درونی بررسی شوند."),
  p("این پروژه به هشت پرسش مشخص، با تکیه بر شواهد و نه فرض، پاسخ می‌دهد:"),
  bullet("Q1 — آیا می‌توان به داده‌های خام اعتماد کرد و دقیقاً کجای آن‌ها مشکل دارد؟"),
  bullet("Q2 — کدام رکوردها قوانین داده‌ای خود کسب‌وکار را نقض می‌کنند؟"),
  bullet("Q3 — آیا چهار فایل بدون ویرایش دستی در صفحه‌گسترده می‌توانند به‌صورت خودکار استاندارد شوند؟"),
  bullet("Q4 — آیا منابع بدون از دست رفتن یا تکرار پنهانِ رکوردها قابل ادغام‌اند؟"),
  bullet("Q5 — یک نمای واحد و آماده کسب‌وکار از موجودی چه شکلی دارد؟"),
  bullet("Q6 — کدام ترکیب‌های کالا/انبار همین حالا نیاز به توجه عملیاتی دارند؟"),
  bullet("Q7 — آیا بارگذاری در SQLite بازتولیدپذیر و از نظر درونی سازگار است؟"),
  bullet("Q8 — آیا مسیر ممیزی کاملی از رخدادها و زمان آن‌ها وجود دارد؟"),
);

// 3. منابع داده ---------------------------------------------------------------
children.push(
  h1("۳. منابع داده"),
  p("برای این پروژه هیچ خروجی واقعی از سامانه تولید در دسترس نبود؛ بنابراین یک مجموعه داده مصنوعی اما واقع‌گرایانه تولید شد (اسکریپت scripts_generate_raw_data.py، با بذر تصادفی numpy برای بازتولیدپذیری کامل). تولیدکننده رویکردی ترکیبی را دنبال می‌کند: ساختارهای جدولی معقول برای تراکنش/سفارش/موجودی همراه با یک شبکه توزیع شبیه‌سازی‌شده هشت‌انباره، که عمداً با همان دسته‌های مشکلاتی که یک خروجی واقعی دارد آلوده شده است؛ به این ترتیب خط لوله چیزی واقعی برای پاک‌سازی دارد، نه یک مجموعه داده تمیز و ساختگی."),
  p("مشکلات عمداً واردشده:"),
  bullet("سرستون‌های ناهماهنگ در فایل‌ها (\" SKU\"، \"Warehouse_ID\"، \"OrderedQty\"، \"SnapshotDate\" و…)"),
  bullet("فرمت‌های تاریخ مختلط (ISO، آمریکایی، \"15-Jan-2026\") و تاریخ‌های کاملاً خالی"),
  bullet("کدهای کالا (SKU) و مقادیر خالی"),
  bullet("مقادیر منفی بدون علامت‌گذاری — سامانه‌های منبع هیچ نشانگری برای «این یک مرجوعی مستند است» ندارند"),
  bullet("شناسه انبار با نگارش/بزرگی‌وکوچکی حروف ناهماهنگ (\"wh-01\"، \"WH_05\")"),
  bullet("شناسه‌های انباری که اصلاً وجود ندارند (WH-99) یا در تراکنش‌ها هستند اما در فایل مرجع انبارها نیستند (WH-09) — یک کلید خارجی آویزان"),
  bullet("ردیف‌های کاملاً تکراری و کلیدهای اصلی تکراری (تراکنش‌ها/سفارش‌های دوباره‌ارسال‌شده)"),
  bullet("متن وضعیت سفارش با غلط تایپی و بزرگی‌وکوچکی ناهماهنگ (\"Shiped\"، \"PENDING\"، \"cancelled\")"),
);

// 4. معماری خط لوله -------------------------------------------------------------
children.push(
  h1("۴. معماری خط لوله"),
  p("خط لوله در پنج ماژول زیرِ پوشه src/ سازمان‌دهی شده که به ترتیبی ثابت توسط src/main.py اجرا می‌شوند:"),
  bullet("extract.py — چهار فایل CSV خام را دقیقاً به همان شکلی که دریافت شده‌اند می‌خواند"),
  bullet("profile.py — پروفایل کامل کیفیت داده برای هر فایل خام (Q1)"),
  bullet("transform.py — استانداردسازی، قوانین اعتبارسنجی، ادغام‌های ایمن، نمای آماده کسب‌وکار و پرچم‌های عملیاتی (Q2 تا Q6)"),
  bullet("load.py — پنج جدول را در SQLite می‌نویسد و بارگذاری را راستی‌آزمایی می‌کند (Q7)"),
  bullet("main.py — تمام مراحل بالا را هماهنگ کرده و لاگ‌ها، نمودارها و خلاصه کیفیت را می‌نویسد (Q8)"),
  p("هر فایل دقیقاً از همان توالی ثابت عبور می‌کند: خواندن خام ← استانداردسازی نام ستون‌ها ← تبدیل نوع داده (تاریخ، عدد) ← اجرای قانون کلید خارجی انبار ← اعمال باقی قوانین اعتبارسنجی ← حذف تکراری‌های کامل ← حذف تکراری بر اساس کلید اصلی. استفاده مجدد از یک مجموعه توابع تبدیل در هر چهار فایل — به‌جای نوشتن کد پاک‌سازی اختصاصی برای هر فایل — همان چیزی است که خط لوله را قابل نگهداری و رفتار آن را قابل پیش‌بینی می‌کند."),
);

// 5. یافته‌های کیفیت داده (Q1) -----------------------------------------------
children.push(
  h1("۵. یافته‌های کیفیت داده (Q1)"),
  p("هر فایل خام پیش از هرگونه پاک‌سازی پروفایل‌بندی شد: تعداد ردیف/ستون، نام دقیق ستون‌ها همان‌گونه که دریافت شده، درصد مقادیر گمشده، ردیف‌های کاملاً تکراری، کلیدهای اصلی تکراری، تاریخ‌های غیرقابل‌تجزیه، مقادیر منفی در ستون‌های مقداری، کدهای کالای خالی و شناسه‌های انباری که در فایل مرجع انبارها نیستند. جزئیات کامل در logs/pipeline.log ثبت شده؛ اعداد کلیدی:"),
  dataTable(
    [1100, 1700, 1500, 1200, 1200, 2200],
    ["مقدار منفی", "تاریخ غیرقابل‌تجزیه", "SKU خالی/گمشده", "تکراری کامل", "تعداد ردیف", "فایل"],
    [
      [fa(S.raw_profiles.sales.negatives[" Quantity"]), fa(S.raw_profiles.sales.bad_dates["SaleDate "]), fa(S.raw_profiles.sales.n_blank_sku), fa(S.raw_profiles.sales.n_exact_dupes), fa(S.raw_profiles.sales.n_rows), "sales.csv"],
      [fa(S.raw_profiles.orders.negatives["OrderedQty"]), fa(S.raw_profiles.orders.bad_dates["Order Date"]), fa(S.raw_profiles.orders.n_blank_sku), fa(S.raw_profiles.orders.n_exact_dupes), fa(S.raw_profiles.orders.n_rows), "orders.csv"],
      [fa(S.raw_profiles.inventory.negatives["OnHandQty"]), fa(S.raw_profiles.inventory.bad_dates["SnapshotDate"]), fa(S.raw_profiles.inventory.n_blank_sku), fa(S.raw_profiles.inventory.n_exact_dupes), fa(S.raw_profiles.inventory.n_rows), "inventory.csv"],
      ["—", "—", "—", fa(S.raw_profiles.warehouses.n_exact_dupes), fa(S.raw_profiles.warehouses.n_rows), "warehouses.csv"],
    ],
  ),
  caption("جدول ۱. پروفایل کیفیت داده خام، پیش از هرگونه پاک‌سازی."),
  p(`ناهنجاری‌های شناسه انبار (مقادیری که به هیچ ردیفی در warehouses.csv نگاشت نمی‌شوند) نیز برای هر فایل شمارش شد: ${fa(S.raw_profiles.sales.n_orphan_warehouse)} مورد در فروش، ${fa(S.raw_profiles.orders.n_orphan_warehouse)} مورد در سفارش‌ها و ${fa(S.raw_profiles.inventory.n_orphan_warehouse)} مورد در موجودی. این موارد در بخش بعد تحت قانون R2 رسیدگی می‌شوند، نه اینکه به‌صورت موردی حذف شوند.`),
  p("سرستون‌های دریافتی نیز مستقیماً مشکل استانداردسازی را نشان می‌دهند: فایل sales.csv با سرستون‌های \" SKU\"، \"SaleDate \" و \"Warehouse_ID\" در کنار هم دریافت شد — سه قرارداد متفاوت فاصله‌گذاری و بزرگی‌وکوچکی حروف در یک فایل شش‌ستونی. این دقیقاً همان چیزی است که بخش ۷ (Q3) به‌صورت خودکار استاندارد می‌کند."),
);

// 6. اعتبارسنجی قوانین کسب‌وکار (Q2) -----------------------------------------
children.push(
  h1("۶. اعتبارسنجی قوانین کسب‌وکار (Q2)"),
  p("هشت قانون پیش از نوشتن هر کد پاک‌سازی تعریف شدند تا هر تصمیم حذف یا پرچم‌گذاری در ادامه مسیر، به یک قانون صریح و مستند بازگردد، نه یک قضاوت موردی هنگام نگاه‌کردن به داده:"),
  dataTable(
    [3550, 5100, 850],
    ["نحوه اجرا", "بیانیه", "قانون"],
    [
      ["ردیف‌ها حذف می‌شوند؛ تعداد ثبت می‌شود", "کد کالا (SKU) نباید خالی باشد", "R1"],
      ["ردیف‌ها به‌جای حذف بی‌صدا، در data/processed/quarantine_*.csv قرنطینه می‌شوند", "warehouse_id باید در جدول مرجع انبارها وجود داشته باشد", "R2"],
      ["مقادیر غیرقابل‌تجزیه با pd.to_datetime(errors='coerce') خالی می‌شوند؛ ردیف‌های با تاریخ الزامی خالی حذف می‌شوند", "ستون‌های تاریخ باید قابل تجزیه باشند", "R3"],
      ["مقادیر غیرعددی با pd.to_numeric(errors='coerce') خالی می‌شوند", "ستون‌های مقداری باید عددی باشند", "R4"],
      ["چون هیچ پرچم مرجوعی در داده منبع نیست، هر مقدار منفی خطا در نظر گرفته و حذف می‌شود", "مقدار منفی فقط در صورت علامت‌گذاری به‌عنوان مرجوعی مستند معتبر است", "R5"],
      ["ردیف‌ها حذف می‌شوند؛ تعداد ثبت می‌شود", "on_hand_qty نمی‌تواند منفی باشد", "R6"],
      ["transaction_id / order_id با حفظ نخستین مورد از تکرار حذف می‌شوند", "کلیدهای اصلی نباید تکرار شوند", "R7"],
      ["در مرحله پروفایل‌بندی بررسی می‌شود (بخش ۵)", "ستون‌های الزامی نباید کاملاً خالی باشند", "R8"],
    ],
  ),
  caption("جدول ۲. قوانین کسب‌وکاری اعتبارسنجی‌شده در src/transform.py."),
  p("قانون R2 نیازمند توضیح جداگانه است: به‌جای حذف بی‌صدای ردیف‌های دارای شناسه انبار ناشناخته، خط لوله آن‌ها را به یک فایل قرنطینه به ازای هر منبع هدایت می‌کند (برای نمونه data/processed/quarantine_sales_bad_warehouse_id.csv) و تمام ستون‌های اصلی را دست‌نخورده نگه می‌دارد تا یک مسئول داده بتواند آن‌ها را بررسی و در صورت لزوم اصلاح و دوباره وارد کند. هیچ‌چیز بدون ردپا ناپدید نمی‌شود."),
);

// 7. استانداردسازی و تبدیل (Q3) ----------------------------------------------
children.push(
  h1("۷. استانداردسازی و تبدیل داده (Q3)"),
  p("شش تابع قابل‌استفاده‌مجدد فقط یک‌بار در src/transform.py نوشته و به‌طور یکسان روی همه فایل‌ها اعمال می‌شوند تا هر اصلاح یا بهبود فقط در یک نقطه لازم باشد:"),
  bullet("standardize_column_names — کوچک‌کردن حروف، حذف فاصله‌های اضافه، تبدیل فاصله‌های داخلی به زیرخط، حذف نویسه‌های عجیب"),
  bullet("normalize_ids — بزرگ‌کردن حروف، حذف فاصله، یکسان‌سازی جداکننده‌ها به خط تیره (به این ترتیب \"wh-01\"، \" WH-01 \" و \"WH_05\" همگی به یک شکل استاندارد واحد می‌رسند)"),
  bullet("parse_dates — استفاده از pd.to_datetime(..., errors='coerce') به‌طور یکسان صرف‌نظر از ترکیب فرمت منبع"),
  bullet("to_numeric_safe — استفاده از pd.to_numeric(..., errors='coerce') برای هر ستون شبه‌مقداری"),
  bullet("clean_text — کوتاه‌کردن و کوچک‌کردن فیلدهای متنی آزاد (وضعیت سفارش)، همراه با یک نگاشت کوچک غلط تایپی (\"shiped\" → \"shipped\") پیش از اعتبارسنجی در برابر مجموعه وضعیت‌های استاندارد"),
  bullet("drop_exact_duplicates — حذف ردیف‌های کاملاً یکسان، با ثبت تعداد برای هر فایل"),
  p("اعمال همان شش تابع در همه‌جا و به همان ترتیب، چیزی است که سه فایل CSV با فرمت‌بندی ناهماهنگ را به جداولی تبدیل می‌کند که می‌توان با اطمینان آن‌ها را ادغام کرد — جایگزین آن (نوشتن اسکریپت‌های پاک‌سازی اختصاصی برای هر فایل) نه مقیاس‌پذیر است و نه به‌راحتی قابل ممیزی."),
);

// 8. یکپارچه‌سازی داده (Q4) ----------------------------------------------------
children.push(
  h1("۸. یکپارچه‌سازی داده (Q4)"),
  p("دانه داده (grain) پیش از نوشتن هر ادغام مشخص شد: یک ردیف به ازای هر (sku, warehouse_id) برای نمای آماده کسب‌وکار، و یک ردیف به ازای هر تراکنش/سفارش برای جداول واقعیت. همه ادغام‌ها از نوع how='left' با indicator=True هستند؛ تعداد ردیف‌ها پیش و پس از هر ادغام ثبت می‌شود و ردیف‌های نامنطبق به‌جای حذف بی‌صدا، جداگانه ثبت می‌شوند."),
  dataTable(
    [2400, 1600, 1500, 1500, 2600],
    ["تفسیر", "نامنطبق", "ردیف پس از ادغام", "ردیف پیش از ادغام", "ادغام"],
    [
      ["هر ترکیب کالا/انبار یک عکس لحظه‌ای موجودی جاری دارد", fa(S.unmatched_counts.inventory), fa(360), fa(360), "تحلیلی ← موجودی"],
      ["بدون فعالیت فروش در ۳۰ روز گذشته — بی‌ضرر، نه یک خطا", fa(S.unmatched_counts.sales), fa(360), fa(360), "تحلیلی ← فروش"],
      ["بدون سفارش باز در ۳۰ روز گذشته — بی‌ضرر، نه یک خطا", fa(S.unmatched_counts.orders), fa(360), fa(360), "تحلیلی ← سفارش"],
      ["صفر ناهنجاری، چون قانون R2 پیش از این مرحله شناسه‌های انباری نامعتبر را قرنطینه کرده است", fa(S.unmatched_counts.warehouses), fa(360), fa(360), "تحلیلی ← انبارها"],
    ],
  ),
  caption("جدول ۳. حسابرسی ادغام برای نمای تحلیلی آماده کسب‌وکار."),
  p(`ثابت ماندن تعداد ردیف روی ${fa(360)} پیش و پس از هر ادغام، نبود fan-out (بزرگ‌شدن ناخواسته تعداد ردیف در اثر ادغام یک‌به‌چند) را تأیید می‌کند — بررسی‌ای که خط لوله به‌صورت خودکار انجام می‌دهد و در صورت شکست، هشدار صادر می‌کند.`),
);

// 9. نمای تحلیلی آماده کسب‌وکار (Q5) ------------------------------------------
children.push(
  h1("۹. نمای تحلیلی آماده کسب‌وکار (Q5)"),
  p(`جدول analytic_sku_warehouse یک ردیف به ازای هر (sku, warehouse_id) دارد — در اجرای حاضر ${fa(S.analytic_rows)} ردیف — با ستون‌های زیر:`),
  bullet("on_hand_qty — آخرین عکس لحظه‌ای موجودی برای آن کالا/انبار"),
  bullet("recent_sales_qty، last_sale_date — حجم فروش ۳۰ روز گذشته و آخرین فروش"),
  bullet("recent_orders_qty، last_order_date — حجم سفارش باز ۳۰ روز گذشته (به‌جز سفارش‌های لغوشده) و آخرین سفارش"),
  bullet("warehouse_name، city، region — پیوندشده از فایل مرجع انبارها"),
  bullet("چهار ستون پرچم عملیاتی — به بخش ۱۰ مراجعه کنید"),
  p("این همان جدولی است که یک مدیر دسته‌بندی یا تحلیل‌گر عملیات، روزانه واقعاً از آن پرس‌وجو می‌کند، به‌جای اینکه هر بار سه جدول واقعیت خام را دستی ادغام کند."),
);

// 10. پرچم‌های عملیاتی (Q6) -----------------------------------------------------
children.push(
  h1("۱۰. پرچم‌های عملیاتی (Q6)"),
  p("چهار پرچم ساده و بدون بهینه‌سازی مستقیماً روی نمای آماده کسب‌وکار محاسبه شدند، با اولویت عمدی شفافیت بر پیچیدگی در این نخستین گذر:"),
  dataTable(
    [1750, 1300, 3990, 2600],
    ["درصد از ۳۶۰", "تعداد ردیف", "تعریف", "پرچم"],
    [
      [faPct(S.flag_counts.flag_stockout_risk, S.analytic_rows), fa(S.flag_counts.flag_stockout_risk), "موجودی فعلی ≤ ۰ درحالی‌که تقاضای فروش اخیر وجود داشته", "ریسک اتمام موجودی (F1)"],
      [faPct(S.flag_counts.flag_excess_inventory, S.analytic_rows), fa(S.flag_counts.flag_excess_inventory), "موجودی فعلی بیش از ۴ برابر مقدار فروش اخیر است", "موجودی مازاد (F2)"],
      [faPct(S.flag_counts.flag_order_backlog, S.analytic_rows), fa(S.flag_counts.flag_order_backlog), "مقدار سفارش باز از موجودی فعلی بیشتر است", "تأخیر در تکمیل سفارش (F3)"],
      [faPct(S.flag_counts.flag_dead_stock, S.analytic_rows), fa(S.flag_counts.flag_dead_stock), "موجودی وجود دارد اما در ۳۰ روز گذشته هیچ فروشی ثبت نشده", "موجودی راکد (F4)"],
    ],
  ),
  caption("جدول ۴. پرچم‌های عملیاتی محاسبه‌شده در src/transform.add_operational_flags()."),
  image("fig2_flags_by_type.png", 480),
  caption("شکل ۱. تعداد ردیف‌های کالا/انبار به تفکیک نوع پرچم."),
  p(`موجودی مازاد با ${faPct(S.flag_counts.flag_excess_inventory, S.analytic_rows)} از ترکیب‌های کالا/انبار، بزرگ‌ترین پرچم منفرد است — سیگنالی معقول برای این نخستین گذر با آستانه ۴ برابر، اما باید پیش از استفاده در تصمیم‌گیری، در برابر اهداف واقعی سطح خدمت بازبینی شود (به بخش ۱۳، محدودیت‌ها مراجعه کنید). تنها یک ترکیب ریسک آشکار اتمام موجودی نشان می‌دهد و ${faPct(S.flag_counts.flag_dead_stock, S.analytic_rows)} در ۳۰ روز گذشته هیچ حرکت فروشی نداشته‌اند.`),
  image("fig1_inventory_by_warehouse.png", 480),
  caption("شکل ۲. مجموع موجودی فعلی به تفکیک انبار."),
  image("fig3_top_skus_on_hand.png", 480),
  caption("شکل ۳. ده کالای برتر بر اساس مجموع موجودی فعلی."),
);

// 11. بارگذاری و بازتولیدپذیری (Q7) ----------------------------------------------
children.push(
  h1("۱۱. بارگذاری و بازتولیدپذیری (Q7)"),
  p("پنج جدول با if_exists='replace' در database/inventory.db نوشته شدند: dim_warehouses، fact_sales، fact_orders، fact_inventory و analytic_sku_warehouse. پس از بارگذاری، خط لوله به‌جای فرض موفقیت‌آمیز بودن نوشتن، بررسی‌های کیفیت خود را اجرا می‌کند:"),
  dataTable(
    [1700, 2100, 2100, 3300],
    ["تطابق", "ردیف در SQLite", "ردیف در دیتافریم", "جدول"],
    Object.entries(S.load_checks).filter(([k]) => typeof S.load_checks[k] === "object" && "rows_in_dataframe" in S.load_checks[k])
      .map(([k, v]) => [v.match ? "بله" : "خیر", fa(v.rows_in_sqlite), fa(v.rows_in_dataframe), k]),
  ),
  caption("جدول ۵. راستی‌آزمایی تعداد ردیف پس از بارگذاری (دیتافریم در برابر SELECT COUNT(*))."),
  p(`بررسی دوم، یکپارچگی ارجاعی را سراسر مسیر تأیید می‌کند: ${fa(S.load_checks.fact_sales_orphan_warehouse_ids)} ردیف در fact_sales به شناسه انباری اشاره می‌کند که در dim_warehouses وجود ندارد (از مجموع ${fa(S.load_checks.total_fact_rows)} ردیف در سه جدول واقعیت).`),
  p("خط لوله تنها از مسیرهای نسبی (pathlib) استفاده می‌کند، با یک دستور واحد (python -m src.main) سرتاسر اجرا می‌شود و ایدمپوتنت است — اجرای دوباره آن از یک data/processed/ و database/ تمیز، همان تعداد ردیف و همان تعداد پرچم را تولید می‌کند، چون تولیدکننده منبع دارای بذر تصادفی ثابت است و هر تبدیل قطعی (deterministic) است."),
);

// 12. ثبت رخداد و مسیر ممیزی (Q8) --------------------------------------------
children.push(
  h1("۱۲. ثبت رخداد و مسیر ممیزی (Q8)"),
  p("logs/pipeline.log در هر اجرا بازنویسی می‌شود (نه افزوده) و با یک برچسب زمانی روی هر خط ثبت می‌کند: زمان شروع و پایان خط لوله؛ تعداد ردیف خوانده‌شده از هر فایل خام؛ هر آماره پروفایل‌بندی از بخش ۵؛ هر نقض قانون اعتبارسنجی و اقدام قرنطینه از بخش ۶؛ تعداد ردیف‌های حذف‌شده در پاک‌سازی و حذف تکراری کامل؛ تعداد پیش/پس/نامنطبق هر ادغام از بخش ۸؛ تعداد هر پرچم عملیاتی از بخش ۱۰؛ و نتایج راستی‌آزمایی پس از بارگذاری از بخش ۱۱. هر استثنای مدیریت‌نشده به‌جای شکست بی‌صدا، به همراه ردپای کامل آن ثبت می‌شود."),
  p("همین موضوع، فایل لاگ را به یک پاسخ کامل و زمانی به این پرسش تبدیل می‌کند که «خط لوله در این اجرا واقعاً چه کاری انجام داد» — که هم برای اشکال‌زدایی و هم برای اثبات به یک بازبین که هیچ مرحله‌ای نادیده گرفته نشده، مفید است."),
);

// 13. محدودیت‌ها ----------------------------------------------------------------
children.push(
  h1("۱۳. محدودیت‌ها"),
  bullet("داده زیربنایی مصنوعی است، نه یک خروجی واقعی از سامانه تولید؛ مقادیر مطلق (واحد، درآمد) نمایشی هستند، نه ارقام واقعی فروش."),
  bullet("هیچ سامانه منبعی نشانگر «این مقدار منفی یک مرجوعی مستند است» ندارد؛ بنابراین قانون R5 هر مقدار منفی را خطای ورود داده در نظر می‌گیرد. یک سامانه منبع واقعی باید پرچم مرجوعی/بازپرداخت داشته باشد که باید به‌جای حذف کلی، رعایت شود."),
  bullet("آستانه‌های موجودی مازاد (۴ برابر) و تأخیر در تکمیل سفارش (بیش از موجودی فعلی) در بخش ۱۰، نقطه شروع معقولی برای این نخستین گذر هستند، نه آستانه‌هایی تنظیم‌شده در برابر توافق‌نامه‌های سطح خدمت واقعی — باید پیش از استفاده در تصمیمات خرید یا تخصیص، با کسب‌وکار بازبینی شوند."),
  bullet("بازه زمانی اخیر به‌صورت ثابت ۳۰ روز از میان ۷۰ روز تاریخچه تعریف شده؛ هر دو در src/main.py قابل تنظیم‌اند و الزام کسب‌وکاری سخت نیستند."),
  bullet("ردیف‌های قرنطینه‌شده (R2) برای بررسی روی دیسک نوشته می‌شوند اما به‌صورت خودکار اصلاح یا دوباره وارد نمی‌شوند — این مرحله عمداً یک تصمیم انسانی است."),
);

// 14. نتیجه‌گیری و پیشنهادها ------------------------------------------------------
children.push(
  h1("۱۴. نتیجه‌گیری و پیشنهادها"),
  p("خط لوله هر هشت هدف بیان‌شده در بخش ۲ را برآورده می‌کند: کیفیت داده خام به‌طور کامل پروفایل‌بندی و مستند شده، قوانین کسب‌وکاری صریح و همراه با مسیر ممیزی اجرا شده‌اند، چهار منبع بدون از دست رفتن بی‌صدای داده استاندارد و ادغام شده‌اند، یک نمای واحد آماده کسب‌وکار به پرسش‌های عملیاتی واقعی پاسخ می‌دهد، چهار وضعیت ریسک عملیاتی به‌صورت شفاف پرچم‌گذاری شده‌اند، بارگذاری SQLite به‌جای فرض‌شدن راستی‌آزمایی شده، و هر اجرا به‌طور کامل ثبت و بازتولیدپذیر است."),
  p("گام‌های پیشنهادی بعدی: اعتبارسنجی آستانه‌های موجودی مازاد و تأخیر در تکمیل سفارش در برابر اهداف واقعی سطح خدمت کسب‌وکار؛ افزودن نشانگر مستند مرجوعی/بازپرداخت به فایل فروش تا مرجوعی‌های واقعی دیگر از خطاهای ورود داده قابل‌تشخیص نباشند؛ و بازبینی ردیف‌های قرنطینه‌شده در data/processed/ با مسئول داده مرجع انبارها، چرا که یک شناسه انباری آویزان تکرارشونده معمولاً نشانه یک شکاف همگام‌سازی میان سامانه‌های منبع است، نه یک غلط تایپی یک‌باره."),
);

// ---------------------------------------------------------------------------
const doc = new Document({
  creator: "امیررضا بابااحمدی",
  title: "خط لوله یکپارچه‌سازی داده‌های موجودی FMCG — گزارش پروژه",
  description: "گزارش پروژه فارسی خط لوله ETL موجودی FMCG (پایتون، پانداس، اس‌کیوالایت).",
  styles: {
    default: {
      document: { run: { font: FONT, size: 22, rightToLeft: true } },
    },
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1300, left: 1300, right: 1300 } },
      bidi: true,
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        bidirectional: true,
        alignment: AlignmentType.LEFT,
        border: { bottom: { color: "CCCCCC", space: 4, style: BorderStyle.SINGLE, size: 4 } },
        children: [
          new TextRun({ text: "خط لوله یکپارچه‌سازی داده‌های موجودی ", size: 16, color: GREY, font: FONT, rightToLeft: true }),
          new TextRun({ text: "FMCG", size: 16, color: GREY, font: LATIN_FONT }),
        ],
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        bidirectional: true,
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "صفحه ", size: 16, color: GREY, font: FONT, rightToLeft: true }),
          new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY, font: FONT }),
          new TextRun({ text: " از ", size: 16, color: GREY, font: FONT, rightToLeft: true }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: GREY, font: FONT }),
        ],
      })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "reports", "FMCG_ETL_Project_Report_FA.docx");
  fs.writeFileSync(out, buf);
  console.log("Wrote", out);
});
