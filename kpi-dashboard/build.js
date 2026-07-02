#!/usr/bin/env node
/**
 * Build dashboard KPI DVPT từ các file CSV trong thư mục data/.
 *
 * Cách dùng:  node build.js
 * Đầu vào :  data/fact.csv · data/dim_date.csv · data/dim_org.csv
 * Đầu ra  :  dist/index.html (dashboard hoàn chỉnh, tự chứa, mở bằng trình duyệt)
 *
 * CSV yêu cầu: UTF-8 (có/không BOM đều được), dấu phân cách `,` hoặc `;`
 * (tự phát hiện), số thập phân dùng dấu chấm (vd: 245.603).
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(ROOT, 'data');
const OUT_DIR = path.join(ROOT, 'dist');
const TEMPLATE = path.join(ROOT, 'template.html');
const PLACEHOLDER = '/*__EMBEDDED_DATA__*/';

function detectDelimiter(headerLine) {
  const candidates = [',', ';', '\t'];
  let best = ',', bestCount = -1;
  for (const d of candidates) {
    const count = headerLine.split(d).length - 1;
    if (count > bestCount) { best = d; bestCount = count; }
  }
  return best;
}

// Parser CSV tối giản nhưng đúng chuẩn: hỗ trợ ô có ngoặc kép, dấu phân cách
// nằm trong ngoặc, ngoặc kép lặp ("") và xuống dòng CRLF/LF.
function parseCsv(text) {
  text = text.replace(/^﻿/, '');
  const firstLine = text.slice(0, text.indexOf('\n') === -1 ? text.length : text.indexOf('\n'));
  const delim = detectDelimiter(firstLine);

  const rows = [];
  let row = [], field = '', inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else inQuotes = false;
      } else field += c;
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === delim) {
      row.push(field); field = '';
    } else if (c === '\n') {
      row.push(field.replace(/\r$/, '')); field = '';
      rows.push(row); row = [];
    } else field += c;
  }
  if (field !== '' || row.length) { row.push(field.replace(/\r$/, '')); rows.push(row); }

  const header = rows.shift().map((h) => h.trim());
  return rows
    .filter((r) => r.some((v) => v.trim() !== ''))
    .map((r) => {
      const obj = {};
      header.forEach((col, i) => { obj[col] = convertValue(r[i] ?? ''); });
      return obj;
    });
}

// Ô trống → null · dạng số → Number · còn lại giữ nguyên chuỗi
function convertValue(raw) {
  const s = raw.trim();
  if (s === '') return null;
  if (/^-?\d+(\.\d+)?$/.test(s)) return Number(s);
  return s;
}

function loadCsv(name, requiredCols) {
  const file = path.join(DATA_DIR, name);
  if (!fs.existsSync(file)) {
    console.error(`✗ Thiếu file ${path.relative(ROOT, file)}`);
    process.exit(1);
  }
  const rows = parseCsv(fs.readFileSync(file, 'utf8'));
  if (!rows.length) {
    console.error(`✗ ${name} không có dòng dữ liệu nào`);
    process.exit(1);
  }
  const missing = requiredCols.filter((c) => !(c in rows[0]));
  if (missing.length) {
    console.error(`✗ ${name} thiếu cột bắt buộc: ${missing.join(', ')}`);
    process.exit(1);
  }
  return rows;
}

const fact = loadCsv('fact.csv', ['o', 'y', 'm']);
const dim_date = loadCsv('dim_date.csv', ['y', 'm']);
const dim_org = loadCsv('dim_org.csv', ['code', 'name', 'brand', 'color']);

// Cảnh báo sớm các lỗi dữ liệu hay gặp thay vì để dashboard trống không rõ lý do
const orgCodes = new Set(dim_org.map((o) => o.code));
const unknownOrgs = [...new Set(fact.map((r) => r.o).filter((o) => !orgCodes.has(o)))];
if (unknownOrgs.length) {
  console.warn(`⚠ fact.csv có mã đại lý không tồn tại trong dim_org.csv: ${unknownOrgs.join(', ')}`);
}

const now = new Date();
const pad = (n) => String(n).padStart(2, '0');
const generated = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;

// Ngày "dữ liệu đến hết" — dashboard dùng để nhận biết tháng chưa trọn kỳ
// (tính "cần đạt/ngày còn lại"). Mặc định = ngày build; ghi đè khi build
// dữ liệu cũ:  node build.js --asof 2026-06-23
let dataMaxDate = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
const asofIdx = process.argv.indexOf('--asof');
if (asofIdx !== -1) {
  const v = process.argv[asofIdx + 1];
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v ?? '')) {
    console.error('✗ --asof cần định dạng YYYY-MM-DD, ví dụ: --asof 2026-06-23');
    process.exit(1);
  }
  dataMaxDate = v;
}

const template = fs.readFileSync(TEMPLATE, 'utf8');
if (!template.includes(PLACEHOLDER)) {
  console.error(`✗ template.html không chứa placeholder ${PLACEHOLDER}`);
  process.exit(1);
}
const payload = JSON.stringify({ fact, dim_date, dim_org, generated });

// Nhúng Chart.js vào file build → dashboard tự chứa, mở offline vẫn chạy
function vendorScript(file) {
  const p = path.join(ROOT, 'vendor', file);
  if (!fs.existsSync(p)) {
    console.error(`✗ Thiếu vendor/${file}`);
    process.exit(1);
  }
  // '</script' trong nội dung JS sẽ phá thẻ <script> bao ngoài
  return fs.readFileSync(p, 'utf8').replaceAll('</script', '<\\/script');
}

const html = template
  .replace(PLACEHOLDER, () => payload)
  .replaceAll('__DATA_MAX_DATE__', dataMaxDate)
  .replace('/*__VENDOR_CHARTJS__*/', () => vendorScript('chart.umd.js'))
  .replace('/*__VENDOR_DATALABELS__*/', () => vendorScript('chartjs-plugin-datalabels.min.js'));

fs.mkdirSync(OUT_DIR, { recursive: true });
const outFile = path.join(OUT_DIR, 'index.html');
fs.writeFileSync(outFile, html);

console.log(`✓ Đã build ${path.relative(ROOT, outFile)} (${(html.length / 1024).toFixed(0)} KB)`);
console.log(`  fact: ${fact.length} dòng · dim_date: ${dim_date.length} · dim_org: ${dim_org.length} · dữ liệu đến: ${dataMaxDate}`);
